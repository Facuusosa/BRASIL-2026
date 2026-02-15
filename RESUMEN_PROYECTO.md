# ✈️ PROYECTO MONITOR FLYBONDI - MANUAL DE USO

¡Bienvenido a tu centro de inteligencia de vuelos! Aquí tienes todo lo que necesitas saber.

## 1. ¿CÓMO LO ENCIENDO? 🟢
Para activar los robots, abre la terminal en esta carpeta y escribe:

```bash
python smart_monitor.py --daemon
```

**(¡No cierres la ventana negra! Si la cierras, los robots se duermen).**

---

## 2. ¿QUÉ HACE CADA ROBOT? 🤖

*   **💰 Monitor de Precios:** Revisa cuánto sale ir a Florianópolis cada 1 hora.
*   **🕵️ El Espía (Flags):** Te avisa si Flybondi activa funciones secretas (como nuevas promos).
*   **💥 Cazador de Errores:** Busca si se equivocaron y pusieron la clase VIP a precio de regalo.
*   **🧪 El Científico:** Prueba buscar vuelos raros para ver si el sistema falla a nuestro favor.

---

## 3. ¿CÓMO LEO LAS ALERTAS? 📱

Te llegarán a Telegram:

*   **🟡 ALERTA AMARILLA:** Precio bueno (menos de $800.000). ¡Considera comprar!
*   **🟢 ALERTA VERDE:** ¡GANGA! (Menos de $600.000). Compra inmediata.
*   **🔴 ALERTA ROJA:** Carísimo. Ni mires.
*   **🧬 SOURCE CHANGE:** El espía encontró cambios en el código de la web (posibles promos futuras).

---

## 4. TRUCOS ÚTILES 💡

*   **Ver el último reporte:** Haz doble clic en el archivo `VER_ULTIMO_REPORTE.bat` y se abrirá el gráfico en tu navegador.
*   **Modo Silencioso:** El monitor trabaja solo. Si no te manda mensajes, es que no pasó nada interesante.

---

**Estado del Proyecto:** FINALIZADO Y OPERATIVO ✅
**Autor:** Tu Asistente de IA (Antigravity)
**Fecha:** Febrero 2026
