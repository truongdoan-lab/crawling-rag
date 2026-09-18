# RAG Chatbot Pipeline — Đồ án môn học

Cài đặt đầy đủ 2 pipeline đã thiết kế và đánh giá:

- **Pipeline 1 (Preparation platform):** Redis Queue (điều phối + dedupe) → Crawl4AI/Playwright
  (cào dữ liệu, có fallback static-fetch nhẹ) → PostgreSQL (quản lý nội dung, content-hash + status)
  → BGE-M3 (dense + sparse embedding) → Qdrant (lưu trữ, hybrid search native).
- **Pipeline 2 (Q&A chatbot):** RedisVL semantic cache → Qdrant hybrid search (RRF) →
  Cohere Rerank → Gemini (sinh câu trả lời, có guardrail chống hallucination).

Toàn bộ code implement đúng các lựa chọn + điểm sửa đã thống nhất ở bước đánh giá pipeline
trước đó (xem comment đầu mỗi file để biết file đó xử lý điểm nào trong review).

## 1. Cài đặt

Điền COHERE_API_KEY, COHERE_RERANK_MODEL GEMINI_MODEL

docker compose up -d          # chạy Redis Stack + PostgreSQL + Qdrant
pip install -r requirements.txt
python -m playwright install chromium --with-deps   # cần cho Crawl4AI
```

> **Lưu ý phần cứng:** `FlagEmbedding` (BGE-M3) chạy được trên CPU nhưng khá chậm khi encode
> nhiều bài viết cùng lúc. Nếu có GPU, đặt `EMBEDDING_DEVICE=cuda` trong `.env` để nhanh hơn
> đáng kể. Lần chạy đầu sẽ tự tải model BGE-M3 (~2GB) từ Hugging Face.

## 2. Chạy Pipeline 1 — nạp dữ liệu

Tạo file `seed_urls.txt`, mỗi dòng 1 URL bài viết hoặc trang danh mục muốn crawl, rồi:

```bash
python run_ingest.py seed_urls.txt --watch
```

`--watch` sẽ lên lịch quét lại các trang seed mỗi `CRAWL_INTERVAL_MINUTES` phút để tìm bài mới.
Mở 2 terminal khác để chạy worker xử lý job và scheduler:

```bash
rq worker crawl_jobs      # terminal 2: xử lý từng URL (crawl -> chunk -> embed -> lưu Qdrant)
rqscheduler                # terminal 3: chỉ cần nếu dùng --watch
```

## 3. Chạy Pipeline 2 — chat thử

```bash
python run_chat.py
```

## Cấu trúc thư mục

```
common/config.py                   Đọc .env, cấu hình dùng chung
pipeline1_preparation/
  db.py                            PostgreSQL: content-hash + status (pending/crawled/embedded/failed)
  queue_utils.py, url_queue.py     Redis Queue: dedupe qua Redis Set, rq-scheduler cho lịch định kỳ
  crawler.py                       Fetch nhẹ trước, fallback Crawl4AI/Playwright khi cần
  chunking.py                      Chunk theo heading markdown, cửa sổ overlap cho section dài
  embedder.py                      BGE-M3: dense + sparse trong 1 lần encode
  vector_store.py                  Qdrant: collection dense+sparse, native hybrid search RRF
  worker.py                        RQ job ghép cả chuỗi trên cho 1 URL
pipeline2_chatbot/
  semantic_cache.py                RedisVL SemanticCache, dùng lại embedding BGE-M3
  retriever.py                     Hybrid search qua VectorStore
  reranker.py                      Cohere Rerank, top 1-3
  generator.py                     Gemini + prompt chống hallucination + streaming
  chat_pipeline.py                 Ghép cache -> retrieve -> rerank -> generate
run_ingest.py, run_chat.py         2 CLI để chạy thử từng pipeline
seed_urls.example.txt              Mẫu danh sách URL để nạp Pipeline 1 (copy thành seed_urls.txt)
eval/golden_dataset.example.json   Mẫu bộ câu hỏi-đáp chuẩn để đánh giá (copy thành golden_dataset.json)
eval/run_eval.py                   Script đánh giá bằng RAGAS (faithfulness, answer relevancy, context precision/recall)
scripts/init_db.sql                Schema PostgreSQL
docker-compose.yml                 Redis Stack + PostgreSQL + Qdrant cho local dev
tests/test_chunking.py             Unit test cho chunking (đã chạy PASS)
```

## Đánh giá bằng RAGAS

```bash
pip install -r requirements-eval.txt
cp eval/golden_dataset.example.json eval/golden_dataset.json
# Sửa eval/golden_dataset.json: viết câu hỏi + đáp án chuẩn (reference) dựa trên
# nội dung BẠN ĐÃ crawl thật - nên có 15-20 câu, đa dạng độ khó, có vài câu chắc
# chắn KHÔNG có trong dữ liệu để test guardrail.

python eval/run_eval.py eval/golden_dataset.json
```

Script chạy từng câu hỏi qua đúng `ChatPipeline` thật rồi chấm bằng RAGAS với Gemini
làm judge (không dùng OpenAI mặc định). Kết quả in ra màn hình + lưu chi tiết từng câu
vào `eval/eval_report.csv`.

> **Lưu ý phụ thuộc:** `requirements-eval.txt` có ép `langchain-community<0.4` - đã tự
> kiểm tra và phát hiện bản mới nhất (đang bị "sunset") thiếu 1 module nội bộ mà `ragas`
> cần khi import, gây lỗi dù không hề dùng Vertex AI. Đây là lỗi tương thích giữa 2 thư
> viện bên thứ ba, không phải do code trong repo này.

## Đã tự kiểm tra được gì / còn lại cần bạn tự chạy

Trong môi trường build code này, mình **đã** xác minh:
- Toàn bộ file `.py` qua `py_compile` — không lỗi cú pháp.
- `tests/test_chunking.py` chạy thật và PASS (heading split, window-split có overlap, bỏ qua section rỗng).
- Import thật với các thư viện nhẹ đã cài (`qdrant-client`, `cohere`, `google-genai`, `redisvl`,
  `redis`, `rq`, `psycopg2-binary`...) — xác nhận đúng tên class/hàm dùng trong code
  (`Fusion.RRF`, `cohere.ClientV2`, `genai.Client`, `types.GenerateContentConfig`...).
- Toàn bộ import chéo giữa các module tự viết (dùng mock thay cho `FlagEmbedding`/`crawl4ai`) —
  không có lỗi gõ nhầm tên hàm/tham số.

Mình **chưa** chạy được (do sandbox này không có mạng ra ngoài tới Hugging Face, Google, Cohere,
và không có sẵn Redis/PostgreSQL/Qdrant đang chạy):
- Tải model BGE-M3 thật và encode thử.
- Gọi API Cohere Rerank / Gemini thật.
- Chạy `docker compose up` và toàn bộ luồng end-to-end.

Nên chạy thử theo đúng thứ tự ở mục 1-3 trên máy bạn (có mạng đầy đủ + API key thật) trước khi
demo/nộp bài, để bắt các lỗi runtime cụ thể theo môi trường của bạn (version thư viện, GPU/CPU...).
