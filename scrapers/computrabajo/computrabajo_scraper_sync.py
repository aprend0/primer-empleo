#!/usr/bin/env python3
"""
ComputrabajoScraper - Versión Completa
Proyecto Primer Empleo | pe.computrabajo.com

Portal #1 de empleo en Perú.
Motor híbrido síncrono (requests + Playwright fallback).
"""

import json
import logging
import random
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("ComputrabajoScraper")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

BASE_URL = "https://pe.computrabajo.com"


class ComputrabajoScraper:
    """Scraper híbrido síncrono para Computrabajo Perú."""

    def __init__(self, delay_range: Tuple[float, float] = (1.5, 3.0), headless: bool = True):
        self.delay_range = delay_range
        self.headless = headless
        self.session = requests.Session()

    def get_jobs(self, keyword: Optional[str] = None, max_pages: int = 2) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        start = time.perf_counter()
        jobs: List[Dict[str, Any]] = []
        errors = 0
        pages_processed = 0
        motor_used = "none"

        logger.info("Iniciando Computrabajo | keyword=%s | pages=%d", keyword, max_pages)

        for page_num in range(1, max_pages + 1):
            try:
                url = self._build_url(keyword, page_num)
                logger.info("Página %d → %s", page_num, url)

                page_jobs, motor = self._extract_page(url)
                if motor != "none":
                    motor_used = motor

                if page_jobs:
                    jobs.extend(page_jobs)
                    pages_processed += 1
                    logger.info("  → %d ofertas vía %s", len(page_jobs), motor)
                else:
                    errors += 1

                self._throttle()
            except Exception as e:
                errors += 1
                logger.error("Error página %d: %s", page_num, e)

        elapsed = time.perf_counter() - start
        status = "success" if errors == 0 and jobs else ("partial" if jobs else "failed")
        metrics = {
            "total_extraidos": len(jobs),
            "errores": errors,
            "tiempo_ejecucion": round(elapsed, 2),
            "motor_utilizado": motor_used,
            "paginas_procesadas": pages_processed,
            "estado": status,
            "fuente": "computrabajo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("Finalizado | jobs=%d | motor=%s | status=%s", len(jobs), motor_used, status)
        return jobs, metrics

    def _extract_page(self, url: str) -> Tuple[List[Dict[str, Any]], str]:
        html = self._fetch_requests(url)
        if html:
            jobs = self._extract_from_html(html)
            if jobs:
                return jobs, "requests+html"

        if PLAYWRIGHT_AVAILABLE:
            logger.info("  → Fallback Playwright")
            jobs = self._extract_with_playwright(url)
            if jobs:
                return jobs, "playwright"

        return [], "none"

    def _fetch_requests(self, url: str) -> Optional[str]:
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "es-PE,es;q=0.9"}
            resp = self.session.get(url, headers=headers, timeout=15)
            return resp.text if resp.status_code == 200 else None
        except Exception:
            return None

    def _extract_with_playwright(self, url: str) -> List[Dict[str, Any]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=["--disable-blink-features=AutomationControlled"])
            page = browser.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(2500)
                return self._extract_from_html(page.content())
            except Exception as e:
                logger.warning("Playwright: %s", e)
                return []
            finally:
                browser.close()

    def _extract_from_html(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        seen = set()

        for article in soup.select("article, div.iO, div[data-id]"):
            link = article.select_one("a[href*='/ofertas-de-trabajo/']")
            if not link:
                continue
            href = link.get("href")
            if not href or href in seen:
                continue
            seen.add(href)

            title = link.get_text(strip=True) or article.select_one("h2, h3")
            if hasattr(title, "get_text"):
                title = title.get_text(strip=True)
            company = article.select_one(".dO, .company, p")
            location = article.select_one(".dO, .location, span")
            text = article.get_text(" ", strip=True)

            results.append({
                "portal": "Computrabajo",
                "titulo": title,
                "empresa": company.get_text(strip=True) if company and hasattr(company, "get_text") else "Confidencial",
                "ubicacion": location.get_text(strip=True) if location and hasattr(location, "get_text") else "Perú",
                "modalidad": self._extract_modality(text),
                "url_origen": urljoin(BASE_URL, href),
                "fecha_publicacion": self._extract_date(text),
                "descripcion_corta": text[:400],
            })

        return results

    @staticmethod
    def _extract_modality(text: str) -> Optional[str]:
        t = text.lower()
        if "remoto" in t:
            return "Remoto"
        if "híbrido" in t or "hibrido" in t or "presencial y remoto" in t:
            return "Híbrido"
        if "presencial" in t:
            return "Presencial"
        return None

    @staticmethod
    def _extract_date(text: str) -> Optional[str]:
        m = re.search(r"Hace\s+\d+\s+(hora|día|días|semana)", text, re.I)
        return m.group(0) if m else None

    def _build_url(self, keyword: Optional[str], page: int) -> str:
        if keyword:
            slug = quote_plus(keyword.lower().replace(" ", "-"))
            base = f"{BASE_URL}/trabajo-de-{slug}"
        else:
            base = f"{BASE_URL}/ofertas-de-trabajo"
        return f"{base}?p={page}" if page > 1 else base

    def _throttle(self):
        time.sleep(random.uniform(*self.delay_range))


if __name__ == "__main__":
    scraper = ComputrabajoScraper()
    jobs, metrics = scraper.get_jobs(keyword="desarrollador", max_pages=1)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Jobs: {len(jobs)}")
