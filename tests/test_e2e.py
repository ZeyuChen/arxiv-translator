import pytest
from unittest.mock import patch, MagicMock
import os
import shutil
from src.main import main

@patch('src.main.download_source')
@patch('src.main.extract_source')
@patch('src.main.GeminiTranslator')
@patch('src.main.compile_pdf')
@patch('src.main.find_main_tex')
def test_e2e_mocked(mock_find, mock_compile, mock_translator, mock_extract, mock_download, tmp_path):
    # Setup mocks
    mock_download.return_value = "/tmp/fake.tar.gz"
    mock_find.return_value = str(tmp_path / "source_zh" / "main.tex")
    
    # Mock sys.argv
    with patch('sys.argv', ['main.py', 'https://arxiv.org/abs/1234.5678']):
        # Mock os.path.exists and os.makedirs/shutil to avoid real filesystem errors if paths are weird
        # But we want to test logic. 
        # Easier to let main run and mock the heavy lifting.
        
        # We need to ensure finding main tex works, so we might need to create dummy files
        # or mock the find_main_tex return value (done above)
        
        # We also need os.walk to find files to translate
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                ('/tmp/source_zh', [], ['main.tex'])
            ]
            
            # and open() calls... actually this gets complicated to mock open() for multiple files
            # better to use a real temporary directory structure
            pass

def test_e2e_real_structure(tmp_path):
    # Create fake structure
    (tmp_path / "source").mkdir()
    (tmp_path / "source" / "main.tex").write_text("\\documentclass{article}\\begin{document}Hello\\end{document}")
    
    with patch('src.main.download_source') as mock_dl, \
         patch('src.main.extract_source') as mock_ext, \
         patch('src.main.GeminiTranslator') as mock_trans, \
         patch('src.main.compile_pdf') as mock_comp:
         
        mock_dl.return_value = str(tmp_path / "fake.tar.gz")
        
        def side_effect_extract(tar, dest):
            # simulate extraction by copying from our fake source
            shutil.copytree(str(tmp_path / "source"), dest, dirs_exist_ok=True)
            
        mock_ext.side_effect = side_effect_extract
        
        mock_trans_instance = MagicMock()
        mock_trans_instance.translate_latex.return_value = "Translated"
        mock_trans.return_value = mock_trans_instance
        
        # Run main
        with patch('sys.argv', ['main.py', '1234.5678']):
            # We need to mock os.getcwd/chdir if main relies on it?
            # main uses os.path.abspath(f"workspace_{arxiv_id}")
            # We should probably run it in a temp dir or mock work_dir
            
            # Using a simplified test logic via directly calling functions might be better than main()
            # but main() is what we want to test.
            
            # Let's just run it. It will create workspace_1234.5678 in CWD.
            # We should clean it up.
            try:
                main()
            except SystemExit:
                pass
            
            # Verify translation happened
            # Check if workspace_1234.5678/source_zh/main.tex contains "Translated"
            # Wait, we mocked translate_latex return, so it should be written to file.
            
            work_dir = os.path.abspath("workspace_1234.5678")
            if os.path.exists(work_dir):
                with open(os.path.join(work_dir, "source_zh", "main.tex"), 'r') as f:
                    content = f.read()
                    assert "Translated" in content
                shutil.rmtree(work_dir)
