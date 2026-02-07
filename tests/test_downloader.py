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

@patch('arxiv_translator.downloader.requests.get')
def test_download_source_with_progress(mock_get, tmp_path):
    # Mock response
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
    mock_response.headers.get.return_value = '12' # chunk1(6) + chunk2(6) = 12
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    output_dir = tmp_path / "output_progress"
    arxiv_id = "1234.5678"

    mock_callback = MagicMock()

    path = download_source(arxiv_id, str(output_dir), progress_callback=mock_callback)

    assert os.path.exists(path)
    # Check if callback was called
    # 1. Start
    # 2. Chunk 1
    # 3. Chunk 2
    # 4. Finish
    assert mock_callback.call_count >= 2
    mock_callback.assert_any_call("download", 0.0, f"Downloading source based on {arxiv_id} from https://arxiv.org/e-print/{arxiv_id}...")
    mock_callback.assert_any_call("download", 1.0, f"Downloaded to {path}")
