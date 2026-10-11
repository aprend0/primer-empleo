#!/usr/bin/env python3
"""
BumeranScraper - Versión Mejorada para Verificación
Proyecto Primer Empleo | bumeran.com.pe | T5.5.BUM

Autor: Néstor (parte del equipo Primer Empleo)

Características:
- Motor híbrido síncrono (Playwright primario + requests fallback)
- Manejo de Cloudflare
- Extracción de __NEXT_DATA__ + HTML
- Métricas para scraper_runs
- Logging claro para depuración
"""

import json
import logging
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("BumeranScraper")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

BASE_URL = "https://www.bumeran.com.pe"


class BumeranScraper:
    """Scraper híbrido síncrono mejorado para Bumeran Perú."""

    def __init__(self, delay_range: Tuple[float, float] = (1.5, 3.0), max_retries: int = 2, headless: bool = True):
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.headless = headless
        self.session = requests.Session()

    def get_jobs(self, keyword: Optional[str] = None, max_pages: int = 3, save_sample: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Extrae ofertas y retorna (jobs, metrics). Opcionalmente guarda sample_output.json."""
        start = time.perf_counter()
        jobs: List[Dict[str, Any]] = []
        errors = 0
        pages_processed = 0
        motor_used = "none"

        logger.info("Iniciando extracción Bumeran | keyword=%s | max_pages=%d", keyword or "todos", max_pages)

        for page_num in range(1, max_pages + 1):
            try:
                url = self._build_listing_url(keyword, page_num)
                logger.info("Página %d/%d → %s", page_num, max_pages, url)

                page_jobs, motor = self._extract_page(url)
                if motor != "none":
                    motor_used = motor

                if page_jobs:
                    jobs.extend(page_jobs)
                    pages_processed += 1
                    logger.info("  → %d ofertas vía %s (acumulado: %d)", len(page_jobs), motor, len(jobs))
                else:
                    errors += 1
                    logger.warning("  → 0 ofertas en página %d", page_num)

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
            "fuente": "bumeran",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "keyword": keyword,
        }
        logger.info("Finalizado | jobs=%d | motor=%s | status=%s | %.1fs", len(jobs), motor_used, status, elapsed)

        if save_sample and jobs:
            self._save_sample(jobs, metrics)

        return jobs, metrics

    def _save_sample(self, jobs: List[Dict], metrics: Dict):
        sample = {"metrics": metrics, "jobs_sample": jobs[:5]}
        path = Path(__file__).parent / "sample_output.json"
        path.write_text(json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Sample guardado en %s", path)

    def _extract_page(self, url: str) -> Tuple[List[Dict[str, Any]], str]:
        if PLAYWRIGHT_AVAILABLE:
            jobs = self._extract_with_playwright(url)
            if jobs:
                return jobs, "playwright"

        html = self._fetch_requests(url)
        if html and "Just a moment" not in html and "cf-browser-verification" not in html.lower():
            jobs = self._extract_from_html(html)
            if jobs:
                return jobs, "requests+html"

        return [], "none"

    def _extract_with_playwright(self, url: str) -> List[Dict[str, Any]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                locale="es-PE",
                viewport={"width": 1366, "height": 768},
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3500)
                content = page.content()
                if "Just a moment" in content or "cf-challenge" in content.lower():
                    logger.info("  Challenge Cloudflare detectado, esperando...")
                    page.wait_for_timeout(7000)
                    content = page.content()

                jobs = self._extract_from_next_data(content)
                if jobs:
                    logger.info("  → Extraído de __NEXT_DATA__")
                    return jobs
                return self._extract_from_html(content)
            except PlaywrightTimeout:
                logger.warning("Playwright timeout en %s", url)
                return []
            except Exception as e:
                logger.warning("Playwright error: %s", e)
                return []
            finally:
                browser.close()
        return []

    def _fetch_requests(self, url: str) -> Optional[str]:
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9",
                "Referer": BASE_URL + "/",
            }
            resp = self.session.get(url, headers=headers, timeout=15)
            return resp.text if resp.status_code == 200 else None
        except Exception as e:
            logger.debug("requests falló: %s", e)
            return None

    def _extract_from_next_data(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return []
        try:
            data = json.loads(script.string)
            raw = self._find_jobs_recursive(data)
            return [self._normalize(j) for j in raw if isinstance(j, dict)]
        except Exception as e:
            logger.debug("Error parseando __NEXT_DATA__: %s", e)
            return []

    def _find_jobs_recursive(self, obj: Any, depth: int = 0) -> List[Dict]:
        if depth > 7:
            return []
        found = []
        if isinstance(obj, dict):
            for v in obj.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    keys = str(list(v[0].keys())).lower()
                    if any(k in keys for k in ["titulo", "title", "url", "id", "aviso", "empresa", "company"]):
                        found.extend(v)
                else:
                    found.extend(self._find_jobs_recursive(v, depth + 1))
        elif isinstance(obj, list):
            for item in obj[:20]:
                found.extend(self._find_jobs_recursive(item, depth + 1))
        return found[:80]

    def _extract_from_html(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        seen = set()
        for a in soup.select("a[href*='/empleos/']"):
            href = a.get("href")
            if not href or href in seen:
                continue
            seen.add(href)
            full_url = urljoin(BASE_URL, href)
            title = a.get_text(strip=True) or None
            if not title or len(title) < 5:
                continue
            parent = a.find_parent(["article", "div", "li", "section"]) or a
            text = parent.get_text(" ", strip=True)
            results.append(self._normalize_from_text(title, full_url, text))
        return results

    def _normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "portal": "Bumeran",
            "titulo": raw.get("titulo") or raw.get("title") or raw.get("nombre"),
            "empresa": raw.get("empresa") or raw.get("company") or raw.get("companyName") or "Confidencial",
            "ubicacion": raw.get("ubicacion") or raw.get("location") or raw.get("ciudad") or "Perú",
            "modalidad": self._norm_modality(raw.get("modalidad") or raw.get("workMode")),
            "url_origen": self._abs_url(raw.get("url") or raw.get("url_origen") or ""),
            "fecha_publicacion": raw.get("fecha_publicacion") or raw.get("publishedAt") or raw.get("fecha"),
            "descripcion_corta": (raw.get("descripcion_corta") or raw.get("snippet") or "")[:400],
        }

    def _normalize_from_text(self, title: Optional[str], url: str, text: str) -> Dict[str, Any]:
        return {
            "portal": "Bumeran",
            "titulo": title,
            "empresa": "Confidencial",
            "ubicacion": self._extract_location(text) or "Perú",
            "modalidad": self._norm_modality(self._extract_modality(text)),
            "url_origen": url,
            "fecha_publicacion": self._extract_date(text),
            "descripcion_corta": text[:300],
        }

    @staticmethod
    def _norm_modality(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        t = str(text).lower()
        if "remoto" in t:
            return "Remoto"
        if "híbrido" in t or "hibrido" in t:
            return "Híbrido"
        if "presencial" in t:
            return "Presencial"
        return str(text).strip()

    @staticmethod
    def _extract_modality(text: str) -> Optional[str]:
        t = text.lower()
        if "remoto" in t:
            return "Remoto"
        if "híbrido" in t or "hibrido" in t:
            return "Híbrido"
        if "presencial" in t:
            return "Presencial"
        return None

    @staticmethod
    def _extract_location(text: str) -> Optional[str]:
        for city in ["Lima", "Arequipa", "Cusco", "Trujillo", "Piura", "Callao", "Chiclayo", "San Isidro", "Miraflores", "Surco", "Ate"]:
            if city in text:
                return city
        return None

    @staticmethod
    def _extract_date(text: str) -> Optional[str]:
        m = re.search(r"(Publicado|Actualizado|hace) [^
.]+", text, re.I)
        return m.group(0) if m else None

    def _abs_url(self, url: str) -> str:
        if url and not url.startswith("http"):
            return urljoin(BASE_URL, url)
        return url

    def _build_listing_url(self, keyword: Optional[str], page: int) -> str:
        if keyword:
            slug = quote_plus(keyword.lower().replace(" ", "-"))
            base = f"{BASE_URL}/empleos-busqueda-{slug}.html"
        else:
            base = f"{BASE_URL}/empleos.html"
        return f"{base}?page={page}" if page > 1 else base

    def _throttle(self):
        time.sleep(random.uniform(*self.delay_range))


if __name__ == "__main__":
    print("=== BumeranScraper - Verificación ===")
    scraper = BumeranScraper(headless=True)
    jobs, metrics = scraper.get_jobs(keyword="desarrollador", max_pages=1, save_sample=True)
    print("\n=== Métricas ===")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    if jobs:
        print("\n=== Ejemplo de oferta ===")
        print(json.dumps(jobs[0], indent=2, ensure_ascii=False))
        print(f"\nTotal extraído: {len(jobs)}")
    else:
        print("\nNo se extrajeron ofertas. Verifica Playwright y conexión.")
