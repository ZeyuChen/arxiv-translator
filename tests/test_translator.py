import pytest
from unittest.mock import patch, MagicMock
from src.translator import GeminiTranslator

@patch('src.translator.genai.Client')
def test_translator_init(mock_client):
    translator = GeminiTranslator("fake_key")
    mock_client.assert_called_with(api_key="fake_key")

@patch('src.translator.genai.Client')
def test_translate_latex(mock_client):
    # Setup mock
    mock_response = MagicMock()
    mock_response.text = "Translated Content"
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_client.return_value.models = mock_model
    
    translator = GeminiTranslator("fake_key")
    result = translator.translate_latex("Original Content")
    
    assert result == "Translated Content"
    mock_model.generate_content.assert_called_once()
    args, kwargs = mock_model.generate_content.call_args
    assert args == ()
    assert kwargs['contents'] == ["Original Content"]
    # Check system instruction is present (impl detail)
    assert kwargs['config'].system_instruction is not None

@patch('src.translator.genai.Client')
def test_translate_latex_markdown_cleanup(mock_client):
    mock_response = MagicMock()
    mock_response.text = "```latex\nClean Content\n```"
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_client.return_value.models = mock_model
    
    translator = GeminiTranslator("fake_key")
    result = translator.translate_latex("Original")
    
    assert result == "Clean Content"
