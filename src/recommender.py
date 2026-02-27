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


def location_score(district_id: str, preferred_districts: List[str], kb: Dict) -> float:
    """
    Điểm vị trí theo ma trận location_similarity (0.0–1.0).
    Trùng quận ưu tiên = 1.0; quận khác lấy điểm tương đồng từ KB (max theo từng quận ưu tiên).
    """
    if not preferred_districts or not district_id:
        return 1.0
    district_id = district_id.strip().upper()
    prefs_upper = [d.strip().upper() for d in preferred_districts]
    if district_id in prefs_upper:
        return 1.0
    sim = kb.get("location_similarity") or {}
    best = 0.0
    for pref in prefs_upper:
        row = sim.get(pref)
        if row is None:
            continue
        if isinstance(row, dict):
            best = max(best, float(row.get(district_id, 0.0)))
        else:
            if district_id in [s.upper() for s in (row if isinstance(row, list) else [])]:
                best = max(best, 0.7)
    return best if best > 0 else 0.3


def facility_score(row: Dict, preferred_facilities: List[str], kb: Dict) -> float:
    """
    Điểm tiện ích: cosine giữa vector BĐS và vector ưu tiên user (trọng số 1.0 nếu KB không có facility_weights).
    preferred_facilities: list tên tiện ích (vd: ["Hồ bơi", "Gym", "Trường học"]).
    """
    order = kb.get("facility_order") or FACILITY_ORDER
    weights = kb.get("facility_weights") or {}
    vec = _parse_vector_facilities(row.get("vector_facilities") or [0] * 6)
    if len(vec) < len(order):
        vec = vec + [0] * (len(order) - len(vec))
    pref_vec = [0.0] * len(order)
    for i, name in enumerate(order):
        if i < len(pref_vec) and name in (preferred_facilities or []):
            pref_vec[i] = float(weights.get(name, 1.0))
    vec_f = [float(x) for x in vec[: len(order)]]
    return cosine_similarity(vec_f, pref_vec)


def legal_score(legal_type: str, kb: Dict) -> float:
    """
    Điểm pháp lý theo legal_priority_scores (0.0–1.0). Không có trong KB thì 0.5.
    """
    if not (legal_type or "").strip():
        return 0.5
    scores = kb.get("legal_priority_scores") or {}
    key = (legal_type or "").strip().upper()
    return float(scores.get(key, 0.5))


def score_property(
    row: Dict,
    preferred_districts: Optional[List[str]] = None,
    preferred_facilities: Optional[List[str]] = None,
    price_weight: float = 0.25,
    location_weight: float = 0.35,
    facility_weight: float = 0.35,
    legal_weight: float = 0.05,
) -> float:
    """
    Tổng hợp điểm cho 1 BĐS (vị trí, tiện ích, pháp lý; price_score mặc định 1.0).
    Trả về giá trị 0..1 (càng cao càng phù hợp).
    """
    kb = _load_knowledge_base()
    loc_score = location_score(row.get("district_id") or "", preferred_districts or [], kb)
    fac_score = facility_score(row, preferred_facilities or [], kb)
    leg_score = legal_score(row.get("legal_type") or "", kb)
    price_score = 1.0
    return (
        price_weight * price_score
        + location_weight * loc_score
        + facility_weight * fac_score
        + legal_weight * leg_score
    )


def recommend(
    candidates: List[Dict],
    preferred_districts: Optional[List[str]] = None,
    preferred_facilities: Optional[List[str]] = None,
    top_k: int = 10,
) -> List[Dict]:
    """
    Sắp xếp danh sách BĐS theo điểm và trả về top_k bản ghi.
    Mỗi bản ghi có thêm key "score" (float).
    """
    scored = []
    for row in candidates:
        s = score_property(
            row,
            preferred_districts=preferred_districts,
            preferred_facilities=preferred_facilities,
        )
        scored.append({**row, "score": s})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
