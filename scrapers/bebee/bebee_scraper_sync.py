#!/usr/bin/env python3
"""BeBeeScraper - bebee.com/pe | T5.5.BEB"""
import json, logging, random, time
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"]
BASE_URL = "https://bebee.com"
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("BeBeeScraper")

class BeBeeScraper:
    def __init__(self, delay_range=(2.0, 4.0), headless=True):
        self.delay_range, self.headless = delay_range, headless
        self.session = requests.Session()

    def get_jobs(self, keyword=None, max_pages=2):
        start = time.perf_counter()
        jobs, errors, pages, motor = [], 0, 0, "none"
        logger.info("Iniciando BeBee | keyword=%s | max_pages=%d", keyword, max_pages)
        for page_num in range(1, max_pages + 1):
            try:
                url = self._build_url(keyword, page_num)
                logger.info("Página %d → %s", page_num, url)
                page_jobs, m = self._extract(url)
                if m != "none": motor = m
                if page_jobs:
                    jobs.extend(page_jobs); pages += 1
                    logger.info("  → %d ofertas (total: %d)", len(page_jobs), len(jobs))
                else:
                    errors += 1
                time.sleep(random.uniform(*self.delay_range))
            except Exception as e:
                errors += 1
                logger.error("Error: %s", e)
        elapsed = time.perf_counter() - start
        status = "success" if errors == 0 and jobs else ("partial" if jobs else "failed")
        return jobs, {"total_extraidos": len(jobs), "errores": errors, "tiempo_ejecucion": round(elapsed, 2), "motor_utilizado": motor, "paginas_procesadas": pages, "estado": status, "fuente": "bebee", "timestamp": datetime.now(timezone.utc).isoformat()}

    def _extract(self, url):
        if PLAYWRIGHT_AVAILABLE:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=self.headless, args=["--disable-blink-features=AutomationControlled"])
                    page = browser.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(2000)
                    html = page.content(); browser.close()
                    jobs = self._parse(html)
                    if jobs: return jobs, "playwright"
            except Exception: pass
        try:
            resp = self.session.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=15)
            if resp.status_code == 200:
                jobs = self._parse(resp.text)
                if jobs: return jobs, "requests"
        except Exception: pass
        return [], "none"

    def _parse(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results, seen = [], set()
        for a in soup.select("a[href*='/pe/jobs/'], a[href*='/jobs/']"):
            href = a.get("href")
            if not href or href in seen or "/pe/jobs/" not in href: continue
            seen.add(href)
            title = a.get_text(strip=True)
            if not title or len(title) < 5: continue
            results.append({"portal": "BeBee", "titulo": title, "empresa": "Confidencial", "ubicacion": "Perú", "modalidad": None, "url_origen": urljoin(BASE_URL, href), "fecha_publicacion": None, "descripcion_corta": ""})
        return results

    def _build_url(self, keyword, page):
        if keyword:
            slug = quote_plus(keyword.lower().replace(" ", "-"))
            base = f"{BASE_URL}/pe/jobs/{slug}"
        else:
            base = f"{BASE_URL}/pe/jobs"
        return f"{base}?page={page}" if page > 1 else base

if __name__ == "__main__":
    scraper = BeBeeScraper()
    jobs, metrics = scraper.get_jobs(keyword="desarrollador", max_pages=1)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Jobs: {len(jobs)}")
