"""
Sinh câu trả lời cuối cùng bằng Gemini.

Điểm còn thiếu đã nêu trong review, xử lý ở đây:
- Prompt ép model chỉ dùng context được cung cấp, và từ chối trả lời khi
  thiếu thông tin thay vì tự bịa (chống hallucination) - gần như bắt buộc
  với một RAG chatbot nghiêm túc.
- generate_stream(): streaming response để cải thiện trải nghiệm chat.

Dùng google-genai (SDK hiện hành) thay cho google-generativeai đã deprecated.
Tên model cần chốt lại theo bản hiện hành khi triển khai thực tế (dòng
Flash-Lite của Gemini 3 hiện đã lên tới bản 3.5, xem phần đánh giá).
"""
from typing import Iterator

from google import genai
from google.genai import types

SYSTEM_PROMPT = """Bạn là trợ lý trả lời câu hỏi dựa HOÀN TOÀN vào các đoạn ngữ cảnh được cung cấp.
Quy tắc bắt buộc:
1. Chỉ dùng thông tin có trong ngữ cảnh; không dùng kiến thức nền của bạn.
2. Nếu ngữ cảnh không đủ để trả lời, nói rõ: "Tôi không tìm thấy thông tin này trong dữ liệu hiện có."
   Không suy đoán hay bịa thông tin.
3. Khi trả lời, nêu tên bài viết nguồn (nếu có) ở cuối câu liên quan.
4. Trả lời ngắn gọn, đúng trọng tâm câu hỏi."""


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(f"[Nguồn {i} - {c.get('title') or 'không rõ'}]\n{c['text']}")
    return "\n\n".join(parts)


class GeminiGenerator:
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _build_prompt(self, question: str, context_chunks: list[dict]) -> str:
        context = build_context(context_chunks)
        return f"Ngữ cảnh:\n{context}\n\nCâu hỏi: {question}"

    def generate(self, question: str, context_chunks: list[dict]) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=self._build_prompt(question, context_chunks),
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.2),
        )
        return response.text

    def generate_stream(self, question: str, context_chunks: list[dict]) -> Iterator[str]:
        stream = self._client.models.generate_content_stream(
            model=self._model,
            contents=self._build_prompt(question, context_chunks),
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.2),
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text
