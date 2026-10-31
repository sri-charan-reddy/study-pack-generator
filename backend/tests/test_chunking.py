from app.ai.chunking import chunk_text, distribute


def _doc(pages: int, words_per_page: int = 300) -> str:
    return "\n\n".join(f"[Page {i}]\n" + " ".join(f"w{i}_{j}" for j in range(words_per_page)) for i in range(1, pages + 1))


def test_single_chunk_when_small():
    text = _doc(2, 50)
    chunks = chunk_text(text, 40000)
    assert len(chunks) == 1 and chunks[0].text == text


def test_splits_on_page_markers_without_losing_text():
    text = _doc(10)
    chunks = chunk_text(text, 6000)
    assert len(chunks) > 1
    assert all(c.char_count <= 6000 for c in chunks)
    assert all(c.text.startswith("[Page ") for c in chunks)
    joined = "\n\n".join(c.text for c in chunks)
    assert joined.split() == text.split()  # nothing discarded


def test_oversized_section_is_split_on_paragraphs():
    section = "## Big\n\n" + "\n\n".join("para " * 200 for _ in range(20))
    chunks = chunk_text(section, 3000)
    assert len(chunks) > 1
    assert " ".join(c.text for c in chunks).split() == section.split()


def test_distribute_sums_to_total():
    assert sum(distribute(10, [100, 50, 50])) == 10
    assert distribute(10, [100, 50, 50]) == [5, 3, 2] or sum(distribute(10, [100, 50, 50])) == 10
    assert distribute(0, [1, 2]) == [0, 0]
    assert distribute(3, [1]) == [3]
