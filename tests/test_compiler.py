import pytest
import subprocess
from unittest.mock import patch, MagicMock
from arxiv_translator.compiler import compile_pdf

@patch('arxiv_translator.compiler.os.getcwd')
@patch('arxiv_translator.compiler.os.chdir')
@patch('arxiv_translator.compiler.subprocess.run')
def test_compile_pdf_success(mock_subprocess_run, mock_chdir, mock_getcwd, capsys):
    """Test successful compilation."""
    source_dir = "/source/dir"
    main_tex_file = "/source/dir/main.tex"
    original_cwd = "/original/path"

    # Mocking os.getcwd()
    mock_getcwd.return_value = original_cwd

    # Mocking subprocess.run()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_subprocess_run.return_value = mock_result

    # Run the function
    compile_pdf(source_dir, main_tex_file)

    # Verify os.chdir was called with source_dir
    mock_chdir.assert_any_call(source_dir)

    # Verify subprocess.run was called correctly
    mock_subprocess_run.assert_called_with(
        ['tectonic', 'main.tex'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Verify os.chdir restored original cwd
    mock_chdir.assert_any_call(original_cwd)
    # Ensure it was called at least twice (once to source, once back)
    assert mock_chdir.call_count >= 2
    # Ensure the last call was to original_cwd
    assert mock_chdir.call_args_list[-1][0][0] == original_cwd

    # Verify output
    captured = capsys.readouterr()
    assert "Compilation successful." in captured.out

@patch('arxiv_translator.compiler.os.getcwd')
@patch('arxiv_translator.compiler.os.chdir')
@patch('arxiv_translator.compiler.subprocess.run')
def test_compile_pdf_failure(mock_subprocess_run, mock_chdir, mock_getcwd, capsys):
    """Test compilation failure (non-zero return code)."""
    source_dir = "/source/dir"
    main_tex_file = "/source/dir/main.tex"
    original_cwd = "/original/path"

    mock_getcwd.return_value = original_cwd

    # Mocking subprocess.run() failure
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "Compilation failed output"
    mock_result.stderr = "Error details"
    mock_subprocess_run.return_value = mock_result

    compile_pdf(source_dir, main_tex_file)

    # Verify subprocess.run was called
    mock_subprocess_run.assert_called_once()

    # Verify os.chdir restored original cwd
    assert mock_chdir.call_args_list[-1][0][0] == original_cwd

    # Verify output
    captured = capsys.readouterr()
    assert "Compilation had warnings/errors." in captured.out
    assert "STDOUT: Compilation failed output" in captured.out
    assert "STDERR: Error details" in captured.out

@patch('arxiv_translator.compiler.os.getcwd')
@patch('arxiv_translator.compiler.os.chdir')
@patch('arxiv_translator.compiler.subprocess.run')
def test_compile_pdf_exception(mock_subprocess_run, mock_chdir, mock_getcwd, capsys):
    """Test exception handling during compilation."""
    source_dir = "/source/dir"
    main_tex_file = "/source/dir/main.tex"
    original_cwd = "/original/path"

    mock_getcwd.return_value = original_cwd

    # Mocking subprocess.run() to raise exception
    mock_subprocess_run.side_effect = FileNotFoundError("tectonic not found")

    # Should not raise exception because compile_pdf catches it
    try:
        compile_pdf(source_dir, main_tex_file)
    except Exception as e:
        pytest.fail(f"compile_pdf raised an exception {e} but should have caught it.")

    # Verify os.chdir restored original cwd
    assert mock_chdir.call_args_list[-1][0][0] == original_cwd

    # Verify output
    captured = capsys.readouterr()
    assert "Compiler error: tectonic not found" in captured.out
