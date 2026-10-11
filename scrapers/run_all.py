#!/usr/bin/env python3
"""Runner unificado para todos los scrapers."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "bumeran"))
sys.path.insert(0, str(Path(__file__).parent / "indeed"))
sys.path.insert(0, str(Path(__file__).parent / "computrabajo"))

from bumeran_scraper_sync import BumeranScraper
from indeed_scraper_sync import IndeedScraper
from computrabajo_scraper_sync import ComputrabajoScraper

def main():
    results = {}

    print("=== Computrabajo ===")
    ct = ComputrabajoScraper()
    jobs, metrics = ct.get_jobs(keyword="desarrollador", max_pages=1)
    results["computrabajo"] = metrics

    print("\n=== Bumeran ===")
    bum = BumeranScraper()
    jobs, metrics = bum.get_jobs(keyword="desarrollador", max_pages=1)
    results["bumeran"] = metrics

    print("\n=== Indeed ===")
    ind = IndeedScraper()
    jobs, metrics = ind.get_jobs(keyword="desarrollador", location="Lima", max_pages=1)
    results["indeed"] = metrics

    print("\n=== RESUMEN ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
