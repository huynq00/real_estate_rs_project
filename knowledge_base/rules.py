# -*- coding: utf-8 -*-
"""
(Thành viên 1 & 3) Luật suy diễn:
- Hard filter: lọc theo ngân sách (<= 120% budget)
- User profiling: phân khúc khách hàng từ budget, area, facilities_vector
- Sales gap: gợi ý đàm phán (tài chính, pháp lý, tiện ích thay thế)
"""


def apply_hard_filters(user_budget, house_price):
    """
    LUẬT LỌC CỨNG (Hard Constraints)
    Loại bỏ ngay lập tức các căn hộ vượt quá xa khả năng chi trả để tối ưu hiệu năng tính toán.
    Luật: Chỉ chấp nhận nhà có giá <= 120% ngân sách của khách hàng.
    """
    try:
        budget = float(user_budget or 0)
        price = float(house_price or 0)
    except (TypeError, ValueError):
        return True  # Không lọc bỏ nếu không parse được
    if budget <= 0:
        return True
    max_affordable = budget * 1.2
    if price > max_affordable:
        return False  # Loại bỏ
    return True  # Chấp nhận đưa vào vòng tính điểm


def infer_user_segment(user_req):
    """
    LUẬT SUY DIỄN SỞ THÍCH KHÁCH HÀNG (User Profiling)
    Đoán tệp khách hàng dựa trên dữ liệu đầu vào.
    Input: user_req (dict) chứa budget, area_m2, facilities_vector...
    Output: Phân khúc khách hàng (String)
    """
    # Vector tiện ích quy ước: [Hồ bơi, Gym, Công viên, Trường học, Bệnh viện, Siêu thị]
    fv = user_req.get("facilities_vector", [0] * 6)
    if len(fv) < 6:
        fv = fv + [0] * (6 - len(fv))
    needs_school = fv[3] == 1
    needs_park = fv[2] == 1
    area = float(user_req.get("area_m2") or 0)
    budget = float(user_req.get("budget") or 0)

    # Luật 1: Gia đình trẻ (Cần trường học, công viên, diện tích vừa phải)
    if needs_school and needs_park and area >= 60:
        return "Gia đình trẻ (Young Family)"

    # Luật 2: Người độc thân/Vợ chồng mới cưới (Ngân sách vừa, diện tích nhỏ)
    if area > 0 and area < 55 and budget <= 3.5:
        return "Người độc thân/Vợ chồng trẻ (Single/Young Couple)"

    # Luật 3: Khách hàng VIP/Nghỉ dưỡng (Ngân sách cao, cần tiện ích cao cấp)
    needs_pool = fv[0] == 1
    if budget >= 6.0 and needs_pool:
        return "Khách hàng VIP/Hưởng thụ (VIP/Lifestyle)"

    return "Khách hàng tiêu chuẩn (Standard Buyer)"


def analyze_sales_gap(user_profile, house_data, match_score, facility_similarity):
    """
    LUẬT HỖ TRỢ SALE & PHÂN TÍCH GAP (Sales Assistant Rules)
    Nếu điểm phù hợp cao nhưng có một vài tiêu chí không khớp, đưa ra kịch bản đàm phán.
    """
    sales_advice = []

    try:
        user_budget = float(user_profile.get("budget") or 0)
        house_price = float(house_data.get("price_billions") or 0)
    except (TypeError, ValueError):
        user_budget, house_price = 0.0, 0.0

    # 1. Luật Đòn bẩy tài chính (Financial Leverage Rule)
    if match_score >= 0.8 and house_price > user_budget and user_budget > 0:
        diff = round(house_price - user_budget, 2)
        advice = (
            f"TÀI CHÍNH: Khách thiếu {diff} tỷ. Đề xuất Sale tư vấn gói vay trả góp ngân hàng "
            "(Hỗ trợ lãi suất 0% ân hạn nợ gốc)."
        )
        sales_advice.append(advice)

    # 2. Luật Đánh đổi Pháp lý (Legal Trade-off Rule)
    legal = (house_data.get("legal_type") or "").strip().upper()
    if match_score >= 0.75 and legal == "HDMB":
        advice = (
            "PHÁP LÝ: Căn này mới có HĐMB. Đề xuất Sale nhấn mạnh lợi thế "
            "'nhà mới bàn giao, thanh toán theo tiến độ nhẹ nhàng' để bù đắp tâm lý e ngại chưa có sổ."
        )
        sales_advice.append(advice)

    # 3. Luật Thay thế Tiện ích (Facility Trade-off Rule)
    user_vec = list(user_profile.get("facilities_vector", [0] * 6))
    house_vec = list(house_data.get("vector_facilities", [0] * 6))
    if len(user_vec) < 6:
        user_vec.extend([0] * (6 - len(user_vec)))
    if len(house_vec) < 6:
        house_vec.extend([0] * (6 - len(house_vec)))
    facility_names = {
        0: "Hồ bơi",
        1: "Gym",
        2: "Công viên",
        3: "Trường học",
        4: "Bệnh viện",
        5: "Siêu thị",
    }
    matrix = facility_similarity or []
    if len(matrix) < 6:
        matrix = matrix + [[0] * 6 for _ in range(6 - len(matrix))]

    for i in range(6):
        if user_vec[i] != 1 or house_vec[i] == 1:
            continue
        best_alt_idx = -1
        best_alt_score = 0.0
        row_sim = matrix[i] if i < len(matrix) else []
        for j in range(6):
            if j >= len(row_sim) or house_vec[j] != 1 or j == i:
                continue
            sim_score = float(row_sim[j]) if row_sim else 0.0
            if sim_score >= 0.5 and sim_score > best_alt_score:
                best_alt_score = sim_score
                best_alt_idx = j

        if best_alt_idx != -1:
            missing = facility_names.get(i, f"Tiện ích {i}")
            alternative = facility_names.get(best_alt_idx, f"Tiện ích {best_alt_idx}")
            advice = (
                f"TIỆN ÍCH: Nhà thiếu '{missing}' nhưng có '{alternative}' "
                f"(Độ thay thế: {best_alt_score}). Đề xuất Sale dùng '{alternative}' để thuyết phục khách."
            )
            sales_advice.append(advice)
        else:
            missing = facility_names.get(i, f"Tiện ích {i}")
            sales_advice.append(
                f"TIỆN ÍCH: Nhà thiếu '{missing}' và không có tiện ích tương đương để bù đắp. "
                "Sale cần cân nhắc giảm giá hoặc tặng voucher bên ngoài."
            )

    return sales_advice


if __name__ == "__main__":
    print("Test hệ thống luật:")

    test_user = {"budget": 4.0, "area_m2": 70, "facilities_vector": [0, 0, 1, 1, 0, 0]}
    print("Tệp khách hàng dự đoán:", infer_user_segment(test_user))

    test_house = {
        "price_billions": 4.5,
        "legal_type": "HDMB",
        "vector_facilities": [1, 1, 0, 0, 0, 0],
    }
    matrix = [
        [1.0, 0.6, 0.4, 0.1, 0.1, 0.1],
        [0.6, 1.0, 0.3, 0.1, 0.1, 0.1],
        [0.4, 0.3, 1.0, 0.2, 0.2, 0.2],
        [0.1, 0.1, 0.2, 1.0, 0.3, 0.2],
        [0.1, 0.1, 0.2, 0.3, 1.0, 0.3],
        [0.1, 0.1, 0.2, 0.2, 0.3, 1.0],
    ]
    advices = analyze_sales_gap(
        test_user, test_house, match_score=0.85, facility_similarity=matrix
    )
    print("\nGợi ý cho Sale:")
    for a in advices:
        print("-", a)
