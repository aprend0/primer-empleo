#!/usr/bin/env python3
"""
IndeedScraper - Versión Completa
Proyecto Primer Empleo | pe.indeed.com

Notas importantes:
- Indeed tiene políticas estrictas contra scraping automatizado (ver ToS).
- Usar solo para fines del proyecto interno y respetar robots.txt.
- Datos embebidos en window.mosaic.providerData["mosaic-provider-jobcards"].
"""

import json
import logging
import random
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urljoin, urlencode

import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("IndeedScraper")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

BASE_URL = "https://pe.indeed.com"


class IndeedScraper:
    """Scraper híbrido síncrono para Indeed Perú (pe.indeed.com)."""

    def __init__(self, delay_range: Tuple[float, float] = (2.0, 4.0), max_retries: int = 2, headless: bool = True):
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.headless = headless
        self.session = requests.Session()

    def get_jobs(self, keyword: Optional[str] = None, location: str = "Lima", max_pages: int = 2) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        start = time.perf_counter()
        jobs: List[Dict[str, Any]] = []
        errors = 0
        pages_processed = 0
        motor_used = "none"

        logger.info("Iniciando extracción Indeed | q=%s | l=%s | pages=%d", keyword, location, max_pages)

        for page_num in range(max_pages):
            try:
                start_offset = page_num * 10
                url = self._build_search_url(keyword, location, start_offset)
                logger.info("Página %d → %s", page_num + 1, url)

                page_jobs, motor = self._extract_page(url)
                if motor != "none":
                    motor_used = motor

                if page_jobs:
                    jobs.extend(page_jobs)
                    pages_processed += 1
                    logger.info("  → %d ofertas vía %s (total: %d)", len(page_jobs), motor, len(jobs))
                else:
                    errors += 1

                self._throttle()
            except Exception as e:
                errors += 1
                logger.error("Error página %d: %s", page_num + 1, e)

        elapsed = time.perf_counter() - start
        status = "success" if errors == 0 and jobs else ("partial" if jobs else "failed")
        metrics = {
            "total_extraidos": len(jobs),
            "errores": errors,
            "tiempo_ejecucion": round(elapsed, 2),
            "motor_utilizado": motor_used,
            "paginas_procesadas": pages_processed,
            "estado": status,
            "fuente": "indeed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("Finalizado | jobs=%d | motor=%s | status=%s", len(jobs), motor_used, status)
        return jobs, metrics

    def _extract_page(self, url: str) -> Tuple[List[Dict[str, Any]], str]:
        # Primario: requests
        html = self._fetch_requests(url)
        if html:
            jobs = self._extract_from_mosaic(html)
            if jobs:
                return jobs, "requests+mosaic"
            jobs = self._extract_from_html(html)
            if jobs:
                return jobs, "requests+html"

        # Fallback Playwright
        if PLAYWRIGHT_AVAILABLE:
            logger.info("  → Fallback Playwright")
            jobs = self._extract_with_playwright(url)
            if jobs:
                return jobs, "playwright"

        return [], "none"

    def _fetch_requests(self, url: str) -> Optional[str]:
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-PE,es;q=0.9",
                "Referer": BASE_URL + "/",
            }
            resp = self.session.get(url, headers=headers, timeout=20)
            return resp.text if resp.status_code == 200 else None
        except Exception:
            return None

    def _extract_with_playwright(self, url: str) -> List[Dict[str, Any]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
            context = browser.new_context(user_agent=random.choice(USER_AGENTS), locale="es-PE")
            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3000)
                html = page.content()
                jobs = self._extract_from_mosaic(html)
                if jobs:
                    return jobs
                return self._extract_from_html(html)
            except Exception as e:
                logger.warning("Playwright error: %s", e)
                return []
            finally:
                browser.close()
        return []

    def _extract_from_mosaic(self, html: str) -> List[Dict[str, Any]]:
        """Extrae del JSON embebido window.mosaic.providerData['mosaic-provider-jobcards']."""
        pattern = r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});'
        matches = re.findall(pattern, html)
        if not matches:
            return []
        try:
            data = json.loads(matches[0])
            results = data.get("metaData", {}).get("mosaicProviderJobCardsModel", {}).get("results", [])
            return [self._normalize_from_mosaic(job) for job in results if isinstance(job, dict)]
        except Exception as e:
            logger.debug("Mosaic parse error: %s", e)
            return []

    def _normalize_from_mosaic(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        jobkey = raw.get("jobkey") or ""
        title = raw.get("title") or raw.get("normTitle")
        company = raw.get("company") or "Confidencial"
        location = raw.get("formattedLocation") or raw.get("jobLocationCity") or "Perú"
        salary = raw.get("salarySnippet", {}).get("salaryTextFormatted") or None
        snippet = raw.get("snippet") or ""
        url = f"{BASE_URL}/viewjob?jk={jobkey}" if jobkey else ""
        date = raw.get("formattedRelativeTime") or raw.get("pubDate")

        modality = None
        if "remote" in (raw.get("remoteLocation") or "").lower() or "remoto" in (location or "").lower():
            modality = "Remoto"

        return {
            "portal": "Indeed",
            "titulo": title,
            "empresa": company,
            "ubicacion": location,
            "modalidad": modality,
            "url_origen": url,
            "fecha_publicacion": date,
            "descripcion_corta": snippet[:500] if snippet else "",
            "salario": salary,
            "jobkey": jobkey,
        }

    def _extract_from_html(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for card in soup.select("div.job_seen_beacon, div.jobsearch-SerpJobCard, a.jcs-JobTitle"):
            title_elem = card.select_one("h2, a.jcs-JobTitle, span[title]")
            title = title_elem.get_text(strip=True) if title_elem else None
            if not title:
                continue
            company = card.select_one(".companyName, [data-testid='company-name']")
            location = card.select_one(".companyLocation, [data-testid='text-location']")
            results.append({
                "portal": "Indeed",
                "titulo": title,
                "empresa": company.get_text(strip=True) if company else "Confidencial",
                "ubicacion": location.get_text(strip=True) if location else "Perú",
                "modalidad": None,
                "url_origen": "",
                "fecha_publicacion": None,
                "descripcion_corta": "",
            })
        return results

    def _build_search_url(self, keyword: Optional[str], location: str, start: int = 0) -> str:
        params = {"q": keyword or "", "l": location, "start": start}
        return f"{BASE_URL}/jobs?{urlencode(params)}"

    def _throttle(self):
        time.sleep(random.uniform(*self.delay_range))


if __name__ == "__main__":
    print("=== IndeedScraper - Prueba ===")
    scraper = IndeedScraper(headless=True)
    jobs, metrics = scraper.get_jobs(keyword="desarrollador", location="Lima", max_pages=1)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    if jobs:
        print("\nEjemplo:")
        print(json.dumps(jobs[0], indent=2, ensure_ascii=False))
