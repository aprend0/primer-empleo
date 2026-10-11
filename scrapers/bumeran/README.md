# Bumeran Scraper (Primer Empleo)

Scraper híbrido síncrono completo para **bumeran.com.pe**.

## Análisis de Cloudflare

- El sitio está protegido por **Cloudflare** (ASN 13335).
- Peticiones HTTP simples (`requests`) reciben el **shell de Next.js** (HTML ~63KB, `<title>` vacío, sin ofertas).
- Navegadores reales (Playwright) pueden superar el challenge "Just a moment..." y obtener el HTML hidratado con las ofertas.
- `robots.txt` es permisivo para las rutas normales de búsqueda (`/empleos.html`, `/empleos-busqueda-*.html`).

**Recomendación:** Usar Playwright como motor principal. El fallback a requests rara vez funciona.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate          # Windows

pip install -r requirements.txt
playwright install chromium
```

## Uso rápido

```bash
python bumeran_scraper_sync.py
```

```python
from bumeran_scraper_sync import BumeranScraper

scraper = BumeranScraper(headless=True)
jobs, metrics = scraper.get_jobs(keyword="desarrollador", max_pages=2)
print(metrics)
print(jobs[0] if jobs else "Sin resultados")
```

## Esquema de salida

```json
{
  "portal": "Bumeran",
  "titulo": "Desarrollador de Software",
  "empresa": "SONDA",
  "ubicacion": "San Isidro, Lima",
  "modalidad": "Híbrido",
  "url_origen": "https://www.bumeran.com.pe/empleos/...",
  "fecha_publicacion": "hace 2 días",
  "descripcion_corta": "..."
}
```

## Métricas (tabla scraper_runs)

- `total_extraidos`
- `errores`
- `tiempo_ejecucion`
- `motor_utilizado` (playwright / requests+html / none)
- `paginas_procesadas`
- `estado` (success / partial / failed)

## Cómo colaborar / mejorar

1. Clona la rama `feature/scraping`.
2. Ejecuta el scraper y observa los logs.
3. Si retorna 0 resultados:
   - Abre Bumeran en el navegador → DevTools → Network → Fetch/XHR.
   - Localiza el endpoint real (ej. `searchNormalizado` o similar).
   - Actualiza `INTERNAL_API_CANDIDATES` o la lógica de interceptación en Playwright.
4. Abre un Pull Request hacia `develop` o `main`.

## Plan B (Gantt T5.5)

Si `estado == "failed"`, pausar el conector Bumeran y continuar con los demás portales.
