#!/usr/bin/env python3
"""Runner unificado para todos los scrapers del proyecto Primer Empleo."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE / "bumeran"))
sys.path.insert(0, str(BASE / "indeed"))
sys.path.insert(0, str(BASE / "computrabajo"))
sys.path.insert(0, str(BASE / "jobsora"))
sys.path.insert(0, str(BASE / "bebee"))
sys.path.insert(0, str(BASE / "practicas"))

from bumeran_scraper_sync import BumeranScraper
from indeed_scraper_sync import IndeedScraper
from computrabajo_scraper_sync import ComputrabajoScraper
from jobsora_scraper_sync import JobsoraScraper
from bebee_scraper_sync import BeBeeScraper
from practicas_scraper_sync import PracticasScraper

def main():
    results = {}
    scrapers = [
        ("computrabajo", ComputrabajoScraper, {"keyword": "desarrollador", "max_pages": 1}),
        ("bumeran", BumeranScraper, {"keyword": "desarrollador", "max_pages": 1}),
        ("indeed", IndeedScraper, {"keyword": "desarrollador", "location": "Lima", "max_pages": 1}),
        ("jobsora", JobsoraScraper, {"keyword": "desarrollador", "max_pages": 1}),
        ("bebee", BeBeeScraper, {"keyword": "desarrollador", "max_pages": 1}),
        ("practicas", PracticasScraper, {"keyword": "desarrollador", "max_pages": 1}),
    ]

    for name, cls, kwargs in scrapers:
        print(f"\n=== {name.upper()} ===")
        try:
            scraper = cls()
            jobs, metrics = scraper.get_jobs(**kwargs)
            results[name] = metrics
            print(f"  Extraídas: {metrics.get('total_extraidos', 0)} | Estado: {metrics.get('estado')}")
        except Exception as e:
            results[name] = {"estado": "error", "error": str(e)}
            print(f"  Error: {e}")

    print("\n=== RESUMEN ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
