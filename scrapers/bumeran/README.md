# Bumeran Scraper (T5.5.BUM)

**Responsable:** Néstor  
**Portal:** bumeran.com.pe  
**Proyecto:** Primer Empleo

Scraper híbrido síncrono listo para verificación y colaboración.

## Clonar y verificar

```bash
git clone -b feature/scraping https://github.com/aprend0/primer-empleo.git
cd primer-empleo/scrapers/bumeran

python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate          # Windows

pip install -r requirements.txt
playwright install chromium

python bumeran_scraper_sync.py
```

El script genera `sample_output.json` con métricas y ejemplos de ofertas.

## Análisis de Cloudflare

- Protegido por Cloudflare (ASN 13335).
- `requests` recibe el shell de Next.js (sin datos).
- Playwright supera el challenge y obtiene el HTML hidratado.
- `robots.txt` es permisivo para rutas normales de búsqueda.

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

## Métricas (scraper_runs)

- `total_extraidos`, `errores`, `tiempo_ejecucion`
- `motor_utilizado` (playwright / requests+html / none)
- `paginas_procesadas`, `estado` (success / partial / failed)

## Colaborar

1. Clona la rama `feature/scraping`.
2. Ejecuta y revisa logs + `sample_output.json`.
3. Si retorna 0 resultados, inspecciona Network tab en el navegador.
4. Abre un Pull Request.

**Nota:** El repositorio debe estar público para clonación libre. Si es privado, el owner puede hacerlo público en Settings → General → Danger Zone.
