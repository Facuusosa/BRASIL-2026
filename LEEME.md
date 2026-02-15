# ✈️ MONITOR FLYBONDI INTELIGENTE - TU PUESTO DE MANDO

¡Hola Facu! Este es tu sistema de monitoreo automatizado. Aquí tienes todo lo que necesitas saber de forma sencilla.

---

## 🟢 1. CÓMO ACTIVAR EL SISTEMA (LO ÚNICO QUE TIENES QUE EJECUTAR)

Para poner a trabajar a los robots, abre la terminal en esta carpeta y corre este comando:

```bash
python smart_monitor.py --daemon
```

**(⚠️ IMPORTANTE: No cierres la ventana negra de la terminal. Mientras esté abierta, los robots vigilan).**

El sistema revisará precios **cada 1 hora** y buscará ofertas ocultas. Si encuentra algo bueno, te avisará por **Telegram**.

---

## 📊 2. CÓMO VER LOS REPORTES GRÁFICOS

Si quieres ver el gráfico de precios con tus propios ojos:
👉 **Haz doble clic en el archivo `VER_ULTIMO_REPORTE.bat`**

Esto abrirá automáticamente en tu navegador el último informe que generó el monitor.

---

## 🤖 3. ¿QUÉ HACE CADA ARCHIVO? (Tu Equipo)

Aquí tienes la lista de los archivos importantes que quedaron en tu carpeta:

*   **`smart_monitor.py` (EL JEFE):** Es el cerebro. Coordina a todos los demás robots.
*   **`monitor_flybondi.py` (EL EXPERTO):** Tiene la lógica pesada para conectarse a Flybondi y entender sus precios.
*   **`src/` (LA CAJA DE HERRAMIENTAS):**
    *   `fare_glitch_detector.py`: El robot que busca errores de precio (ej: VIP más barato que Turista).
    *   `source_analyzer.py`: El espía que lee el código de la web buscando promos ocultas.
    *   `abrir_reporte.py`: El ayudante que busca tu reporte más nuevo.
*   **`data/` (EL ARCHIVO):** Aquí se guardan todos los logs y reportes históricos.
*   **`archivo_viejo/` (EL SÓTANO):** Aquí guardé todos los scripts viejos y pruebas anteriores. Si alguna vez necesitas revivir algo antiguo, búscalo aquí.

---

## 🔧 4. SOLUCIÓN DE PROBLEMAS RÁPIDA

*   **¿No abre el reporte?**
    *   Asegúrate de haber corrido el monitor al menos una vez (tiene que haber generado un archivo HTML en `data/flybondi_logs`).
*   **¿Se cortó la luz o cerré la ventana?**
    *   Solo vuelve a abrir la terminal y corre el comando `python smart_monitor.py --daemon`.
*   **¿No llegan mensajes a Telegram?**
    *   Revisa que el archivo `.env` tenga tu TOKEN correcto (aunque si ya te llegaron antes, no toques nada).

---

¡Eso es todo! Tienes un sistema de vigilancia de nivel profesional trabajando para ti. 🚀
