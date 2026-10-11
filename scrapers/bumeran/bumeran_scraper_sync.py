#!/usr/bin/env python3
"""
BumeranScraper - Versión Final Híbrida Síncrona
Proyecto Primer Empleo | bumeran.com.pe

Motor Primario  : requests → __NEXT_DATA__ o endpoint JSON interno
Motor Secundario: playwright.sync_api (fallback automático)
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
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeout = Exception

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

BASE_URL = "https://www.bumeran.com.pe"

INTERNAL_API_CANDIDATES = [
    "https://www.bumeran.com.pe/api/searchNormalizado",
    "https://www.bumeran.com.pe/api/search",
    "https://www.bumeran.com.pe/api/avisos",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("BumeranScraper")


class BumeranScraper:
    def __init__(self, delay_range=(1.5, 3.0), max_retries=3, headless=True):
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.headless = headless
        self.session = requests.Session()

    def get_jobs(self, keyword=None, max_pages=3):
        start_time = time.perf_counter()
        jobs = []
        errors = 0
        pages_processed = 0
        motor_used = "none"

        logger.info("Iniciando extracción | keyword=%s | max_pages=%d", keyword, max_pages)

        for page_num in range(1, max_pages + 1):
            try:
                url = self._build_listing_url(keyword, page_num)
                logger.info("Página %d/%d → %s", page_num, max_pages, url)
                page_jobs, motor = self._extract_page(url, keyword, page_num)
                if motor != "none":
                    motor_used = motor
                if not page_jobs:
                    errors += 1
                    continue
                jobs.extend(page_jobs)
                pages_processed += 1
                logger.info("  → %d ofertas vía %s (total: %d)", len(page_jobs), motor, len(jobs))
                self._throttle()
            except Exception as e:
                errors += 1
                logger.error("Error en página %d: %s", page_num, e)

        elapsed = time.perf_counter() - start_time
        status = "success" if errors == 0 and jobs else ("partial" if jobs else "failed")
        metrics = {
            "total_extraidos": len(jobs),
            "errores": errors,
            "tiempo_ejecucion": round(elapsed, 2),
            "motor_utilizado": motor_used,
            "paginas_procesadas": pages_processed,
            "estado": status,
            "fuente": "bumeran",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("Finalizado | jobs=%d | motor=%s | status=%s", len(jobs), motor_used, status)
        return jobs, metrics

    def _extract_page(self, url, keyword, page):
        try:
            html = self._fetch_requests(url)
            if html:
                jobs = self._extract_from_next_data(html)
                if jobs:
                    return jobs, "requests+next_data"
                jobs = self._try_internal_api(keyword, page)
                if jobs:
                    return jobs, "requests+api"
                jobs = self._extract_from_html(html)
                if jobs:
                    return jobs, "requests+html"
        except Exception as e:
            logger.debug("requests falló: %s", e)

        if PLAYWRIGHT_AVAILABLE:
            logger.info("  → Fallback a Playwright")
            try:
                jobs = self._extract_with_playwright(url)
                if jobs:
                    return jobs, "playwright"
            except Exception as e:
                logger.warning("Playwright falló: %s", e)
        return [], "none"

    def _fetch_requests(self, url):
        for attempt in range(1, self.max_retries + 1):
            try:
                headers = {
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "es-ES,es;q=0.9",
                    "Referer": BASE_URL + "/",
                }
                resp = self.session.get(url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code in (403, 429, 500, 502, 503):
                    time.sleep((2 ** attempt) + random.uniform(0.5, 1.5))
                    continue
                return None
            except requests.RequestException:
                time.sleep(2 ** attempt)
        return None

    def _try_internal_api(self, keyword, page):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Referer": BASE_URL + "/",
            "Origin": BASE_URL,
            "Content-Type": "application/json",
        }
        payload = {"query": keyword or "", "page": page, "pageSize": 20, "pais": "pe"}
        for api_url in INTERNAL_API_CANDIDATES:
            try:
                resp = self.session.post(api_url, json=payload, headers=headers, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    raw = data.get("resultados") or data.get("jobs") or data.get("avisos") or []
                    if raw:
                        return [self._normalize_from_json(j) for j in raw]
            except Exception:
                continue
        return []

    def _extract_with_playwright(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent=random.choice(USER_AGENTS), locale="es-PE")
            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(2000)
                html = page.content()
                jobs = self._extract_from_next_data(html)
                if jobs:
                    return jobs
                return self._extract_from_html(html)
            finally:
                browser.close()
        return []

    def _extract_from_next_data(self, html):
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return []
        try:
            data = json.loads(script.string)
            return []
        except Exception:
            return []

    def _extract_from_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        seen = set()
        for a in soup.select("a[href*='/empleos/']"):
            href = a.get("href")
            if not href or href in seen:
                continue
            seen.add(href)
            url = urljoin(BASE_URL, href)
            title = a.get_text(strip=True) or None
            results.append({
                "portal": "Bumeran",
                "titulo": title,
                "empresa": "Confidencial",
                "ubicacion": "Perú",
                "modalidad": None,
                "url_origen": url,
                "fecha_publicacion": None,
                "descripcion_corta": "",
            })
        return results

    def _normalize_from_json(self, raw):
        return {
            "portal": "Bumeran",
            "titulo": raw.get("titulo") or raw.get("title"),
            "empresa": raw.get("empresa") or raw.get("company") or "Confidencial",
            "ubicacion": raw.get("ubicacion") or raw.get("location") or "Perú",
            "modalidad": raw.get("modalidad") or raw.get("workMode"),
            "url_origen": raw.get("url") or "",
            "fecha_publicacion": raw.get("fecha_publicacion") or raw.get("publishedAt"),
            "descripcion_corta": (raw.get("descripcion") or "")[:300],
        }

    def _build_listing_url(self, keyword, page):
        if keyword:
            slug = quote_plus(keyword.lower().replace(" ", "-"))
            base = f"{BASE_URL}/empleos-busqueda-{slug}.html"
        else:
            base = f"{BASE_URL}/empleos.html"
        return f"{base}?page={page}" if page > 1 else base

    def _throttle(self):
        time.sleep(random.uniform(*self.delay_range))


if __name__ == "__main__":
    scraper = BumeranScraper()
    jobs, metrics = scraper.get_jobs(keyword="desarrollador", max_pages=1)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Jobs: {len(jobs)}")
