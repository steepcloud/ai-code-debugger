from ai_debugger.syntax_checker import SyntaxChecker
from ai_debugger.runtime_err_checker import detect_runtime_error

def analyze_file(file_path: str) -> dict:
    syntax_err = SyntaxChecker.analyze_file(file_path)
    if syntax_err:
        return syntax_err

    runtime_err = detect_runtime_error(file_path)
    if runtime_err:
        return runtime_err

    return {}