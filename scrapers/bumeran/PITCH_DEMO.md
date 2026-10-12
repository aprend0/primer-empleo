# Pitch de 1 Minuto — Bumeran Scraper

## Guion para pantalla compartida

---

**[0:00 - 0:10] Apertura**

> "Buenas, soy Néstor. Les presento el módulo de scraping de Bumeran, mi parte asignada en el Gantt como T5.5.BUM."

---

**[0:10 - 0:30] Técnica**

> "El scraper es 100% síncrono, pensado para integrarse fácil en el pipeline. Usa un motor híbrido: primero intenta Playwright para superar la protección de Cloudflare, y si eso falla, tiene fallback a requests."

> "En lugar de depender de selectores CSS frágiles, extraemos directamente el JSON interno que el frontend de Bumeran ya tiene estructurado. Eso nos da datos limpios: título, empresa, ubicación, modalidad y URL."

---

**[0:30 - 0:45] Resiliencia**

> "Implementamos throttling con delays aleatorios entre 1.5 y 3 segundos para no saturar el sitio. También hay reintentos con backoff exponencial ante errores 429 o 5xx. Si una página falla, el scraper continúa con las siguientes."

---

**[0:45 - 1:00] Integración**

> "La salida está normalizada en un diccionario estándar y las métricas — total extraído, errores, tiempo, motor usado — están listas para insertarse en la tabla scraper_runs. Esto permite al pipeline decidir si pausar el conector según el Plan B del Gantt."

> "Eso es todo de mi lado. ¿Preguntas?"

---

## Frases clave si preguntan

| Pregunta | Respuesta |
|----------|-----------|
| ¿Por qué Playwright? | Cloudflare bloquea requests simples. Playwright simula un navegador real. |
| ¿Qué pasa si falla? | El Plan B dice pausar Bumeran y continuar con otros portales. |
| ¿Cuántas ofertas? | Depende del keyword. En pruebas, 10-20 por página. |
| ¿Es legal? | Solo datos públicos. Respetamos robots.txt y rate limiting. |
