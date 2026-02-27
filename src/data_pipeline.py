# -*- coding: utf-8 -*-
"""
(Thành viên 2) Pipeline: Crawl batdongsan.com.vn (Playwright) + Clean data.
Xuất raw CSV vào data/raw/, final CSV vào data/processed/real_estate_data_final.csv
"""

import csv
import re
import time
import random
from difflib import SequenceMatcher
from typing import List, Tuple, Optional
from urllib.parse import urljoin

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# --- Crawl (Playwright) ---
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    sync_playwright = None
    PlaywrightTimeout = Exception


def _random_delay(min_sec=1.5, max_sec=4.0):
    time.sleep(random.uniform(min_sec, max_sec))


def _extract_id_from_url(url: str) -> Optional[str]:
    m = re.search(r"-pr(\d+)(?:\?|$|/)", url)
    return f"pr{m.group(1)}" if m else None


def _normalize_text(s: str) -> str:
    if not s:
        return ""
    return " ".join(s.split()).strip()


def launch_browser(headless: bool = False):
    if sync_playwright is None:
        raise ImportError("Cài đặt: pip install playwright && python -m playwright install chromium")
    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="vi-VN",
        timezone_id="Asia/Ho_Chi_Minh",
    )
    context.set_extra_http_headers({"Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"})
    return p, browser, context


def get_listing_links_from_page(page, keyword: str, max_links: int) -> list:
    seen = set()
    links = []
    locator = page.locator('a[href*="-pr"][href*="ban-can-ho-chung-cu"]')
    n = min(locator.count(), 60)
    for i in range(n):
        try:
            a = locator.nth(i)
            href = a.get_attribute("href")
            if not href:
                continue
            full_url = urljoin(config.BASE_URL, href.split("?")[0])
            if full_url in seen:
                continue
            seen.add(full_url)
            links.append(full_url)
            if len(links) >= max_links:
                break
        except Exception:
            continue
    return links


def extract_detail(page, url: str) -> Optional[dict]:
    for attempt in range(2):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            _random_delay(1.5, 3)
            break
        except (PlaywrightTimeout, Exception):
            if attempt == 1:
                return None
            _random_delay(3, 6)

    row = {
        "id": _extract_id_from_url(url) or "",
        "title": "",
        "price_billions": None,
        "area_m2": None,
        "district_raw": "",
        "legal_raw": "",
        "full_desc": "",
        "url": url,
    }
    try:
        h1 = page.locator("h1").first
        if h1.count():
            row["title"] = _normalize_text(h1.inner_text())
    except Exception:
        pass
    if not row["title"]:
        try:
            t = page.locator('[class*="title"], [data-id="title"]').first
            if t.count():
                row["title"] = _normalize_text(t.inner_text())
        except Exception:
            pass
    try:
        body = page.locator("body").inner_text()
        price_match = re.search(r"([\d,\.]+)\s*(tỷ|tỉ|ty|triệu|tr/m²)", body, re.I)
        if price_match:
            val = price_match.group(1).replace(",", ".")
            unit = price_match.group(2).lower()
            if "tỷ" in unit or "tỉ" in unit or "ty" in unit:
                row["price_billions"] = float(re.sub(r"[^\d.]", "", val) or "0")
            elif "triệu" in unit or "tr" in unit:
                row["price_billions"] = float(re.sub(r"[^\d.]", "", val) or "0") / 1000.0
    except Exception:
        pass
    try:
        area_match = re.search(r"([\d,\.]+)\s*m²|diện tích[:\s]*([\d,\.]+)", page.content(), re.I)
        if area_match:
            a = (area_match.group(1) or area_match.group(2) or "").replace(",", ".")
            if a:
                row["area_m2"] = float(a)
    except Exception:
        pass
    try:
        body = page.locator("body").inner_text()
        for part in ["Quận 1", "Quận 2", "Quận 3", "Quận 4", "Quận 5", "Quận 6", "Quận 7", "Quận 8", "Quận 9", "Quận 10", "Quận 11", "Quận 12",
                     "Bình Thạnh", "Gò Vấp", "Bình Chánh", "Thủ Đức", "Tân Phú", "Tân Bình", "Phú Nhuận", "Bình Tân", "Nhà Bè", "Hồ Chí Minh"]:
            if part in body:
                for line in body.split("\n"):
                    line = line.strip()
                    if part in line and len(line) < 120:
                        row["district_raw"] = _normalize_text(line)
                        break
                if row["district_raw"]:
                    break
    except Exception:
        pass
    try:
        desc_sel = page.locator('[class*="description"], [class*="detail-content"], [class*="content-detail"], article, .detail__body')
        for i in range(desc_sel.count()):
            el = desc_sel.nth(i)
            text = _normalize_text(el.inner_text())
            if len(text) > 100 and ("pháp lý" in text or "diện tích" in text or "tiện ích" in text or "mô tả" in text):
                row["full_desc"] = text[:8000]
                break
        if not row["full_desc"]:
            main = page.locator("main, [role=main], #main, .main-content, .product-detail").first
            if main.count():
                row["full_desc"] = _normalize_text(main.inner_text())[:8000]
    except Exception:
        pass
    if not row["id"]:
        row["id"] = f"crawl_{hash(url) % 10**8}"
    return row


def crawl_all(
    output_raw_csv: str = None,
    max_per_keyword: int = 25,
    max_detail_pages: int = 250,
    headless: bool = False,
) -> str:
    """Crawl batdongsan.com.vn, lưu raw CSV. Trả về đường dẫn file."""
    output_raw_csv = output_raw_csv or config.RAW_CSV
    os.makedirs(os.path.dirname(output_raw_csv), exist_ok=True)
    p, browser = None, None
    all_rows = []
    seen_ids = set()
    try:
        p, browser, context = launch_browser(headless=headless)
        page = context.new_page()
        page.goto(config.LISTING_URL_TPHCM, wait_until="domcontentloaded", timeout=45000)
        _random_delay(2, 4)
        seen_urls = set()
        unique_links = []
        max_pages = max(15, (max_detail_pages // 20) + 2)
        for page_no in range(1, max_pages + 1):
            if len(unique_links) >= max_detail_pages:
                break
            url_page = config.LISTING_URL_TPHCM if page_no == 1 else config.LISTING_URL_TPHCM.rstrip("/") + "/p" + str(page_no)
            try:
                page.goto(url_page, wait_until="domcontentloaded", timeout=25000)
                _random_delay(2, 4)
            except PlaywrightTimeout:
                continue
            need = max_detail_pages - len(unique_links)
            links = get_listing_links_from_page(page, "", min(need, 25))
            for link in links:
                if link not in seen_urls:
                    seen_urls.add(link)
                    unique_links.append(link)
                    if len(unique_links) >= max_detail_pages:
                        break
            _random_delay(2, 4)
        fieldnames = ["id", "title", "price_billions", "area_m2", "district_raw", "legal_raw", "full_desc", "url"]
        with open(output_raw_csv, "w", newline="", encoding="utf-8") as csvfile:
            w = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            csvfile.flush()
            for url in unique_links:
                rid = _extract_id_from_url(url)
                if rid and rid in seen_ids:
                    continue
                row = extract_detail(page, url)
                if row and row.get("title"):
                    if row["id"]:
                        seen_ids.add(row["id"])
                    all_rows.append(row)
                    w.writerow({k: (row.get(k) if row.get(k) is not None else "") for k in fieldnames})
                    csvfile.flush()
                _random_delay(1.5, 4)
    finally:
        if browser:
            browser.close()
        if p:
            p.stop()
    return output_raw_csv


# --- Clean & chuẩn hóa ---
def normalize_legal(desc: str) -> str:
    if not desc:
        return ""
    d = (desc or "").lower()
    for legal, keywords in config.LEGAL_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in d:
                return legal
    return ""


def normalize_district(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.lower().strip()
    for pattern, code in config.DISTRICT_MAPPING.items():
        if pattern in raw:
            return code
    m = re.search(r"quận\s*(\d+)|q\.?\s*(\d+)", raw, re.I)
    if m:
        num = m.group(1) or m.group(2)
        return f"Q{num}"
    return ""


def build_facility_vector(desc: str) -> Tuple[List[int], List[str]]:
    vec = [0] * 6
    found = []
    names = ["Hồ bơi", "Gym", "Công viên", "Trường học", "Bệnh viện", "Siêu thị"]
    if not desc:
        return vec, []
    d = desc.lower()
    for i, keywords in enumerate(config.FACILITY_KEYWORDS):
        for kw in keywords:
            if kw.lower() in d:
                vec[i] = 1
                found.append(names[i])
                break
    return vec, list(dict.fromkeys(found))


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def clean_and_dedupe(rows: list) -> list:
    filtered = []
    for r in rows:
        price = r.get("price_billions")
        if price is not None and price != "":
            try:
                if float(price) < config.MIN_PRICE_BILLIONS:
                    continue
            except (TypeError, ValueError):
                pass
        area = r.get("area_m2")
        if area is not None and area != "":
            try:
                if float(area) < config.MIN_AREA_M2:
                    continue
            except (TypeError, ValueError):
                pass
        filtered.append(r)
    kept = []
    for r in filtered:
        title = (r.get("title") or "").strip()
        is_dup = False
        for k in kept:
            if _similarity(title, (k.get("title") or "").strip()) >= config.SIMILARITY_THRESHOLD:
                is_dup = True
                break
        if not is_dup:
            kept.append(r)
    return kept


def run_clean(
    input_csv: str = None,
    output_csv: str = None,
) -> str:
    """Đọc raw CSV, chuẩn hóa, lọc, de-dup, ghi final CSV. Trả về đường dẫn file."""
    input_csv = input_csv or config.RAW_CSV
    output_csv = output_csv or config.FINAL_CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    rows = []
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(dict(r))
    if not rows:
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            f.write("id,title,price_billions,area_m2,district_id,legal_type,raw_facilities,vector_facilities,full_desc\n")
        return output_csv
    for r in rows:
        desc = r.get("full_desc") or ""
        r["legal_type"] = normalize_legal(desc)
        r["district_id"] = normalize_district(r.get("district_raw") or "")
        vec, raw_fac = build_facility_vector(desc)
        r["vector_facilities"] = vec
        r["raw_facilities"] = ", ".join(raw_fac) if raw_fac else ""
    rows = clean_and_dedupe(rows)
    out_fields = [
        "id", "title", "price_billions", "area_m2", "district_id", "legal_type",
        "raw_facilities", "vector_facilities", "full_desc",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row_out = {k: r.get(k, "") for k in out_fields}
            if isinstance(row_out.get("vector_facilities"), list):
                row_out["vector_facilities"] = "[" + ",".join(map(str, row_out["vector_facilities"])) + "]"
            w.writerow(row_out)
    return output_csv


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crawl + Clean BĐS căn hộ chung cư TP.HCM")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--max", type=int, default=200)
    parser.add_argument("--crawl-only", action="store_true")
    parser.add_argument("--clean-only", action="store_true")
    args = parser.parse_args()
    if args.clean_only:
        run_clean()
        print(f"Đã tạo {config.FINAL_CSV}")
    else:
        crawl_all(max_detail_pages=args.max, headless=args.headless)
        print(f"Raw: {config.RAW_CSV}")
        if not args.crawl_only:
            run_clean()
            print(f"Final: {config.FINAL_CSV}")
