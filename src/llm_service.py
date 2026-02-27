# -*- coding: utf-8 -*-
"""
(Thành viên 4) Gọi API Gemini/GPT và Prompt để phân tích nhu cầu / tóm tắt BĐS.
"""

import os
from typing import Optional, Dict, Any


def get_llm_client():
    """
    Trả về client LLM (Gemini hoặc OpenAI) theo biến môi trường.
    Ví dụ: GOOGLE_API_KEY hoặc OPENAI_API_KEY.
    """
    # Placeholder: có thể dùng google-generativeai hoặc openai
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            return genai.GenerativeModel("gemini-1.5-flash")
        except ImportError:
            pass
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            import openai
            return openai.OpenAI(api_key=api_key)
        except ImportError:
            pass
    return None


def parse_user_preferences(user_text: str) -> Dict[str, Any]:
    """
    Dùng LLM để trích xuất từ user_text:
    - preferred_districts: list quận (Q7, Bình Thạnh, ...)
    - preferred_facilities: list tiện ích (Hồ bơi, Gym, ...)
    - min_price, max_price (tỷ), min_area, max_area (m²)
    Trả về dict; nếu không có LLM thì trả về dict rỗng.
    """
    client = get_llm_client()
    if not client:
        return {}
    # TODO: gọi API với prompt chuẩn, parse JSON từ response
    # Ví dụ prompt: "Từ đoạn sau trích xuất thông tin ưu tiên BĐS (quận, tiện ích, khoảng giá, diện tích). Trả về JSON."
    return {}


def summarize_property(row: Dict[str, Any]) -> str:
    """
    Tạo mô tả ngắn cho 1 BĐS (dùng LLM hoặc template).
    """
    title = row.get("title") or "Căn hộ"
    price = row.get("price_billions")
    area = row.get("area_m2")
    district = row.get("district_id") or ""
    legal = row.get("legal_type") or ""
    facilities = row.get("raw_facilities") or ""
    parts = [title]
    if price is not None and price != "":
        parts.append(f"Giá: {price} tỷ")
    if area is not None and area != "":
        parts.append(f"Diện tích: {area} m²")
    if district:
        parts.append(f"Vị trí: {district}")
    if legal:
        parts.append(f"Pháp lý: {legal}")
    if facilities:
        parts.append(f"Tiện ích: {facilities}")
    return " | ".join(parts)
