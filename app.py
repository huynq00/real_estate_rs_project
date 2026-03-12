# -*- coding: utf-8 -*-
"""
(Thành viên 5) Giao diện Streamlit chính: chạy từ thư mục real_estate_rs_project.
  streamlit run app.py
"""

import os
import sys
import csv
import json
import re

# Đảm bảo chạy từ thư mục project
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import textwrap

from knowledge_base.rules import apply_hard_filters, infer_user_segment, analyze_sales_gap
from src.llm_service import LLMService

st.set_page_config(page_title="Gợi ý BĐS", page_icon="🏠", layout="wide")

# Theme tổng thể: màu tối + điểm nhấn vàng/cam cho BĐS cao cấp
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top, #1f2933 0, #020617 55%, #000000 100%);
        color: #f9fafb;
        font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #030712 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.35);
    }
    section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        color: #fbbf24;
        text-shadow: 0 0 24px rgba(251, 191, 36, 0.4);
        margin-bottom: 0.1rem;
    }
    .main-subtitle {
        font-size: 0.9rem;
        color: #9ca3af;
        margin-bottom: 0.6rem;
    }
    div[data-baseweb="tab-list"] {
        border-bottom: 1px solid rgba(148, 163, 184, 0.4);
    }
    button[data-baseweb="tab"] {
        font-weight: 600;
        color: #d1d5db;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #facc15;
        border-bottom: 2px solid #facc15;
    }
    .stButton>button {
        border-radius: 999px;
        border: 1px solid rgba(249, 250, 251, 0.1);
        background: linear-gradient(135deg, #f97316, #ea580c);
        color: #f9fafb;
        font-weight: 600;
        padding: 0.32rem 1.1rem;
    }
    .stButton>button:hover {
        box-shadow: 0 0 18px rgba(248, 150, 69, 0.55);
        transform: translateY(-0.5px);
    }
    .stAlert {
        border-radius: 0.9rem;
        border: 1px solid rgba(148, 163, 184, 0.35);
    }

    /* Card gợi ý BĐS kiểu dashboard proptech */
    .re-card {
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.45);
        background: radial-gradient(circle at top left, rgba(55, 65, 81, 0.6), rgba(15, 23, 42, 0.96));
        padding: 14px 16px 12px 16px;
        margin-bottom: 12px;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.85);
        transition: all 0.18s ease-out;
    }
    .re-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 22px 50px rgba(248, 150, 69, 0.32);
        border-color: rgba(251, 191, 36, 0.55);
    }
    .re-card-rank {
        position: absolute;
        top: 10px;
        left: 14px;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #020617;
        border: 1px solid rgba(148, 163, 184, 0.8);
        color: #e5e7eb;
    }
    .re-card-rank-1 {
        background: linear-gradient(135deg, #fbbf24, #f97316);
        color: #0f172a;
        border-color: rgba(250, 204, 21, 0.9);
        box-shadow: 0 0 16px rgba(251, 191, 36, 0.6);
    }
    .re-score-bar {
        width: 100%;
        height: 7px;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.9);
        overflow: hidden;
    }
    .re-score-bar-inner {
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, #22c55e, #facc15);
    }
    .re-badge {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 11px;
        border: 1px solid rgba(148, 163, 184, 0.6);
        margin-right: 4px;
        margin-bottom: 4px;
        background: rgba(15, 23, 42, 0.85);
        color: #e5e7eb;
    }
    .re-badge--primary {
        border-color: rgba(52, 211, 153, 0.7);
        background: rgba(6, 78, 59, 0.45);
        color: #a7f3d0;
    }
    .re-badge--warning {
        border-color: rgba(251, 191, 36, 0.7);
        background: rgba(120, 53, 15, 0.6);
        color: #fed7aa;
    }
    .re-meta {
        font-size: 11px;
        color: #e5e7eb;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-right: 10px;
    }
    .re-meta svg {
        width: 14px;
        height: 14px;
        color: #9ca3af;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">🏠 Hệ thống gợi ý Bất động sản</div>'
    '<div class="main-subtitle">Phân tích khách hàng & tri thức hệ thống để đề xuất căn hộ tối ưu.</div>',
    unsafe_allow_html=True,
)

# Thứ tự tiện ích (trùng với recommender & rules)
FACILITY_ORDER = ["Hồ bơi", "Gym", "Công viên", "Trường học", "Bệnh viện", "Siêu thị"]


def _guess_project_name(title: str) -> str:
    """Ước lượng tên dự án từ title tin đăng (cắt theo '-', '–', '|')."""
    if not title:
        return ""
    t = str(title)
    for sep in [" - ", " – ", " | "]:
        if sep in t:
            t = t.split(sep)[0]
            break
    # Nếu có pattern '[Tên dự án]' ở đầu
    m = re.match(r"\[([^\]]+)\]", t)
    if m:
        return m.group(1).strip()
    return t.strip(" -–|")


@st.cache_resource
def get_llm_service():
    """
    Khởi tạo LLMService một lần cho toàn bộ phiên.
    Nếu thiếu GEMINI_API_KEY thì trả về None để UI xử lý graceful.
    """
    try:
        service = LLMService()
        # Thử khởi tạo nhẹ để phát hiện lỗi cấu hình sớm
        return service
    except Exception:
        return None


# Sidebar: pipeline (crawl/clean) và form nhu cầu thông minh
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
    st.header("Nhập nhu cầu khách hàng")
    user_budget = st.number_input(
        "Ngân sách (tỷ)",
        min_value=0.0,
        max_value=100.0,
        value=5.0,
        step=0.5,
        help="Chỉ hiển thị nhà có giá ≤ 120% ngân sách (luật lọc cứng)",
    )
    area_m2 = st.number_input(
        "Diện tích mong muốn (m²)",
        min_value=0.0,
        max_value=500.0,
        value=70.0,
        step=5.0,
        help="0 = bỏ qua, >0 sẽ dùng cho phân khúc & chấm điểm diện tích",
    )
    preferred_districts = st.multiselect(
        "Quận ưu tiên",
        [
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "Q5",
            "Q6",
            "Q7",
            "Q8",
            "Q9",
            "Q10",
            "Q11",
            "Q12",
            "BINHTHANH",
            "GOVAP",
            "THUDUC",
            "TANPHU",
            "TANBINH",
            "PHUNHUAN",
            "BINHTAN",
            "BINHCHANH",
            "NHABE",
        ],
        default=[],
    )
    preferred_facilities = st.multiselect(
        "Tiện ích ưu tiên",
        FACILITY_ORDER,
        default=[],
    )

    st.markdown("**Mức độ ưu tiên (1 = không quan trọng, 10 = rất quan trọng)**")
    w_price = st.slider("Ưu tiên Giá", 1, 10, 8)
    w_location = st.slider("Ưu tiên Vị trí", 1, 10, 7)
    w_area = st.slider("Ưu tiên Diện tích", 1, 10, 6)
    w_facility = st.slider("Ưu tiên Tiện ích", 1, 10, 5)
    w_legal = st.slider("Ưu tiên Pháp lý", 1, 10, 9)

    top_k = st.slider("Số tin gợi ý", 5, 30, 10)


# User profile cho rules (budget, area, facilities_vector)
facilities_vector = [1 if name in preferred_facilities else 0 for name in FACILITY_ORDER]
user_profile = {
    "budget": user_budget,
    "area_m2": area_m2,
    "facilities_vector": facilities_vector,
    "weights": {
        "price": w_price,
        "location": w_location,
        "area": w_area,
        "facility": w_facility,
        "legal": w_legal,
    },
}

# Phân khúc khách hàng (luật infer_user_segment)
segment = infer_user_segment(user_profile)
st.caption(f"Phân khúc khách hàng suy diễn: **{segment}**")


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
        r for r in rows if apply_hard_filters(user_budget, r.get("price_billions"))
    ]
    if len(rows_filtered) < len(rows):
        st.caption(f"Đã lọc bỏ {len(rows) - len(rows_filtered)} tin vượt quá 120% ngân sách.")
else:
    rows_filtered = rows

# Load KB cho sales advice & giải thích AI
kb_path = os.path.join(PROJECT_ROOT, "knowledge_base", "knowledge_base.json")
if os.path.exists(kb_path):
    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)
    facility_similarity = kb.get("facility_similarity", [])
    location_similarity = kb.get("location_similarity", {})
    legal_scores = kb.get("legal_priority_scores", {})
else:
    facility_similarity = []
    location_similarity = {}
    legal_scores = {}

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

# Gợi ý (Recommendation Engine)
try:
    from src.recommender import recommend

    # Chuyển budget/area thành khoảng để recommender sử dụng
    preferred_budget_range = [user_budget * 0.8, user_budget * 1.2] if user_budget > 0 else []
    preferred_area_range = [area_m2 * 0.8, area_m2 * 1.2] if area_m2 > 0 else []

    results = recommend(
        rows_filtered,
        preferred_districts=preferred_districts if preferred_districts else [],
        preferred_budget=preferred_budget_range,
        preferred_area_m2=preferred_area_range,
        preferred_facilities=preferred_facilities if preferred_facilities else [],
        top_k=top_k,
    )
except Exception as e:
    st.error(f"Lỗi recommender: {e}")
    results = rows_filtered[:top_k]
    for r in results:
        r["score"] = 0.0


# Tabs cho 3 module chính của Thành viên 5
tab_list, tab_compare, tab_sales = st.tabs(
    ["Danh sách gợi ý & giải thích", "So sánh 2 căn", "Góc trợ lý Sale"]
)

with tab_list:
    st.subheader(f"Top {len(results)} gợi ý cho bạn")

    llm_service = get_llm_service()
    if llm_service is None:
        st.warning("Không khởi tạo được LLM (Gemini). Chỉ hiển thị giải thích toán học, không có phần AI.")

    for i, r in enumerate(results, 1):
        score = float(r.get("score", 0) or 0)
        score_percent = max(0, min(100, int(score)))
        price = r.get("price_billions")
        area_val = r.get("area_m2")
        district = r.get("district_id") or "N/A"
        legal_type = r.get("legal_type") or "ĐANG_CẬP_NHẬT"
        raw_facilities = r.get("raw_facilities") or ""
        title = r.get("title", "") or ""
        project_name = _guess_project_name(title)

        # Box/card dùng container (tránh HTML bị render dưới dạng text)
        with st.container(border=True):
            # Hàng trên: rank + title + giá
            col_left, col_right = st.columns([3, 1.2])
            with col_left:
                rank_label = f"#{i} Ưu tiên"
                if i == 1:
                    st.markdown(f"**:orange[{rank_label}]**")
                else:
                    st.markdown(f"**{rank_label}**")
                # Header sạch: ưu tiên tên dự án + quận
                header_text = (
                    f"📍 {district} • {project_name}"
                    if project_name
                    else f"📍 {district}"
                )
                st.markdown(header_text)
            with col_right:
                st.markdown(
                    f"<div style='text-align:right; font-weight:600; color:#fbbf24;'>{price or 'N/A'} tỷ</div>"
                    f"<div style='text-align:right; font-size:11px; color:#9ca3af;'>Điểm: {score:.1f}</div>",
                    unsafe_allow_html=True,
                )

            # Progress bar điểm
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;font-size:11px;color:#9ca3af;'>"
                f"<span>Độ phù hợp tổng thể</span>"
                f"<span style='color:#6ee7b7;font-weight:600;'>{score_percent}%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.progress(score_percent / 100)

            # Meta: diện tích / PN / WC (demo PN/WC cố định)
            meta_cols = st.columns(3)
            meta_cols[0].markdown(
                f"**{area_val or 'N/A'} m²**\n\n<sub>Diện tích</sub>",
                unsafe_allow_html=True,
            )
            # Chưa có dữ liệu PN/WC trong CSV nên chỉ để nhãn trống (hoặc ẩn nếu muốn)
            meta_cols[1].markdown("**—**\n\n<sub>Phòng ngủ</sub>", unsafe_allow_html=True)
            meta_cols[2].markdown("**—**\n\n<sub>Phòng tắm</sub>", unsafe_allow_html=True)

            # Badges
            badges = [f"`{legal_type}`"]
            if raw_facilities:
                badges.append(f"`{raw_facilities}`")
            note = r.get("note", "")
            if note:
                badges.append(f"`Giải thích: {note[:40]}...`")
            if badges:
                st.markdown(" ".join(badges))

            # Tiện ích với icon (hiển thị dạng badge nhỏ)
            if raw_facilities:
                icon_map = {
                    "Hồ bơi": "🏊",
                    "Gym": "💪",
                    "Công viên": "🌳",
                    "Trường học": "🏫",
                    "Bệnh viện": "🏥",
                    "Siêu thị": "🛒",
                }
                facilities_list = [
                    f.strip() for f in raw_facilities.split(",") if f.strip()
                ]
                if facilities_list:
                    st.markdown(
                        "<div style='font-size:11px;color:#9ca3af;margin-top:4px;'>Tiện ích nổi bật:</div>",
                        unsafe_allow_html=True,
                    )
                    badge_html = ""
                    for fac in facilities_list:
                        icon = icon_map.get(fac, "•")
                        badge_html += (
                            f"<span style='display:inline-flex;align-items:center;gap:4px;"
                            f"padding:2px 8px;border-radius:999px;font-size:11px;"
                            f"background:rgba(15,23,42,0.9);border:1px solid rgba(148,163,184,0.7);"
                            f"color:#e5e7eb;margin-right:4px;margin-top:4px;'>"
                            f"<span>{icon}</span><span>{fac}</span></span>"
                        )
                    st.markdown(badge_html, unsafe_allow_html=True)

            # Nút hành động & chi tiết
            btn_cols = st.columns([1, 1.3])

            # Giải thích bằng AI (nút nằm ngay trong box) – đổi label thân thiện
            if llm_service is not None and btn_cols[0].button(
                "💡 Vì sao căn này phù hợp?", key=f"ai_explain_{i}"
            ):
                user_profile_text = (
                    f"Ngân sách ~{user_budget} tỷ, diện tích mong muốn ~{area_m2} m², "
                    f"ưu tiên quận: {preferred_districts}, tiện ích: {preferred_facilities}."
                )
                house_text = (
                    f"Tiêu đề: {r.get('title')}, giá: {price} tỷ, diện tích: {area_val} m², "
                    f"quận: {district}, pháp lý: {legal_type}, tiện ích: {raw_facilities}."
                )
                price_analysis = (
                    f"Căn này có giá {price} tỷ so với ngân sách {user_budget} tỷ."
                )
                facility_vec = _parse_vector_facilities(r.get("vector_facilities"))
                facility_analysis = (
                    f"Vector tiện ích căn hộ: {facility_vec} theo thứ tự {FACILITY_ORDER}."
                )
                similarity_knowledge = (
                    "Hệ thống dùng ma trận tương đồng tiện ích & vị trí để đánh giá mức độ "
                    "thay thế giữa các quận và tiện ích, kết hợp ưu tiên pháp lý."
                )
                explain = llm_service.generate_explanation(
                    user_profile=user_profile_text,
                    house_data=house_text,
                    match_score=score,
                    price_analysis=price_analysis,
                    facility_analysis=facility_analysis,
                    similarity_knowledge=similarity_knowledge,
                )
                st.markdown("**Lời giải thích từ AI:**")
                st.write(explain)

            # Xem chi tiết: dùng expander trong box
            with btn_cols[1].expander("Xem chi tiết căn hộ"):
                # Tóm tắt gọn thay cho đoạn marketing dài
                summary_lines = []
                if area_val:
                    summary_lines.append(f"📐 {area_val} m²")
                # Chưa có dữ liệu PN/WC/garden nên bỏ qua nếu không có
                if project_name:
                    summary_lines.append(f"🏢 Dự án: {project_name}")
                if district:
                    summary_lines.append(f"📍 Quận: {district}")

                if summary_lines:
                    st.markdown("**Thông tin tóm tắt:**")
                    st.markdown("\n".join(summary_lines))

                st.markdown(f"**Pháp lý:** `{legal_type}`")

                # Mô tả chi tiết gốc trong collapsible con
                full_desc = (r.get("full_desc") or "").strip()
                if full_desc:
                    with st.expander("Xem mô tả chi tiết"):
                        st.write(full_desc)
                else:
                    st.caption("Không có mô tả chi tiết cho căn này.")

with tab_compare:
    st.subheader("So sánh 2 căn hộ để ra quyết định")
    if not results:
        st.info("Chưa có kết quả để so sánh.")
    else:
        titles = [f"#{i+1} - {r.get('title', 'N/A')}" for i, r in enumerate(results)]
        col_a, col_b = st.columns(2)
        with col_a:
            idx_a = st.selectbox("Chọn Căn A", list(range(len(titles))), format_func=lambda i: titles[i])
        with col_b:
            idx_b = st.selectbox("Chọn Căn B", list(range(len(titles))), index=min(1, len(titles) - 1), format_func=lambda i: titles[i])

        llm_service = get_llm_service()
        if llm_service is None:
            st.warning("Không khởi tạo được LLM (Gemini). Chỉ hiển thị so sánh cơ bản dựa trên điểm & giá.")

        if st.button("Phân tích so sánh"):
            house_a = results[idx_a]
            house_b = results[idx_b]
            if llm_service is None:
                st.write(
                    f"- Căn A: giá {house_a.get('price_billions')} tỷ, điểm {house_a.get('score', 0):.2f}, pháp lý {house_a.get('legal_type')}."
                )
                st.write(
                    f"- Căn B: giá {house_b.get('price_billions')} tỷ, điểm {house_b.get('score', 0):.2f}, pháp lý {house_b.get('legal_type')}."
                )
            else:
                user_profile_text = (
                    f"Ngân sách khoảng {user_budget} tỷ, diện tích mong muốn khoảng {area_m2} m², "
                    f"phân khúc suy diễn: {segment}. Quận ưu tiên: {', '.join(preferred_districts) or 'không cố định'}."
                )

                def _summarize_house(h: dict) -> str:
                    """Chuẩn hóa dữ liệu 1 căn hộ cho prompt (ngắn gọn nhưng đủ ý)."""
                    return (
                        f"Tiêu đề: {h.get('title', 'N/A')}. "
                        f"Giá: {h.get('price_billions', 'N/A')} tỷ. "
                        f"Diện tích: {h.get('area_m2', 'N/A')} m². "
                        f"Quận: {h.get('district_id', 'N/A')}. "
                        f"Pháp lý: {h.get('legal_type', 'N/A')}. "
                        f"Tiện ích chính: {h.get('raw_facilities', 'không rõ')}. "
                        f"Điểm phù hợp tổng hợp: {h.get('score', 0):.2f}."
                    )

                house_a_text = _summarize_house(house_a)
                house_b_text = _summarize_house(house_b)

                system_rules_text = (
                    "Hệ thống đánh giá căn hộ dựa trên 5 nhóm tiêu chí: Giá, Vị trí (quận và độ tương đồng khu vực), "
                    "Diện tích, Tiện ích (ma trận tương đồng tiện ích) và Pháp lý (ưu tiên: SỔ HỒNG > HĐMB > ĐANG CẬP NHẬT). "
                    "Điểm càng cao chứng tỏ căn hộ càng phù hợp với hồ sơ khách hàng."
                )

                compare_text = llm_service.generate_comparison(
                    user_profile=user_profile_text,
                    house_a_data=house_a_text,
                    house_b_data=house_b_text,
                    system_rules=system_rules_text,
                )
                st.markdown("**Phân tích từ AI:**")
                st.write(compare_text)

with tab_sales:
    st.subheader("Góc trợ lý Sale (Gap Analysis)")
    st.caption(
        "Dùng cho môi giới: xem nhanh các gợi ý chênh ngân sách/pháp lý/tiện ích để chuẩn bị kịch bản tư vấn."
    )

    if not results:
        st.info("Chưa có kết quả để phân tích.")
    else:
        llm_service = get_llm_service()
        for i, r in enumerate(results, 1):
            score = r.get("score", 0)
            house_data = {
                "price_billions": float(r.get("price_billions") or 0),
                "legal_type": r.get("legal_type") or "",
                "vector_facilities": _parse_vector_facilities(r.get("vector_facilities")),
            }
            advices = analyze_sales_gap(
                user_profile,
                house_data,
                match_score=score,
                facility_similarity=facility_similarity,
            )
            if not advices:
                continue

            with st.expander(f"Căn #{i}: {r.get('title', 'N/A')} — Điểm: {score:.2f}"):
                st.write(
                    f"**Giá:** {r.get('price_billions')} tỷ | **Diện tích:** {r.get('area_m2')} m² | **Quận:** {r.get('district_id')} | **Pháp lý:** {r.get('legal_type')}"
                )
                st.markdown("**Gợi ý cho Sale (từ luật hệ chuyên gia):**")
                for a in advices:
                    st.markdown(f"- {a}")

                if llm_service is not None and st.button(
                    f"Xin kịch bản nói chuyện mẫu từ AI cho căn #{i}", key=f"ai_sale_{i}"
                ):
                    gap_reason = "; ".join(advices)
                    house_text = (
                        f"Tiêu đề: {r.get('title')}, giá: {r.get('price_billions')} tỷ, diện tích: {r.get('area_m2')} m², "
                        f"quận: {r.get('district_id')}, pháp lý: {r.get('legal_type')}."
                    )
                    script = llm_service.generate_sales_script(
                        house_data=house_text, gap_reason=gap_reason
                    )
                    st.markdown("**Kịch bản gợi ý từ AI:**")
                    st.write(script)
