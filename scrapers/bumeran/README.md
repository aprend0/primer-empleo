# Bumeran Scraper (Primer Empleo)

Scraper híbrido síncrono para bumeran.com.pe.

## Instalación

```bash
pip install -r requirements.txt
playwright install chromium   # solo necesario para el fallback
```

## Uso

```python
from bumeran_scraper_sync import BumeranScraper

scraper = BumeranScraper()
jobs, metrics = scraper.get_jobs(keyword="desarrollador", max_pages=2)
print(metrics)
```

## Integración en el pipeline (T5.5.BUM)

1. Colocar `bumeran_scraper_sync.py` en el módulo de scrapers.
2. Llamar `get_jobs()` desde el workflow diario de GitHub Actions.
3. Registrar `metrics` en la tabla `scraper_runs`.
4. Plan B: si `estado == "failed"`, pausar el conector y continuar con los demás portales.

## Métricas (scraper_runs)

- total_extraidos
- errores
- tiempo_ejecucion
- motor_utilizado
- paginas_procesadas
- estado
