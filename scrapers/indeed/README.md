# Indeed Scraper (Primer Empleo)

Scraper híbrido síncrono para **pe.indeed.com**.

## Advertencia legal / ToS

Indeed prohíbe explícitamente el scraping automatizado sin permiso escrito (ver Terms of Service).
Este módulo es para uso interno del proyecto Primer Empleo y debe respetar:
- `robots.txt` (muchas rutas están disallow)
- Rate limiting agresivo
- No uso comercial ni redistribución de datos

## Extracción de datos

Indeed embebe los resultados de búsqueda en:
```js
window.mosaic.providerData["mosaic-provider-jobcards"]
```
El scraper prioriza este JSON (más estable que selectores CSS).

## Instalación

```bash
pip install -r requirements.txt
playwright install chromium
```

## Uso

```python
from indeed_scraper_sync import IndeedScraper

scraper = IndeedScraper()
jobs, metrics = scraper.get_jobs(keyword="desarrollador", location="Lima", max_pages=2)
print(metrics)
```

## Esquema

Compatible con el de Bumeran + campos extra (`salario`, `jobkey`).

## Plan B

Si falla, pausar conector y continuar con otros portales.
