import re
from dataclasses import dataclass

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


@dataclass
class Chunk:
    text: str
    heading_path: str
    chunk_index: int


def _split_by_heading(markdown: str) -> list[tuple[str, str]]:
    """Trả về list (heading_path, section_text) theo thứ tự xuất hiện."""
    matches = list(HEADING_RE.finditer(markdown))
    if not matches:
        return [("", markdown)]

    sections: list[tuple[str, str]] = []
    heading_stack: list[tuple[int, str]] = []

    for i, m in enumerate(matches):
        level = len(m.group(1))
        heading_text = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()

        heading_stack = [h for h in heading_stack if h[0] < level] + [(level, heading_text)]
        path = " > ".join(h[1] for h in heading_stack)

        if body:
            sections.append((path, body))

    if matches[0].start() > 0:
        preface = markdown[: matches[0].start()].strip()
        if preface:
            sections.insert(0, ("", preface))

    return sections


def _window_split(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    windows = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        windows.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return windows


def chunk_markdown(markdown: str, max_chars: int = 1200, overlap: int = 150) -> list[Chunk]:
    sections = _split_by_heading(markdown)
    chunks: list[Chunk] = []
    idx = 0
    for heading_path, body in sections:
        for window in _window_split(body, max_chars, overlap):
            if window.strip():
                chunks.append(
                    Chunk(text=window.strip(), heading_path=heading_path, chunk_index=idx)
                )
                idx += 1
    return chunks
