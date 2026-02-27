# Real Estate Recommendation System

Hệ thống gợi ý bất động sản: crawl & làm sạch dữ liệu, tri thức (luật + ma trận tương đồng), thuật toán gợi ý (Cosine Similarity), LLM và giao diện Streamlit.

## Cấu trúc project

```
real_estate_rs_project/
├── data/                       # Dữ liệu (Thành viên 2)
│   ├── raw/                    # CSV crawl thô
│   └── processed/              # real_estate_data_final.csv
├── knowledge_base/             # Tri thức (Thành viên 1 & 3)
│   ├── rules.py                # Luật: Lọc cứng (120% budget), Phân khúc khách, Gợi ý Sale (gap)
│   └── knowledge_base.json      # Ma trận tương đồng (vị trí, tiện ích)
├── src/
│   ├── __init__.py
│   ├── data_pipeline.py        # (TV2) Crawl + Clean
│   ├── recommender.py         # (TV3) Điểm, Cosine Similarity
│   └── llm_service.py         # (TV4) API Gemini/GPT, Prompt
├── app.py                      # (TV5) Giao diện Streamlit
├── config.py                   # Cấu hình đường dẫn, từ khóa, ngưỡng
├── requirements.txt
├── .gitignore
└── README.md
```

## Cài đặt

```bash
cd real_estate_rs_project
pip install -r requirements.txt
python -m playwright install chromium
```

## Chạy

- **Giao diện Streamlit (gợi ý BĐS):**
  ```bash
  streamlit run app.py
  ```

- **Crawl + Clean (tạo raw & final CSV):**
  ```bash
  python -m src.data_pipeline --max 200
  python -m src.data_pipeline --clean-only   # Chỉ clean từ file raw
  ```

## Output data

| File | Mô tả |
|------|--------|
| `data/raw/real_estate_data_raw.csv` | Dữ liệu thô từ crawl |
| `data/processed/real_estate_data_final.csv` | Đã chuẩn hóa: district_id, legal_type, vector_facilities; lọc tin ảo & de-dup |

Schema final: id, title, price_billions, area_m2, district_id, legal_type, raw_facilities, vector_facilities, full_desc.
