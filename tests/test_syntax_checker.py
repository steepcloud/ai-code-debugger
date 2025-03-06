import os
from ai_debugger.syntax_checker import SyntaxChecker
from ai_debugger.debugger import Debugger
from ai_debugger.static_analyzer import StaticAnalyzer
from ai_debugger.runtime_err_checker import detect_runtime_error


debugger = Debugger()

def test_syntax_checking():
    file_path = os.path.join(os.path.dirname(__file__), "test_files", "broken_script.py")

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
    file_path = os.path.join(os.path.dirname(__file__), "test_files", "runtime_error_script.py")

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
    file_path = os.path.join(os.path.dirname(__file__), "test_files", "valid_script.py")

    try:
        with open(file_path, 'r') as file:
            print(f"File Content:\n{file.read()}")
    except FileNotFoundError:
        print(f"File {file_path} not found!")

    error = SyntaxChecker.analyze_file(file_path)

    assert error == {}
    error_runtime = detect_runtime_error(file_path)
    assert error_runtime == {}


def test_no_runtime_errors():
    file_path = os.path.join(os.path.dirname(__file__), "test_files", "valid_script.py")

    try:
        with open(file_path, 'r') as file:
            print(f"File Content:\n{file.read()}")
    except FileNotFoundError:
        print(f"File {file_path} not found!")

    error = detect_runtime_error(file_path)
    assert error == {}

def test_static_analysis():
    code = """
def empty_function():
    pass

class EmptyClass:
    pass
    """

    issues = StaticAnalyzer.analyze_code(code)
    assert len(issues) > 0
    assert issues[0]['issue'] == 'Empty Function'
    assert issues[1]['issue'] == 'Empty Class'


def test_prioritize_errors():
    errors = [
        {"issue": "Static Analysis", "message": "Unused variable"},
        {"issue": "Syntax Error", "message": "Missing colon"},
        {"issue": "Runtime Error", "message": "Division by zero"},
    ]

    prioritized = debugger._prioritize_errors(errors)
    assert prioritized[0]["issue"] == "Syntax Error"
    assert prioritized[1]["issue"] == "Runtime Error"
    assert prioritized[2]["issue"] == "Static Analysis"


def test_consolidate_fixes():
    errors = [
        {"issue": "Syntax Error", "message": "Missing colon", "line": 10, "fix_suggestion": "Add colon"},
        {"issue": "Static Analysis", "message": "Unused variable", "line": 15, "fix_suggestion": "Remove variable"},
        {"issue": "Syntax Error", "message": "Indentation error", "line": 10, "fix_suggestion": "Fix indentation"},
    ]
    fixes = debugger._consolidate_fixes(errors)
    assert len(fixes) == 2
    assert len(fixes[10]) == 2
    assert len(fixes[15]) == 1


def test_cross_validate_analysis():
    syntax_err = {"message": "Missing colon"}
    runtime_err = {"message": "Division by zero"}
    static_issues = [{"message": "Unused variable"}, {"message": "Missing colon"}]
    llm_analysis = {"message": "Possible bug"}
    pylint_analysis = {"errors": "Unused variable"}
    validated = debugger._cross_validate_analysis(syntax_err, runtime_err, static_issues, llm_analysis, pylint_analysis)
    assert len(validated) == 4
    assert validated[0]["confidence"] == "High"
    assert validated[1]["confidence"] == "High"


def test_analyze_changes():
    old_file_path = os.path.join(os.path.dirname(__file__), "test_files", "old_script.py")
    new_file_path = os.path.join(os.path.dirname(__file__), "test_files", "new_script.py")
    changes = debugger.analyze_changes(old_file_path, new_file_path)
    assert "changed_lines" in changes
    assert len(changes["changed_lines"]) > 0


def test_analyze_file():
    file_path = os.path.join(os.path.dirname(__file__), "test_files", "broken_script.py")
    result = debugger.analyze_file(file_path, should_generate_report=True)
    assert "errors" in result
    assert "fixes" in result
    assert "validated_issues" in result
    assert "report" in result