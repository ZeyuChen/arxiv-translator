import os
import shutil
import pytest
import sys

# Ensure src is in path for imports
sys.path.append(os.path.join(os.getcwd(), 'src'))

from arxiv_translator.extractor import find_main_tex

@pytest.fixture
def temp_source_dir(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    return source_dir

def test_find_main_tex_single_file(temp_source_dir):
    (temp_source_dir / "main.tex").write_text("\\documentclass{article}", encoding='utf-8')
    assert find_main_tex(str(temp_source_dir)) == str(temp_source_dir / "main.tex")

def test_find_main_tex_multiple_files_with_documentclass(temp_source_dir):
    (temp_source_dir / "other.tex").write_text("Just some text", encoding='utf-8')
    (temp_source_dir / "main.tex").write_text("\\documentclass{article}", encoding='utf-8')
    assert find_main_tex(str(temp_source_dir)) == str(temp_source_dir / "main.tex")

def test_find_main_tex_priority(temp_source_dir):
    # Both have documentclass, but main.tex has priority
    (temp_source_dir / "other_candidates.tex").write_text("\\documentclass{article}", encoding='utf-8')
    (temp_source_dir / "main.tex").write_text("\\documentclass{article}", encoding='utf-8')
    assert find_main_tex(str(temp_source_dir)) == str(temp_source_dir / "main.tex")

def test_find_main_tex_priority_ms(temp_source_dir):
    # ms.tex has priority over random names
    (temp_source_dir / "random.tex").write_text("\\documentclass{article}", encoding='utf-8')
    (temp_source_dir / "ms.tex").write_text("\\documentclass{article}", encoding='utf-8')
    assert find_main_tex(str(temp_source_dir)) == str(temp_source_dir / "ms.tex")

def test_find_main_tex_no_tex_files(temp_source_dir):
    with pytest.raises(FileNotFoundError):
        find_main_tex(str(temp_source_dir))

def test_find_main_tex_documentclass_not_at_start(temp_source_dir):
    # Check if it finds documentclass even if it's not the very first line
    # but still within the first 4096 chars
    content = "% Comments\n" * 10 + "\\documentclass{article}"
    (temp_source_dir / "main.tex").write_text(content, encoding='utf-8')
    assert find_main_tex(str(temp_source_dir)) == str(temp_source_dir / "main.tex")

def test_find_main_tex_documentclass_too_far(temp_source_dir):
    # If documentclass is beyond 4096 chars, it should NOT find it as candidate
    # But since it falls back to first tex file if no candidate found,
    # we need to be careful what we test.

    # Case: Two files.
    # 'far.tex': documentclass at 5000 chars (missed by scan)
    # 'near.tex': documentclass at 0 chars (found by scan)
    # Should pick 'near.tex'

    content_far = "a" * 5000 + "\\documentclass{article}"
    (temp_source_dir / "far.tex").write_text(content_far, encoding='utf-8')
    (temp_source_dir / "near.tex").write_text("\\documentclass{article}", encoding='utf-8')

    assert find_main_tex(str(temp_source_dir)) == str(temp_source_dir / "near.tex")

def test_find_main_tex_fallback(temp_source_dir):
    # No file has documentclass in first 4096 chars.
    # Should return one of them.
    (temp_source_dir / "a.tex").write_text("content", encoding='utf-8')
    (temp_source_dir / "b.tex").write_text("content", encoding='utf-8')

    result = find_main_tex(str(temp_source_dir))
    # It returns candidates[0] if candidates exist, else tex_files[0]
    # here candidates is empty. tex_files order depends on OS.
    assert result in [str(temp_source_dir / "a.tex"), str(temp_source_dir / "b.tex")]

def test_find_main_tex_large_file_performance(temp_source_dir):
    # Functional test for large file, ensuring no crash
    large_content = "a" * (1024 * 1024) # 1MB
    (temp_source_dir / "large.tex").write_text(large_content, encoding='utf-8')
    # Just ensure it doesn't crash and returns something
    assert find_main_tex(str(temp_source_dir)) == str(temp_source_dir / "large.tex")
