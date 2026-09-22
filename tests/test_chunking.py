import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preparation_pipeline.chunking import chunk_markdown


def test_no_heading_falls_back_to_window_split():
    text = "a" * 3000
    chunks = chunk_markdown(text, max_chars=1000, overlap=100)
    assert len(chunks) == 4  # 1000, 1000, 1000, phần dư có overlap
    assert all(c.heading_path == "" for c in chunks)


def test_splits_by_heading_and_keeps_path():
    markdown = (
        "# Giới thiệu\n"
        "Nội dung mở đầu.\n"
        "## Lịch sử\n"
        "Nội dung lịch sử.\n"
        "# Kết luận\n"
        "Nội dung kết luận.\n"
    )
    chunks = chunk_markdown(markdown, max_chars=1000, overlap=50)
    paths = [c.heading_path for c in chunks]
    assert "Giới thiệu" in paths
    assert "Giới thiệu > Lịch sử" in paths
    assert "Kết luận" in paths


def test_long_section_still_gets_window_split_with_overlap():
    markdown = "# Mục dài\n" + ("b" * 2500)
    chunks = chunk_markdown(markdown, max_chars=1000, overlap=100)
    assert len(chunks) == 3
    assert all(c.heading_path == "Mục dài" for c in chunks)
    # đoạn overlap giữa chunk 1 và 2 phải trùng nhau
    assert chunks[0].text[-100:] == chunks[1].text[:100]


def test_empty_sections_are_skipped():
    markdown = "# A\n\n# B\nNội dung B.\n"
    chunks = chunk_markdown(markdown)
    assert len(chunks) == 1
    assert chunks[0].heading_path == "B"


if __name__ == "__main__":
    test_no_heading_falls_back_to_window_split()
    test_splits_by_heading_and_keeps_path()
    test_long_section_still_gets_window_split_with_overlap()
    test_empty_sections_are_skipped()
    print("Tất cả test chunking đều PASS.")
