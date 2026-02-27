# -*- coding: utf-8 -*-
"""
(Thành viên 5) Giao diện Streamlit chính: chạy từ thư mục real_estate_rs_project.
  streamlit run app.py
"""

import os
import sys
import csv
import json

# Đảm bảo chạy từ thư mục project
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

st.set_page_config(page_title="Gợi ý BĐS", page_icon="🏠", layout="wide")
st.title("🏠 Hệ thống gợi ý Bất động sản")

# Thứ tự tiện ích (trùng với recommender & rules)
FACILITY_ORDER = ["Hồ bơi", "Gym", "Công viên", "Trường học", "Bệnh viện", "Siêu thị"]

# Sidebar: pipeline (crawl/clean) và lọc & gợi ý
with st.sidebar:
    st.header("Data Pipeline")
    if st.button("Chạy Clean (từ raw → processed)"):
        try:
            from src.data_pipeline import run_clean
            import config
            out = run_clean()
            st.success(f"Đã tạo: {out}")
        except Exception as e:
            st.error(str(e))
    st.markdown("---")
    st.header("Lọc & Gợi ý")
    user_budget = st.number_input(
        "Ngân sách (tỷ)",
        min_value=0.0,
        max_value=100.0,
        value=5.0,
        step=0.5,
        help="Chỉ hiển thị nhà có giá ≤ 120% ngân sách (luật lọc cứng)",
    )
    area_m2 = st.number_input(
        "Diện tích cần (m²)",
        min_value=0.0,
        max_value=500.0,
        value=0.0,
        step=5.0,
        help="Dùng cho phân khúc khách hàng (0 = bỏ qua)",
    )
    preferred_districts = st.multiselect(
        "Quận ưu tiên",
        ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10", "Q11", "Q12",
         "BINHTHANH", "GOVAP", "THUDUC", "TANPHU", "TANBINH", "PHUNHUAN", "BINHTAN", "BINHCHANH", "NHABE"],
        default=[],
    )
    preferred_facilities = st.multiselect(
        "Tiện ích ưu tiên",
        FACILITY_ORDER,
        default=[],
    )
    top_k = st.slider("Số tin gợi ý", 5, 30, 10)

# User profile cho rules (budget, area, facilities_vector)
facilities_vector = [1 if name in preferred_facilities else 0 for name in FACILITY_ORDER]
user_profile = {
    "budget": user_budget,
    "area_m2": area_m2,
    "facilities_vector": facilities_vector,
}

# Phân khúc khách hàng (luật infer_user_segment)
from knowledge_base.rules import apply_hard_filters, infer_user_segment, analyze_sales_gap

segment = infer_user_segment(user_profile)
st.caption(f"Phân khúc: **{segment}**")

# Đọc data đã xử lý
import config
final_csv = config.FINAL_CSV
if not os.path.exists(final_csv):
    st.warning(f"Chưa có file {final_csv}. Chạy pipeline (crawl + clean) trước.")
    st.stop()

rows = []
with open(final_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(dict(r))

if not rows:
    st.info("Không có bản ghi nào trong file final.")
    st.stop()

# Luật lọc cứng theo ngân sách (chỉ áp dụng khi user nhập budget > 0)
if user_budget and float(user_budget) > 0:
    rows_filtered = [
        r for r in rows
        if apply_hard_filters(user_budget, r.get("price_billions"))
    ]
    if len(rows_filtered) < len(rows):
        st.caption(f"Đã lọc bỏ {len(rows) - len(rows_filtered)} tin vượt quá 120% ngân sách.")
else:
    rows_filtered = rows

# Load KB cho sales advice (facility_similarity)
kb_path = os.path.join(PROJECT_ROOT, "knowledge_base", "knowledge_base.json")
if os.path.exists(kb_path):
    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)
    facility_similarity = kb.get("facility_similarity", [])
else:
    facility_similarity = []

# Parse vector tiện ích (từ CSV string/list)
try:
    from src.recommender import _parse_vector_facilities
except ImportError:
    def _parse_vector_facilities(v):
        if isinstance(v, list):
            return [int(x) for x in v][:6]
        if isinstance(v, str) and v.strip().startswith("["):
            s = v.strip()[1:-1]
            return [int(x.strip()) for x in s.split(",") if x.strip().isdigit()][:6]
        return [0] * 6

# Gợi ý
try:
    from src.recommender import recommend
    results = recommend(
        rows_filtered,
        preferred_districts=preferred_districts if preferred_districts else None,
        preferred_facilities=preferred_facilities if preferred_facilities else None,
        top_k=top_k,
    )
except Exception as e:
    st.error(f"Lỗi recommender: {e}")
    results = rows_filtered[:top_k]
    for r in results:
        r["score"] = 0.0

st.subheader(f"Top {len(results)} gợi ý")
for i, r in enumerate(results, 1):
    score = r.get("score", 0)
    with st.expander(f"#{i} {r.get('title', 'N/A')} — Điểm: {score:.2f}"):
        st.write(f"**Giá:** {r.get('price_billions')} tỷ | **Diện tích:** {r.get('area_m2')} m² | **Quận:** {r.get('district_id')}")
        st.write(f"**Pháp lý:** {r.get('legal_type')} | **Tiện ích:** {r.get('raw_facilities')}")
        if r.get("full_desc"):
            st.caption(r.get("full_desc", "")[:500] + "…")
        # Gợi ý Sale (luật analyze_sales_gap)
        try:
            house_data = {
                "price_billions": float(r.get("price_billions") or 0),
                "legal_type": r.get("legal_type") or "",
                "vector_facilities": _parse_vector_facilities(r.get("vector_facilities")),
            }
            advices = analyze_sales_gap(
                user_profile, house_data,
                match_score=score,
                facility_similarity=facility_similarity,
            )
            if advices:
                st.markdown("**Gợi ý cho Sale:**")
                for a in advices:
                    st.markdown(f"- {a}")
        except Exception:
            pass
