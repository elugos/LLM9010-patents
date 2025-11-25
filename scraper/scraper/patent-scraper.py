import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re

TEST_MODE = False
URL_FILE = "patent_urls.txt"
OUT_FILE = "patents_test.json" if TEST_MODE else "patents.json"

with open(URL_FILE, encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

if TEST_MODE:
    urls = urls[:5]

patents = []

def safe_get(tag, attr):
    return tag.get(attr, "").strip() if tag and tag.has_attr(attr) else None

def extract_dates_from_timeline(soup):
    filing_date = publication_date = expiration_date = None
    date_regex = re.compile(r"\d{4}-\d{2}-\d{2}")

    for div in soup.select("div.event.layout.horizontal.style-scope.application-timeline"):
        # Filing date
        filed_div = div.find("div", class_="filed")
        if filed_div and not filing_date:
            text = filed_div.get_text(strip=True)
            if date_regex.match(text):
                filing_date = text

        # Publication date
        pub_div = div.find("div", class_="publication")
        if pub_div and not publication_date:
            text = pub_div.get_text(strip=True)
            if date_regex.match(text):
                publication_date = text

        # Expiration date
        legal_div = div.find("div", class_="legal-status")
        if legal_div and not expiration_date:
            text = legal_div.get_text(strip=True)
            if date_regex.match(text):  # only assign if it looks like a date
                expiration_date = text

    return filing_date, publication_date, expiration_date

# Optional: fallback with Playwright for dynamic content
USE_PLAYWRIGHT = True
if USE_PLAYWRIGHT:
    from playwright.sync_api import sync_playwright
    playwright_context = sync_playwright().start()
    browser = playwright_context.firefox.launch(headless=True)
    page = browser.new_page()

for i, url in enumerate(urls, 1):
    print(f"{i}/{len(urls)}: {url}")
    try:
        r = requests.get(url, timeout=10)
        r.encoding = "utf-8"
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] {url} → {e}")
        continue

    soup = BeautifulSoup(r.text, "html.parser")

    title = safe_get(soup.find("meta", {"name": "DC.title"}), "content")
    inventors = [m["content"].strip() for m in soup.find_all("meta", {"scheme": "inventor"}) if m.has_attr("content")]

    # Updated description extraction for current Google Patents layout
    description = ""
    desc_container = soup.find("patent-text", {"name": "description"})
    if desc_container:
        paragraphs = desc_container.find_all("div", class_="description-paragraph")
        description = "\n".join(p.get_text(" ", strip=True) for p in paragraphs if p.get_text(strip=True))

    # Extract dates from timeline
    filing_date, publication_date, expiration_date = extract_dates_from_timeline(soup)

    # Playwright fallback for missing critical dates or description
    if USE_PLAYWRIGHT and (not filing_date or not publication_date or not expiration_date or not description):
        page.goto(url, timeout=30000)
        time.sleep(2)
        soup_js = BeautifulSoup(page.content(), "html.parser")
        fd, pd, ed = extract_dates_from_timeline(soup_js)
        filing_date = filing_date or fd
        publication_date = publication_date or pd
        expiration_date = expiration_date or ed

        if not description:
            desc_container_js = soup_js.find("patent-text", {"name": "description"})
            if desc_container_js:
                paragraphs = desc_container_js.find_all("div", class_="description-paragraph")
                description = "\n".join(p.get_text(" ", strip=True) for p in paragraphs if p.get_text(strip=True))

    patents.append({
        "url": url,
        "title": title,
        "inventors": inventors,
        "filing_date": filing_date,
        "publication_date": publication_date,
        "expiration_date": expiration_date,
        "description": description
    })

    time.sleep(random.uniform(0.5, 2))

if USE_PLAYWRIGHT:
    browser.close()
    playwright_context.stop()

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(patents, f, ensure_ascii=False, indent=2)

print(f"Scraped {len(patents)} patents → {OUT_FILE}")
