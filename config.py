# -*- coding: utf-8 -*-
"""Cấu hình crawl và chuẩn hóa (đường dẫn data, từ khóa, ngưỡng)."""

import os

# Thư mục gốc project (nơi chứa config.py)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- URL & Crawl ---
BASE_URL = "https://batdongsan.com.vn"
LISTING_URL_TPHCM = "https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-hcm"

PROJECT_KEYWORDS = [
    ("Masteri Thảo Điền", 15),
    ("The Estella", 15),
    ("Vinhomes Central Park", 20),
    ("Sunrise City", 15),
    ("Eco Green", 15),
    ("Vinhomes Grand Park", 15),
    ("Safira Khang Điền", 15),
    ("Cityland Park Hills", 15),
    ("Ehome", 15),
    ("Mizuki Park", 15),
    ("Lovera Park", 15),
    ("Gold View", 15),
    ("Millennium", 15),
]

# --- Chuẩn hóa Pháp lý ---
LEGAL_KEYWORDS = {
    "SOHONG": ["sổ hồng", "so hong", "sổ đỏ", "so do", "sổ riêng", "đã có sổ"],
    "HDMB": ["hợp đồng mua bán", "hđmb", "hdmb", "hợp đồng MB"],
    "VIBANG": ["vi bằng", "giấy tay"],
}

# --- Chuẩn hóa Quận (district_id) ---
DISTRICT_MAPPING = {
    "quận 1": "Q1", "q.1": "Q1", "q1": "Q1",
    "quận 2": "Q2", "q.2": "Q2", "q2": "Q2", "thành phố thủ đức (khu q2)": "Q2",
    "quận 3": "Q3", "q.3": "Q3", "q3": "Q3",
    "quận 4": "Q4", "q.4": "Q4", "q4": "Q4",
    "quận 5": "Q5", "q.5": "Q5", "q5": "Q5",
    "quận 6": "Q6", "q.6": "Q6", "q6": "Q6",
    "quận 7": "Q7", "q.7": "Q7", "q7": "Q7",
    "quận 8": "Q8", "q.8": "Q8", "q8": "Q8",
    "quận 9": "Q9", "q.9": "Q9", "q9": "Q9",
    "quận 10": "Q10", "q.10": "Q10", "q10": "Q10",
    "quận 11": "Q11", "q.11": "Q11", "q11": "Q11",
    "quận 12": "Q12", "q.12": "Q12", "q12": "Q12",
    "bình thạnh": "BINHTHANH", "quận bình thạnh": "BINHTHANH",
    "gò vấp": "GOVAP", "quận gò vấp": "GOVAP",
    "bình chánh": "BINHCHANH", "huyện bình chánh": "BINHCHANH",
    "thủ đức": "THUDUC", "tp. thủ đức": "THUDUC",
    "tân phú": "TANPHU", "quận tân phú": "TANPHU",
    "tân bình": "TANBINH", "quận tân bình": "TANBINH",
    "phú nhuận": "PHUNHUAN", "quận phú nhuận": "PHUNHUAN",
    "bình tân": "BINHTAN", "quận bình tân": "BINHTAN",
    "nhà bè": "NHABE", "huyện nhà bè": "NHABE",
}

# --- Vector tiện ích: [Hồ bơi, Gym, Công viên, Trường học, Bệnh viện, Siêu thị] ---
FACILITY_KEYWORDS = [
    ["hồ bơi", "bể bơi", "swimming pool", "hồ vô cực"],
    ["gym", "phòng tập", "fitness", "yoga"],
    ["công viên", "cây xanh", "mảng xanh", "vườn", "cảnh quan", "kênh đào"],
    ["trường học", "cấp 1", "cấp 2", "tiểu học", "mầm non", "đại học", "nhà trẻ"],
    ["bệnh viện", "phòng khám", "trạm y tế", "nhà thuốc"],
    ["siêu thị", "chợ", "vinmart", "coopmart", "bách hóa xanh", "lotte", "mart"],
]

# --- Lọc tin ảo ---
MIN_PRICE_BILLIONS = 1.0
MIN_AREA_M2 = 20.0
SIMILARITY_THRESHOLD = 0.90

# --- Đường dẫn data (trong real_estate_rs_project) ---
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_CSV = os.path.join(DATA_DIR, "raw", "real_estate_data_raw.csv")
FINAL_CSV = os.path.join(DATA_DIR, "processed", "real_estate_data_final.csv")
