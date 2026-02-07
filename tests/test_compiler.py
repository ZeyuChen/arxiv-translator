import pytest
from unittest.mock import patch, MagicMock
from arxiv_translator.compiler import compile_pdf

@patch('arxiv_translator.compiler.subprocess.Popen')
@patch('arxiv_translator.compiler.os.getcwd')
@patch('arxiv_translator.compiler.os.chdir')
def test_compile_pdf_with_progress(mock_chdir, mock_getcwd, mock_popen):
    mock_process = MagicMock()
    # Simulate output lines
    mock_process.stdout.readline.side_effect = ["Running latex...", "Done.", ""]
    # Simulate poll behavior:
    # The loop calls poll() only when readline returns "".
    # So it will be called once at the end.
    mock_process.poll.side_effect = [0]
    # stderr=STDOUT means communicate returns (out, None) for stderr
    mock_process.communicate.return_value = ("", None)
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    mock_callback = MagicMock()
    compile_pdf("/tmp/source", "main.tex", progress_callback=mock_callback)

    # Check assertions
    mock_callback.assert_any_call("compile", 0.0, "Compiling main.tex in /tmp/source...")
    mock_callback.assert_any_call("compile", 1.0, "Compilation successful.")
