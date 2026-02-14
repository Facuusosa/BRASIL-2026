"""
Interacción directa con las mutations GraphQL de Flybondi.
Simula el flujo de checkout para aplicar descuentos.
"""
import json, os, time
from curl_cffi import requests as cffi_requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except: pass

API_URL = "https://flybondi.com/graphql"
API_KEY = os.getenv("FLYBONDI_API_KEY", "b64ead64fb26d64668838ac2ef8c0c3222c3d285cf5a2fd1ce49281c140bcdaa")
SESSION_COOKIE = os.getenv("FLYBONDI_SESSION", "SFO-bfac89a4-129e-4741-a22e-b1875eaf52f8")

HEADERS = {
    "accept": "application/json",
    "authorization": f"Key {API_KEY}",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "referer": "https://flybondi.com/ar/search/results",
    "user-agent": "Mozilla/5.0 Chrome/144.0.0.0 Mobile Safari/537.36",
    "x-fo-flow": "ibe",
    "x-fo-market-origin": "ar",
    "x-fo-ui-version": "2.209.0",
}

def gql(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    cookies = {"SFO": SESSION_COOKIE}
    r = cffi_requests.post(API_URL, json=payload, headers=HEADERS, cookies=cookies, impersonate="chrome120", timeout=20)
    return r.json()

out = open("mutation_results.txt", "w", encoding="utf-8")
def p(s=""):
    print(s)
    out.write(s + "\n")
    out.flush()

# Step 1: Search flights first to establish session
p("=" * 60)
p("STEP 1: Searching flights to establish session")
p("=" * 60)

SEARCH_Q = """
query FlightSearchContainerQuery($input: FlightsQueryInput!) {
  viewer {
    flights(input: $input) {
      searchUrl
      edges {
        node {
          id
          lfId
          sfId
          flightNo
          origin
          destination
          departureDate
          direction
          fares {
            fareRef
            type
            class
            availability
            passengerType
            prices { afterTax beforeTax promotionAmount }
          }
        }
      }
    }
    id
  }
}
"""

search_vars = {
    "input": {
        "origin": "BUE", "destination": "FLN",
        "departureDate": "2026-03-08", "returnDate": "2026-03-17",
        "currency": "ARS",
        "pax": {"adults": 2, "children": 0, "infants": 0},
        "promoCode": None,
    }
}

result = gql(SEARCH_Q, search_vars)
if "data" in result:
    edges = result["data"]["viewer"]["flights"]["edges"]
    viewer_id = result["data"]["viewer"]["id"]
    p(f"  Flights found: {len(edges)}")
    p(f"  Viewer ID: {viewer_id}")
    
    # Get cheapest outbound
    outbound_flights = [e for e in edges if e["node"]["direction"] == "OUTBOUND"]
    inbound_flights = [e for e in edges if e["node"]["direction"] == "INBOUND"]
    
    if outbound_flights:
        cheapest_out = min(outbound_flights, key=lambda e: e["node"]["fares"][0]["prices"]["afterTax"])
        out_node = cheapest_out["node"]
        p(f"  Cheapest outbound: FO{out_node['flightNo']} {out_node['origin']}->{out_node['destination']} ${out_node['fares'][0]['prices']['afterTax']:,.0f}/pp")
        p(f"    id: {out_node['id']}")
        p(f"    lfId: {out_node.get('lfId')}")
        p(f"    sfId: {out_node.get('sfId')}")
        p(f"    fareRef: {out_node['fares'][0].get('fareRef')}")
    
    if inbound_flights:
        cheapest_in = min(inbound_flights, key=lambda e: e["node"]["fares"][0]["prices"]["afterTax"])
        in_node = cheapest_in["node"]
        p(f"  Cheapest inbound: FO{in_node['flightNo']} {in_node['origin']}->{in_node['destination']} ${in_node['fares'][0]['prices']['afterTax']:,.0f}/pp")
        p(f"    id: {in_node['id']}")
        p(f"    lfId: {in_node.get('lfId')}")
        p(f"    sfId: {in_node.get('sfId')}")
        p(f"    fareRef: {in_node['fares'][0].get('fareRef')}")
else:
    p(f"  ERROR: {json.dumps(result.get('errors', result))[:300]}")
    outbound_flights = []
    inbound_flights = []

# Step 2: Try UpdateSession mutation to select flights
p()
p("=" * 60)
p("STEP 2: Try to select flights via session")
p("=" * 60)

# The UpdateSessionMutation likely needs flight IDs
UPDATE_SESSION = """
mutation UpdateSessionMutation($input: UpdateSessionInput!) {
  updateSession(input: $input) {
    clientMutationId
    session {
      id
      shoppingVersion
      currency
      flights {
        outbound {
          id
          fares {
            type
            prices { afterTax beforeTax promotionAmount }
          }
        }
        inbound {
          id
          fares {
            type
            prices { afterTax beforeTax promotionAmount }
          }
        }
      }
      discount {
        __typename
        type
        amount
      }
    }
  }
}
"""

if outbound_flights and inbound_flights:
    session_input = {
        "input": {
            "clientMutationId": "1",
            "outbound": out_node["sfId"] or out_node["id"],
            "inbound": in_node["sfId"] or in_node["id"],
            "fareType": "STANDARD",
        }
    }
    
    p(f"  Selecting flights: out={session_input['input']['outbound']}, in={session_input['input']['inbound']}")
    result2 = gql(UPDATE_SESSION, session_input)
    
    if "data" in result2 and result2["data"].get("updateSession"):
        session = result2["data"]["updateSession"].get("session", {})
        p(f"  Session ID: {session.get('id')}")
        p(f"  Shopping version: {session.get('shoppingVersion')}")
        p(f"  Currency: {session.get('currency')}")
        shopping_version = session.get("shoppingVersion")
        
        if session.get("flights"):
            flights = session["flights"]
            if flights.get("outbound"):
                ob_price = flights["outbound"]["fares"][0]["prices"]["afterTax"]
                p(f"  Outbound price: ${ob_price:,.0f}/pp")
            if flights.get("inbound"):
                ib_price = flights["inbound"]["fares"][0]["prices"]["afterTax"]
                p(f"  Inbound price: ${ib_price:,.0f}/pp")
        
        # Step 3: Apply UBA discount
        p()
        p("=" * 60)
        p("STEP 3: Applying UBA discount")
        p("=" * 60)
        
        UBA_MUTATION = """
mutation useAddUBADiscountMutation($input: AddUBADiscountInput!) {
  addUBADiscount(input: $input) {
    clientMutationId
    session {
      id
      shoppingVersion
      flights {
        outbound {
          fares {
            type
            prices { afterTax beforeTax promotionAmount }
          }
          id
        }
        inbound {
          fares {
            type
            prices { afterTax beforeTax promotionAmount }
          }
          id
        }
      }
      discount {
        __typename
        type
        amount
        ... on UBADiscount {
          nationalId
          percentage
        }
      }
      currency
    }
  }
}
"""
        
        uba_input = {
            "input": {
                "clientMutationId": "2",
                "nationalId": "41168646",
                "shoppingVersion": shopping_version,
            }
        }
        
        p(f"  Sending DNI: 41168646")
        result3 = gql(UBA_MUTATION, uba_input)
        
        if "data" in result3 and result3["data"].get("addUBADiscount"):
            uba_session = result3["data"]["addUBADiscount"].get("session", {})
            discount = uba_session.get("discount", {})
            p(f"  DISCOUNT TYPE: {discount.get('type')}")
            p(f"  DISCOUNT AMOUNT: {discount.get('amount')}")
            p(f"  PERCENTAGE: {discount.get('percentage')}")
            p(f"  NATIONAL ID: {discount.get('nationalId')}")
            
            if uba_session.get("flights"):
                flights = uba_session["flights"]
                if flights.get("outbound"):
                    new_price = flights["outbound"]["fares"][0]["prices"]["afterTax"]
                    promo = flights["outbound"]["fares"][0]["prices"].get("promotionAmount", 0)
                    p(f"  NEW Outbound price: ${new_price:,.0f}/pp (promo: ${promo:,.0f})")
                if flights.get("inbound"):
                    new_price = flights["inbound"]["fares"][0]["prices"]["afterTax"]
                    promo = flights["inbound"]["fares"][0]["prices"].get("promotionAmount", 0)
                    p(f"  NEW Inbound price: ${new_price:,.0f}/pp (promo: ${promo:,.0f})")
        else:
            errors = result3.get("errors", [])
            p(f"  UBA RESULT: {json.dumps(result3, indent=2)[:500]}")
    else:
        p(f"  Session error: {json.dumps(result2, indent=2)[:500]}")

p()
p("=" * 60)
p("DONE")
p("=" * 60)
out.close()
