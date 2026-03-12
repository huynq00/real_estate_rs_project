# -*- coding: utf-8 -*-
"""
(Thành viên 3) Thuật toán gợi ý: tính điểm, Cosine Similarity.
Sử dụng knowledge_base (ma trận tương đồng vị trí, tiện ích).
"""

import json
import os
from typing import List, Dict, Any, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Vector facilities: [Hồ bơi, Gym, Công viên, Trường học, Bệnh viện, Siêu thị]
FACILITY_ORDER = ["Hồ bơi", "Gym", "Công viên", "Trường học", "Bệnh viện", "Siêu thị"]


def _load_knowledge_base() -> Dict:
    kb_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "knowledge_base", "knowledge_base.json"
    )
    if not os.path.exists(kb_path):
        return {
            "location_similarity": {},
            "facility_order": FACILITY_ORDER,
            "facility_similarity": [],
            "legal_priority_scores": {},
        }
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_vector_facilities(vec_str: Any) -> List[int]:
    """Chuyển 'vector_facilities' từ string '[0,1,0,1,0,1]' hoặc list thành list int."""
    if isinstance(vec_str, list):
        return [int(x) for x in vec_str]
    if isinstance(vec_str, str):
        s = vec_str.strip()
        if s.startswith("["):
            s = s[1:-1]
        return [int(x.strip()) for x in s.split(",") if x.strip().isdigit()]
    return [0] * 6


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity giữa hai vector (cùng độ dài)."""
    if len(a) != len(b) or len(a) == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def location_score(district_id: str, preferred_districts: List[str], kb: Dict) -> dict:
    """
    Điểm vị trí theo ma trận location_similarity (0.0–1.0).
    Trùng quận ưu tiên = 1.0; quận khác lấy điểm tương đồng từ KB (max theo từng quận ưu tiên).
    """
    if preferred_districts == []:
        return {"fit" : 1.0, "note" : "vị trí bất động sản không quan trọng, "}
    
    if not district_id:
        return {"fit" : 0.0, "note" : "Bất động sản không có dữ liệu vị trí, "}
    
    district_id = district_id.strip().upper()
    prefs_upper = [d.strip().upper() for d in preferred_districts]
    if district_id in prefs_upper:
        return {"fit" : 1.0, "note" : f"Bất động sản ở {district_id} như bạn mong muốn, "}
    sim = kb.get("location_similarity") or {}
    best = 0.0
    for pref in prefs_upper:
        row = sim.get(pref)
        best = max(best, float(row.get(district_id, 0.0)))
        
    return {"fit" : best, "note" : f"Bất động sản ở {district_id} bạn có thể cân nhắc, "}

def budget_score(price: float, preferred_budget: List[float]) -> dict:
    """
    Tính độ phù hợp về Giá.
    - preferred_budget: [min, max] theo đơn vị tỷ.
    - Tự động chuyển 'price' từ string -> float nếu cần.
    """
    if not preferred_budget:
        return {"fit": 1.0, "note": "Bất động sản giá không quan trọng, "}

    try:
        price_val = float(price)
    except (TypeError, ValueError):
        return {"fit": 0.0, "note": "Bất động sản không có dữ liệu giá, "}

    prefs_value = [float(min(preferred_budget)), float(max(preferred_budget))]

    if prefs_value[1] <= 0:
        return {"fit": 1.0, "note": "Khoảng ngân sách không hợp lệ, bỏ qua tiêu chí giá, "}

    if prefs_value[0] <= price_val <= prefs_value[1]:
        return {"fit": 1.0, "note": "Bất động sản có giá như bạn mong muốn, "}
    elif price_val < prefs_value[0]:
        return {
            "fit": max(0.0, price_val / prefs_value[0]),
            "note": "Bất động sản có giá rẻ hơn bạn mong muốn, ",
        }
    else:
        over = (price_val - prefs_value[1]) / prefs_value[1]
        return {
            "fit": max(0.0, 1.0 - over),
            "note": "Bất động sản có giá đắt hơn bạn mong muốn, ",
        }


def area_m2_score(area_m2: float, preferred_area_m2: List[float]) -> dict:
    """
    Tính độ phù hợp về Diện tích.
    - preferred_area_m2: [min, max] theo m².
    - Tự động chuyển 'area_m2' từ string -> float nếu cần.
    """
    if not preferred_area_m2:
        return {"fit": 1.0, "note": "Bất động sản diện tích không quan trọng, "}

    try:
        area_val = float(area_m2)
    except (TypeError, ValueError):
        return {"fit": 0.0, "note": "Bất động sản không có dữ liệu diện tích, "}

    prefs_value = [float(min(preferred_area_m2)), float(max(preferred_area_m2))]

    if prefs_value[1] <= 0:
        return {"fit": 1.0, "note": "Khoảng diện tích không hợp lệ, bỏ qua tiêu chí diện tích, "}

    if prefs_value[0] <= area_val <= prefs_value[1]:
        return {"fit": 1.0, "note": "Bất động sản có diện tích như bạn mong muốn, "}
    elif area_val < prefs_value[0]:
        return {
            "fit": max(0.0, area_val / prefs_value[0]),
            "note": "Bất động sản có diện tích nhỏ hơn bạn mong muốn, ",
        }
    else:
        over = (area_val - prefs_value[1]) / prefs_value[1]
        return {
            "fit": max(0.0, 1.0 - over),
            "note": "Bất động sản có diện tích lớn hơn bạn mong muốn, ",
        }

def facility_score(facilities_vector: list, preferred_facilities: List[str], kb: Dict) -> dict:
    score = 0.0
    note = ""
    note1 = ""
    note2 = ""

    facility_key_list = kb.get("facility_order")
    # facility_index_mapping = kb.get("facility_index_mapping")

    for index in range(6):
        key = facility_key_list[index]

        if facilities_vector[index]:
            note1 += f"{key}, "
            score += 3.3
        else:
            if key in preferred_facilities:
                note2 += f"{key}, "
                score -= 3.3

    if note1 != "":
        note += f"Gần bất động sản có những tiện ích: {note1}"

    if note2 != "":
        note += f"Gần bất động sản thiếu những tiện ích: {note2}"
    
    return {"score" : score, "note" : note}

def legal_score(legal_type: str, kb: Dict) -> dict:
    """
    Điểm pháp lý theo legal_priority_scores (0.0–1.0). Không có trong KB thì 0.5.
    """
    if not (legal_type or "").strip():
        return {"fit" : 0.3, "note" : f"Loại sổ cấp: DANG_CAP_NHAT, "}
    scores = kb.get("legal_priority_scores") or {}
    key = (legal_type or "").strip().upper()

    return {"fit" : float(scores.get(key, 0.5)), "note" : f"Loại sổ cấp: {key}, "}


def score_on_fit(fit: float) -> float:
    return 20 * ((fit - 0.3) / 0.7)

def score_property(
    row: Dict,
    preferred_districts: Optional[List[str]] = None,
    preferred_budget: Optional[List] = None,
    preferred_area_m2: Optional[List] = None,
    preferred_facilities: Optional[List[str]] = None,
) -> dict:
    """
    Tổng hợp điểm cho 1 BĐS (vị trí, tiện ích, pháp lý; price_score mặc định 1.0).
    Trả về giá trị 0..1 (càng cao càng phù hợp).
    """
    score = 0.0
    note = ""

    kb = _load_knowledge_base()
    loc_score = location_score(row.get("district_id") or "", preferred_districts or [], kb)
    # print("loc_score:", loc_score["fit"], score_on_fit(loc_score["fit"]))
    score += score_on_fit(loc_score["fit"])
    note += loc_score["note"]

    # Giá: dùng cột price_billions từ CSV (có thể là string)
    bud_score = budget_score(row.get("price_billions") or "", preferred_budget or [])
    # print("bud_score:", bud_score["fit"], score_on_fit(bud_score["fit"]))
    score += score_on_fit(bud_score["fit"])
    note += bud_score["note"]

    area_score = area_m2_score(row.get("area_m2") or "", preferred_area_m2 or [])
    # print("area_score:", area_score["fit"], score_on_fit(area_score["fit"]))
    score += score_on_fit(area_score["fit"])
    note += area_score["note"]

    # Tiện ích: đảm bảo chuyển về vector 6 phần tử
    facilities_raw = row.get("vector_facilities") or row.get("facilities_vector") or ""
    facilities_vec = facilities_raw
    if not isinstance(facilities_raw, list):
        facilities_vec = _parse_vector_facilities(facilities_raw)
    fac_score = facility_score(facilities_vec, preferred_facilities or [], kb)
    # print("fac_score:", fac_score["score"])
    score += fac_score["score"]
    note += fac_score["note"]

    leg_score = legal_score(row.get("legal_type") or "", kb)
    # print("leg_score:", leg_score["fit"], score_on_fit(leg_score["fit"]))
    score += score_on_fit(leg_score["fit"])
    note += leg_score["note"]

    return {"score" : score, "note" : note}


def recommend(
    candidates: List[Dict],
    preferred_districts: Optional[List] = None,
    preferred_budget: Optional[List] = None,
    preferred_area_m2: Optional[List] = None,
    preferred_facilities: Optional[List] = None,
    top_k: int = 10,
) -> List[Dict]:
    """
    Sắp xếp danh sách BĐS theo điểm và trả về top_k bản ghi.
    Mỗi bản ghi có thêm key "score" (float).
    """
    if preferred_districts == [] and preferred_budget == [] and preferred_area_m2 == [] and preferred_facilities == []:
        return []
    
    scored = []
    for row in candidates:
        s = score_property(
            row,
            preferred_districts=preferred_districts,
            preferred_budget = preferred_budget,
            preferred_area_m2 =  preferred_area_m2,
            preferred_facilities=preferred_facilities,
        )

        scored.append({**row, "score": s["score"], "note" : s["note"]})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

if __name__ == "__main__":
    print("Test hệ thống recommend:")
    kb = _load_knowledge_base()

    candidates = [{"district_id" : "Q1", "budget": 4.0, "area_m2": 70, "facilities_vector": [0, 0, 1, 1, 0, 0]}]
    preferred_districts = ["PHUNHUAN", "Q2", "THUDUC"]
    preferred_budget = [1.0, 2.0]
    preferred_area_m2 = [50, 80]
    preferred_facilities = ["Trường học", "Gym"]

    # print(candidates)
    scored = recommend(candidates, preferred_districts, preferred_budget, preferred_area_m2, preferred_facilities)
    print(scored)

    # print(score_on_fit(0.7))
    
