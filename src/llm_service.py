# -*- coding: utf-8 -*-
"""
(Thành viên 4) Gọi API Gemini/GPT và Prompt để phân tích nhu cầu / tóm tắt BĐS.
"""

import os
from typing import Optional, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import dotenv

# Tải biến môi trường từ file .env
dotenv.load_dotenv()

# Lấy key từ .env
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def _extract_text_from_response(response) -> str:
    """
    Chuẩn hóa output từ ChatGoogleGenerativeAI về dạng string thuần.
    Một số phiên bản LangChain trả về list block [{type: 'text', text: '...'}].
    """
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content

    # LangChain mới: content là list các block
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        if parts:
            return "\n\n".join(parts)

    return str(content)


class LLMService:
    def __init__(self, model_name: str = "gemini-2.5-flash-lite", temperature: float = 0.7):
        # Truyền API key tường minh để tránh lỗi xác thực
        self.llm = ChatGoogleGenerativeAI(
            model=model_name, 
            temperature=temperature,
            google_api_key=GEMINI_API_KEY 
        )
        
        # 1. Template Giải thích Khuyến nghị (Sát đề bài đồ án)
        self.explain_template = ChatPromptTemplate.from_messages([
            ("system", """Bạn là một chuyên gia tư vấn BĐS cao cấp. Nhiệm vụ của bạn là chuyển đổi các dữ liệu toán học khô khan thành lời tư vấn tự nhiên, thuyết phục để giải thích lý do căn hộ này phù hợp với khách.
                Nguyên tắc tối thượng: KHÔNG ĐƯỢC bịa đặt thông tin, tiện ích, hay giá cả không có trong dữ liệu được cung cấp."""),
                            ("user", """Dưới đây là thông tin chi tiết từ hệ thống:

                1. Hồ sơ khách hàng:
                {user_profile}

                2. Thông tin căn hộ được đề xuất:
                {house_data}

                3. Dữ liệu phân tích từ thuật toán (Độ phù hợp tổng quan: {match_score}/1.0):
                - Đánh giá về giá: {price_analysis}
                - Đánh giá về tiện ích: {facility_analysis}
                - Tri thức hệ thống (Ma trận tương đồng): {similarity_knowledge}

                Yêu cầu thực thi:
                - Viết một đoạn văn ngắn (3-4 câu) thuyết phục khách hàng.
                - BẮT BUỘC sử dụng dữ liệu từ "Tri thức hệ thống" (nhấn mạnh sự tương đồng tiện ích/vị trí) để biện minh cho gợi ý này, giúp khách hàng thấy rằng dù không khớp 100% yêu cầu ban đầu nhưng đây vẫn là sự lựa chọn thay thế hoàn hảo.
                - Văn phong chuyên nghiệp, khéo léo, tập trung vào giá trị mang lại cho khách hàng.""")
        ])

        # 2. Template So sánh 2 sản phẩm (Comparison & Trade-off)
        self.compare_template = ChatPromptTemplate.from_messages([
            ("system", """Bạn là chuyên gia phân tích BĐS khách quan và sắc bén. Nhiệm vụ của bạn là giúp khách hàng ra quyết định khi họ đang phân vân giữa 2 lựa chọn.
                Nguyên tắc: KHÔNG ĐƯỢC thiên vị vô lý. Bắt buộc phân tích dựa trên sự đánh đổi (Trade-off) thực tế từ dữ liệu đầu vào. Trọng tâm là đối chiếu lợi ích - rủi ro (đặc biệt là tính pháp lý và tài chính)."""),
                            ("user", """Hãy phân tích so sánh 2 bất động sản sau cho khách hàng:

                1. Hồ sơ khách hàng:
                {user_profile}

                2. Thông tin Căn A:
                {house_a_data}

                3. Thông tin Căn B:
                {house_b_data}

                4. Luật ưu tiên của hệ thống:
                {system_rules}

                Yêu cầu thực thi:
                - Viết một đoạn so sánh ngắn gọn, chỉ ra điểm mạnh/yếu cốt lõi của từng căn.
                - BẮT BUỘC có phần "Phân tích sự đánh đổi (Trade-off)": Nhấn mạnh rõ ràng nếu chọn A thì được gì/mất gì, chọn B thì đối mặt rủi ro gì (dựa vào Luật ưu tiên của hệ thống).
                - Đưa ra lời khuyên cuối cùng một cách tinh tế.""")
                        ])

        # 3. Template Trợ lý Sale & Đàm phán (Sales Assistant & Gap Analysis)
        self.sales_template = ChatPromptTemplate.from_messages([
            ("system", """Bạn là một chuyên viên Sale BĐS "Thực chiến" và khéo léo (Top Seller). Khách hàng đang có ý định từ chối hoặc chần chừ.
                Nhiệm vụ của bạn là đưa ra kịch bản đàm phán để cứu vãn giao dịch. Tuyệt đối không nài ép thô thiển, hãy dùng logic dòng tiền và sự đồng cảm để thuyết phục."""),
                            ("user", """Tình huống đàm phán:

                1. Dữ liệu căn hộ khách đang xem:
                {house_data}

                2. Lý do khách đang phân vân/từ chối (Gap Reason):
                {gap_reason}

                Yêu cầu thực thi:
                Hãy viết một kịch bản thoại đàm phán ngắn gọn (đúng 3-4 câu) cho nhân viên Sale đọc trực tiếp với khách:
                - Câu 1: Đồng cảm sâu sắc với khó khăn/lo lắng của khách.
                - Câu 2: Đề xuất giải pháp (Gợi ý gói vay ngân hàng, giãn tiến độ thanh toán) HOẶC nhấn mạnh tiềm năng tăng giá/giá trị vô hình để bù đắp rủi ro/chi phí.
                - Câu 3: Lời kêu gọi hành động (Call to action) nhẹ nhàng nhưng dứt khoát để giữ chân khách đi xem nhà hoặc cọc thiện chí.""")
        ])

    def generate_explanation(self, user_profile: str, house_data: str, match_score: float, 
                             price_analysis: str, facility_analysis: str, similarity_knowledge: str) -> str:
        """[Prompt 1] Sinh lời giải thích tại sao căn hộ phù hợp, dựa trên ma trận tương đồng."""
        chain = self.explain_template | self.llm
        try:
            response = chain.invoke({
                "user_profile": user_profile,
                "house_data": house_data,
                "match_score": match_score,
                "price_analysis": price_analysis,
                "facility_analysis": facility_analysis,
                "similarity_knowledge": similarity_knowledge
            })
            return _extract_text_from_response(response)
        except Exception as e:
            # In toàn bộ lỗi LLM ra terminal để debug
            import traceback
            print("[LLM][generate_explanation] Error:", repr(e))
            traceback.print_exc()
            return f"Hệ thống LLM đang bận, vui lòng thử lại. (Lỗi: {str(e)})"

    def generate_comparison(self, user_profile: str, house_a_data: str, house_b_data: str, system_rules: str) -> str:
        """[Prompt 2] So sánh 2 căn hộ, phân tích sự đánh đổi (Trade-off) dựa trên luật hệ thống."""
        chain = self.compare_template | self.llm
        try:
            response = chain.invoke({
                "user_profile": user_profile,
                "house_a_data": house_a_data,
                "house_b_data": house_b_data,
                "system_rules": system_rules
            })
            return _extract_text_from_response(response)
        except Exception as e:
            import traceback
            print("[LLM][generate_comparison] Error:", repr(e))
            traceback.print_exc()
            return f"Không thể tạo bảng so sánh lúc này. (Lỗi: {str(e)})"

    def generate_sales_script(self, house_data: str, gap_reason: str) -> str:
        """[Prompt 3] Sinh kịch bản đàm phán chốt Sale xử lý tình huống khách từ chối."""
        chain = self.sales_template | self.llm
        try:
            response = chain.invoke({
                "house_data": house_data,
                "gap_reason": gap_reason
            })
            return _extract_text_from_response(response)
        except Exception as e:
            import traceback
            print("[LLM][generate_sales_script] Error:", repr(e))
            traceback.print_exc()
            return f"Không thể tạo kịch bản đàm phán lúc này. (Lỗi: {str(e)})"


# def get_llm_client():
#     """
#     Trả về client LLM (Gemini hoặc OpenAI) theo biến môi trường.
#     Ví dụ: GOOGLE_API_KEY hoặc OPENAI_API_KEY.
#     """
#     # Placeholder: có thể dùng google-generativeai hoặc openai
#     api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
#     if api_key:
#         try:
#             import google.generativeai as genai
#             genai.configure(api_key=api_key)
#             return genai.GenerativeModel("gemini-1.5-flash")
#         except ImportError:
#             pass
#     api_key = os.environ.get("OPENAI_API_KEY")
#     if api_key:
#         try:
#             import openai
#             return openai.OpenAI(api_key=api_key)
#         except ImportError:
#             pass
#     return None


# def parse_user_preferences(user_text: str) -> Dict[str, Any]:
#     """
#     Dùng LLM để trích xuất từ user_text:
#     - preferred_districts: list quận (Q7, Bình Thạnh, ...)
#     - preferred_facilities: list tiện ích (Hồ bơi, Gym, ...)
#     - min_price, max_price (tỷ), min_area, max_area (m²)
#     Trả về dict; nếu không có LLM thì trả về dict rỗng.
#     """
#     client = get_llm_client()
#     if not client:
#         return {}
#     # TODO: gọi API với prompt chuẩn, parse JSON từ response
#     # Ví dụ prompt: "Từ đoạn sau trích xuất thông tin ưu tiên BĐS (quận, tiện ích, khoảng giá, diện tích). Trả về JSON."
#     return {}


# def summarize_property(row: Dict[str, Any]) -> str:
#     """
#     Tạo mô tả ngắn cho 1 BĐS (dùng LLM hoặc template).
#     """
#     title = row.get("title") or "Căn hộ"
#     price = row.get("price_billions")
#     area = row.get("area_m2")
#     district = row.get("district_id") or ""
#     legal = row.get("legal_type") or ""
#     facilities = row.get("raw_facilities") or ""
#     parts = [title]
#     if price is not None and price != "":
#         parts.append(f"Giá: {price} tỷ")
#     if area is not None and area != "":
#         parts.append(f"Diện tích: {area} m²")
#     if district:
#         parts.append(f"Vị trí: {district}")
#     if legal:
#         parts.append(f"Pháp lý: {legal}")
#     if facilities:
#         parts.append(f"Tiện ích: {facilities}")
#     return " | ".join(parts)
