# Creación de producto desde cero

## Ejercicio - Hipótesis y validación

**Proyecto: Regalo de 15 años (libros como regalo)**

| Paso | Elemento | Desarrollo aplicado al proyecto |
| --- | --- | --- |
| 1 | **Producto digital** | Plataforma web donde familiares y amigos, desde distintos lugares, pueden elegir y regalar **libros** a la cumpleañera a partir de tarjetas con propuestas. El objetivo es que la cumpleañera reciba **al menos 15 libros**. |
| 2 | **Hipótesis** | *Si la plataforma ofrece una interfaz sencilla y guiada para elegir libros, entonces los familiares y amigos que están lejos podrán elegir más rápido y con mayor confianza un regalo que realmente quiere la cumpleañera.* |
| 3 | **Métricas de éxito** | **Métrica 1:** Tiempo promedio que tarda un invitado en elegir un libro desde que entra a la plataforma. **Métrica 2:** Porcentaje de invitados que completan la elección del libro (libros regalados / invitados). |
| 4 | **Ciclo corto de validación** | **Paso 1:** Diseñar una versión simple de la interfaz con tarjetas claras, pocas opciones y textos guía ("Este libro fue elegido por la cumpleañera"). **Paso 2:** Compartir el link con un grupo reducido de familiares y amigos reales. **Paso 3:** Medir durante una semana cuánto tardan en elegir y cuántos completan el regalo. **Paso 4:** Comparar los resultados con una versión más cargada o menos guiada. |
| 5 | **Aprendizaje esperado** | Entender si una interfaz sencilla reduce la duda y el esfuerzo al elegir un regalo a distancia. Detectar si la principal fricción está en la cantidad de opciones, en la claridad de la información o en el flujo de la interfaz. |
| 6 | **Reflexión sobre el impacto en el equipo** | El equipo prioriza simplificar la experiencia antes que agregar más funcionalidades. Las decisiones de diseño y desarrollo se basan en aprendizaje real, no en supuestos. Se construyen funcionalidades que ayudan directamente a cumplir el objetivo: llegar a los 15 libros. |

---

## Ejercicio - Análisis del proyecto y roles

**Proyecto: App web para reservar espacios comunes en un edificio (SUM, parrilla y sala de reuniones).**

El **objetivo** del proyecto fue reducir conflictos entre vecinos y centralizar la información de reservas en un solo lugar.

---

### Roles identificados y responsabilidades

**Product Manager (PM)**

Se encargó de definir el problema principal, priorizar qué funcionalidades entraban al MVP y validar las hipótesis con usuarios reales. También coordinó el trabajo entre roles y ajustó el alcance según el feedback.

**UX/UI Designer**

Diseñó los flujos principales de la app (login, vista de calendario y reserva), cuidando que fueran simples y claros. Testeó los primeros prototipos con usuarios y propuso mejoras de usabilidad.

**Desarrollador/a Full Stack**

Implementó el frontend y el backend básico del MVP. Integró autenticación, base de datos y lógica de reservas. También se encargó del deploy para que la app estuviera disponible online.

---

### Checklist de entregables mínimos por rol

| ROL | CARACTERÍSTICAS DEL ROL | QUÉ DEBE ENTREGAR |
| --- | --- | --- |
| **PROJECT MANAGER** | Es quien cuida el *para qué* y el *qué*. Define el problema a resolver, prioriza qué construir primero y valida que el producto tenga sentido para usuarios reales. Su obsesión: que el producto genere valor y no features sin fundamentación. | • Problema definido claramente • Hipótesis central del MVP • Lista priorizada de funcionalidades • Métricas básicas de validación • Feedback inicial de usuarios |
| **UX/UI** | Es quien se encarga del *cómo se siente usar el producto*. Diseña la experiencia (UX) y la interfaz visual (UI) para que el usuario entienda qué hacer, no se frustre y quiera volver. Traduce problemas en flujos claros, pantallas simples y decisiones visuales que reduzcan fricción. | • User flow principal • Wireframes o pantallas clave del MVP • Textos básicos de la interfaz • Ajustes de diseño según feedback temprano |
| **DESARROLLO** | Es quien convierte las ideas en algo que funciona de verdad. Implementa la lógica, conecta servicios, maneja datos y se asegura de que la app sea estable, performante y escalable. Hoy, con IA, su foco no es tipear código sin parar, sino pensar buenas soluciones técnicas y elegir bien cómo construir. | • App funcional (login + reservas) • Base de datos conectada • Validaciones básicas de uso • Deploy en entorno productivo • Corrección de bugs críticos |

### Reflexión sobre la colaboración entre roles

La colaboración fue bastante fluida y con **ciclos cortos de trabajo**. No se esperaba a tener todo "perfecto" para avanzar: se construía algo, se probaba rápido y se ajustaba.

Hubo comunicación continua, sobre todo entre PM y UX para validar decisiones antes de implementarlas.

Lo que se podría mejorar es **involucrar antes a todos los roles en las decisiones**, especialmente al inicio. Algunas correcciones podrían haberse evitado si diseño y desarrollo participaban más desde la definición de la hipótesis.

En general, el enfoque fue muy alineado a Vibe Coding: menos documentación eterna y más producto real funcionando lo antes posible. En Vibe Coding estos roles no desaparecen, pero se mezclan más: todos piensan producto, solo que desde lentes distintos.

---

## Práctica: Diseñar un v0 asistido por ChatGPT

### Contexto

En el desarrollo de productos digitales, ChatGPT puede actuar como un asistente de producto que ayuda a generar ideas, prompts, textos y flujos para prototipar rápidamente un v0, un prototipo funcional mínimo que permite validar hipótesis centrales sin necesidad de un producto final listo para producción.

En este ejercicio, simularás la validación de un v0 generado con ayuda de ChatGPT. Recibirás una serie de prompts y flujos que representan la estructura del v0. Tu tarea será procesar esta información para validar que el v0 cumple con los criterios mínimos: que cada flujo tenga un nombre único, que los textos asociados no estén vacíos y que la estructura sea coherente para avanzar a la validación.

### Descripción del problema

Se te proporciona una lista de flujos generados por ChatGPT para un v0. Cada flujo tiene un identificador y un texto descriptivo. Debes verificar que:

- No haya flujos con identificadores duplicados.
- Ningún texto descriptivo esté vacío.
- La cantidad total de flujos sea al menos 1 (un v0 debe tener al menos un flujo funcional).

Si la validación es exitosa, debes imprimir "VALID" y luego listar los flujos ordenados por su identificador. Si falla alguna validación, imprimir "INVALID".

### Formato de entrada

- La primera línea contiene un entero N, el número de flujos.
- Las siguientes N líneas contienen dos elementos separados por un espacio:
    - Un identificador de flujo (cadena sin espacios).
    - Un texto descriptivo (cadena que puede contener espacios).

### Formato de salida

- Si la validación es exitosa:
    - Imprimir "VALID" en una línea.
    - Luego imprimir N líneas con los flujos ordenados por identificador, cada línea con el formato: `<identificador> <texto>`
- Si la validación falla:
    - Imprimir "INVALID"

### Ejemplo

**Entrada:**
```
3
login Pantalla de inicio de sesión
signup Formulario de registro
dashboard Vista principal del usuario
```

**Salida:**
```
VALID
dashboard Vista principal del usuario
login Pantalla de inicio de sesión
signup Formulario de registro
```

### Notas

- El identificador no contiene espacios ni comillas.
- El texto descriptivo puede contener espacios.
- Debes manejar correctamente la lectura y validación de los textos.

---

## Interpretación del ejercicio

### ¿De qué se trata?

En este ejercicio **no vas a crear nada nuevo**. Vas a **revisar información que ya existe** y decidir si está bien o mal.

Imaginá que una IA (como ChatGPT) ya armó un primer borrador de un producto digital y te pasó una lista de "flujos" (pantallas o pasos del producto). Tu trabajo es **revisar esa lista** y decir si sirve para probar una idea básica de producto.

> Este ejercicio no evalúa creatividad. Evalúa si sabés **leer información y aplicar reglas simples** para validar un producto mínimo.

### Qué NO es este ejercicio

❌ No es:
- escribir un prompt
- hablar con ChatGPT
- pedirle algo a la IA
- inventar flujos
- decidir tecnologías

Todo eso **ya pasó antes** en la historia del ejercicio.

### Qué SÍ es este ejercicio

👉 Es un ejercicio de **lectura + verificación lógica**.

> "Imaginá que ChatGPT ya generó un v0 y ahora vos tenés que revisar si está bien armado."

### Qué hace el alumno concretamente

1. Lee el input (los flujos).
2. Revisa 3 reglas:
    - ¿hay al menos uno?
    - ¿no hay nombres repetidos?
    - ¿ningún texto está vacío?
3. Llega a una conclusión: VALID o INVALID
4. Escribe la salida correcta.

---

## Solución posible

### INPUT DE EJEMPLO

```
3
login Pantalla de inicio de sesión
dashboard Vista principal del usuario
logout Cerrar sesión
```

### PASO 1: ¿Cuántos flujos hay?

```
3
```

> "Hay 3 flujos" → ✔️ Regla cumplida (hay al menos 1)

### PASO 2: Mirar cada flujo uno por uno

- **Flujo 1:** `login` → "Pantalla de inicio de sesión" ✔️
- **Flujo 2:** `dashboard` → "Vista principal del usuario" ✔️
- **Flujo 3:** `logout` → "Cerrar sesión" ✔️

### PASO 3: Verificar reglas

- **Regla 1 — ¿Nombres repetidos?** → login, dashboard, logout → Todos distintos ✔️
- **Regla 2 — ¿Algún texto vacío?** → Todos tienen descripción ✔️
- **Regla 3 — ¿Hay al menos un flujo?** → Hay 3 ✔️

### CONCLUSIÓN: VALID

### OUTPUT FINAL

```
VALID
dashboard Vista principal del usuario
login Pantalla de inicio de sesión
logout Cerrar sesión
```

---

## Por qué este ejercicio está en una unidad de IA / Vibe Coding

Porque enseña esto:
- la IA genera rápido
- **los humanos validan**
- no todo lo generado sirve
- hay que poner reglas claras

Eso es mentalidad de producto.

---

## ¿Qué es Supabase y para qué sirve?

Supabase es un **backend listo para usar**.

Backend significa todo lo que no se ve, pero que hace que una app funcione de verdad:

- Base de datos (guardar información)
- Autenticación (login, usuarios)
- Seguridad (quién puede ver o modificar datos)
- API para que el frontend se comunique con esos datos

Antes, para hacer esto necesitabas:
- Un servidor
- Una base de datos
- Configurar seguridad
- Escribir muchas líneas de código

### Links relacionados
- [SUPABASE PRIMEROS PASOS](https://www.notion.so/SUPABASE-PRIMEROS-PASOS-30587b9421a7816095d2c125fecf0429)
- [FRAMEWORK RICE](https://www.notion.so/FRAMEWORK-RICE-30587b9421a781b6ae7cca0749fb3428)
