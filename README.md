# Trợ lý ảo RAG tích hợp cào dữ liệu

Cài đặt đầy đủ 2 pipeline đã thiết kế và đánh giá:

## Cài đặt

1. Điền COHERE_API_KEY, COHERE_RERANK_MODEL GEMINI_MODEL

Tải Docker Desktop về PCs, bật ứng dụng và đảm bảo ứng dụng chạy trong suốt quá trình chạy thử.

```bash
docker compose up -d
pip install -r requirements.txt
python -m playwright install chromium --with-deps   # cần cho Crawl4AI
```

## Chạy local

Thao tác nạp URLs:

```bash
python run_ingest.py seed_urls.txt # --watch để chạy lần thứ hai và lên lịch quét định kỳ
```

Thao tác xử lý nội dung trên URLs:

```bash
rq worker crawl_jobs
rqscheduler # Khi có sử dụng --watch để lên lịch định kỳ
```

Chạy chatbot:

```bash
python run_chat.py
```

Đánh giá bằng RAGAS

```bash
pip install -r requirements-eval.txt
cp eval/golden_dataset.example.json eval/golden_dataset.json
python eval/run_eval.py eval/golden_dataset.json
```
