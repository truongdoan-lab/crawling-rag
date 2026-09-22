from typing import Iterator

from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based EXCLUSIVELY on the provided context.
Strict rules:
1. Only use information from the context; do not use your own knowledge.
2. If the context is insufficient to answer, state: "I cannot find this information in the provided data."
   Do not guess or fabricate information.
3. When answering, mention the source article name (if available) at the end of the relevant sentence.
4. Provide concise and focused answers."""


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(f"[Source {i} - {c.get('title') or 'unknown'}]\n{c['text']}")
    return "\n\n".join(parts)


class GeminiGenerator:
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _build_prompt(self, question: str, context_chunks: list[dict]) -> str:
        context = build_context(context_chunks)
        return f"Context:\n{context}\n\nQuestion: {question}"

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
