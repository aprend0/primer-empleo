# Guía Completa — Bumeran Scraper (T5.5.BUM)

**Para dominar el tema y presentarlo en la reunión.**

---

## 1. ¿Qué hace este módulo?

Extrae ofertas de empleo de **bumeran.com.pe** de forma automática y las entrega en un formato estándar listo para el pipeline de Primer Empleo.

---

## 2. ¿Por qué es difícil?

Bumeran está protegido por **Cloudflare**.  
Una petición HTTP simple (`requests`) recibe una página vacía o el mensaje "Just a moment...".  
El sitio es una SPA que carga los datos con JavaScript.

---

## 3. ¿Cómo lo resolvemos?

**Motor híbrido síncrono:**

1. **Playwright (primario)** → Abre un navegador real, espera el challenge de Cloudflare y extrae el HTML renderizado.
2. **requests (fallback)** → Solo si Playwright no está disponible (casi nunca funciona en este sitio).

---

## 4. ¿De dónde sacamos los datos?

Buscamos el **JSON interno** que el frontend ya tiene:

```html
<script id="__NEXT_DATA__" type="application/json">
  { ... ofertas aquí ... }
</script>
```

Si no existe, parseamos el HTML buscando links con `/empleos/`.

---

## 5. Campos que extraemos

| Campo               | Ejemplo                          |
|---------------------|----------------------------------|
| titulo              | Desarrollador Backend Senior     |
| empresa             | SONDA                            |
| ubicacion           | San Isidro, Lima                 |
| modalidad           | Híbrido / Remoto / Presencial    |
| url_origen          | https://www.bumeran.com.pe/...   |
| fecha_publicacion   | hace 2 días                     |
| descripcion_corta   | Resumen del puesto               |

---

## 6. ¿Cómo evitamos ser bloqueados?

- Delays aleatorios de 1.5 a 3 segundos entre páginas.
- User-Agents rotativos.
- Reintentos con backoff ante errores 429/5xx.
- Si una página falla, continuamos con las siguientes.

---

## 7. ¿Qué retorna?

```python
jobs, metrics = scraper.get_jobs(keyword="desarrollador", max_pages=2)
```

**metrics** para la tabla `scraper_runs`:

```json
{
  "total_extraidos": 15,
  "errores": 0,
  "tiempo_ejecucion": 12.5,
  "motor_utilizado": "playwright",
  "estado": "success",
  "fuente": "bumeran"
}
```

---

## 8. Plan B

Si `estado == "failed"`, el pipeline pausa Bumeran y continúa con los demás portales.

---

## 9. Cómo ejecutar la demo

```bash
cd scrapers/bumeran
python demo_bumeran.py
```

El script muestra logs visuales, una tabla de ofertas y las métricas.  
Si la extracción real falla, usa datos simulados automáticamente.

---

## 10. Checklist pre-demo (10 minutos antes)

1. Activar entorno virtual
2. Verificar dependencias (`pip list`)
3. Limpiar la terminal (`clear`)
4. Probar: `python demo_bumeran.py`
5. Tener el README abierto por si preguntan

---

## 11. Pitch de 1 minuto

> "Buenas, soy Néstor. Les presento el módulo de scraping de Bumeran, T5.5.BUM."

> "El scraper es 100% síncrono. Usa Playwright para superar Cloudflare y extrae el JSON interno del frontend. Eso nos da datos limpios: título, empresa, ubicación, modalidad y URL."

> "Tiene throttling de 1.5 a 3 segundos y reintentos ante errores. Si una página falla, continúa con las siguientes."

> "La salida está normalizada y las métricas están listas para la tabla scraper_runs. Eso permite al pipeline aplicar el Plan B si algo falla."

> "Eso es todo de mi lado. ¿Preguntas?"

---

## 12. Resumen en una frase

> "Usamos Playwright para superar Cloudflare, extraemos el JSON interno del frontend, normalizamos los datos y entregamos métricas listas para auditoría."

---

**Repositorio:** https://github.com/aprend0/primer-empleo/tree/feature/scraping/scrapers/bumeran
