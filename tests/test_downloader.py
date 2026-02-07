import os
import pytest
from unittest.mock import patch, MagicMock
from arxiv_translator.downloader import download_source

@patch('arxiv_translator.downloader.requests.get')
def test_download_source(mock_get, tmp_path):
    # Mock response
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    output_dir = tmp_path / "output"
    arxiv_id = "1234.5678"
    
    path = download_source(arxiv_id, str(output_dir))
    
    assert os.path.exists(path)
    assert path.endswith("1234.5678.tar.gz")
    with open(path, 'rb') as f:
        content = f.read()
        assert content == b'chunk1chunk2'
