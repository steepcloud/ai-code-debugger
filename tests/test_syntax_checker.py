import pytest
from ai_debugger.syntax_checker import SyntaxChecker
from ai_debugger.debugger import analyze_file
from ai_debugger.runtime_err_checker import detect_runtime_error


def test_syntax_checking():
    file_path = "test_files/broken_script.py"

    try:
        with open(file_path, 'r') as file:
            print(f"File Content:\n{file.read()}")
    except FileNotFoundError:
        print(f"File {file_path} not found!")

    error = SyntaxChecker.analyze_file(file_path)

    assert error != {}
    assert error['error'] == 'Syntax Error'
    assert 'message' in error
    assert 'fix_suggestion' in error


def test_runtime_error_detection():
    file_path = "test_files/runtime_error_script.py"

    try:
        with open(file_path, 'r') as file:
            print(f"File Content:\n{file.read()}")
    except FileNotFoundError:
        print(f"File {file_path} not found!")

    error = detect_runtime_error(file_path)

    assert error != {}
    assert error['error'] == 'Runtime Error'
    assert 'message' in error
    assert 'fix_suggestion' in error


def test_no_errors():
    file_path = "tests/test_files/valid_script.py"

    try:
        with open(file_path, 'r') as file:
            print(f"File Content:\n{file.read()}")
    except FileNotFoundError:
        print(f"File {file_path} not found!")

    result = SyntaxChecker.analyze_file(file_path)

    assert result == {}
    result_runtime = detect_runtime_error(file_path)
    assert result_runtime == {}