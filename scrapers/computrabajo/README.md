# Computrabajo Scraper (Primer Empleo)

Scraper para **pe.computrabajo.com** (portal #1 de empleo en Perú).

## Uso

```bash
pip install -r ../bumeran/requirements.txt
playwright install chromium
python computrabajo_scraper_sync.py
```

```python
from computrabajo_scraper_sync import ComputrabajoScraper
jobs, metrics = ComputrabajoScraper().get_jobs(keyword="desarrollador")
```
