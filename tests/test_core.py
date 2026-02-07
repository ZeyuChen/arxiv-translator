import pytest
import os
from unittest.mock import patch, MagicMock
from arxiv_translator.core import process_arxiv_paper

@patch('arxiv_translator.core.os.path.exists')
@patch('arxiv_translator.core.os.makedirs')
@patch('arxiv_translator.core.shutil.rmtree')
@patch('arxiv_translator.core.shutil.copytree')
@patch('arxiv_translator.core.shutil.copy')
@patch('arxiv_translator.core.os.walk')
@patch('arxiv_translator.core.download_source')
@patch('arxiv_translator.core.extract_source')
@patch('arxiv_translator.core.find_main_tex')
@patch('arxiv_translator.core.GeminiTranslator')
@patch('arxiv_translator.core.compile_pdf')
def test_process_arxiv_paper_flow(mock_compile, mock_translator, mock_find, mock_extract, mock_download,
                                  mock_walk, mock_copy, mock_copytree, mock_rmtree, mock_makedirs, mock_exists):
    # Setup mocks

    # We need to control os.path.exists carefully
    # 1. work_dir check (False)
    # 2. tar_path check (False)
    # 3. source_dir check (False)
    # 4. source_zh_dir check (False)
    # 5. compiled_pdf check (True)

    def side_effect_exists(path):
        if path.endswith(".pdf") and "source_zh" in path:
            return True # Simulate successful compilation
        return False # Assume everything else doesn't exist initially

    mock_exists.side_effect = side_effect_exists

    mock_walk.return_value = [("/tmp/source_zh", [], ["main.tex"])]
    mock_find.return_value = "/tmp/source_zh/main.tex"

    mock_trans_instance = MagicMock()
    mock_trans_instance.translate_latex.return_value = "Translated"
    mock_translator.return_value = mock_trans_instance

    mock_callback = MagicMock()

    # Mock open using mock_open is tricky with patch inside patch context
    # so we use a mock object

    with patch('builtins.open', MagicMock()):
        process_arxiv_paper("1234.5678", "flash", "key", progress_callback=mock_callback)

    # Verify calls
    mock_download.assert_called_once()
    mock_extract.assert_called_once()
    mock_trans_instance.translate_latex.assert_called()
    mock_compile.assert_called_once()

    # Check key callbacks were invoked
    stages = [args[0] for args, _ in mock_callback.call_args_list]
    assert "download" in stages
    assert "extract" in stages
    assert "translate" in stages
    assert "compile" in stages
    assert "done" in stages
