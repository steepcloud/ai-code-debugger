import logging
from ai_debugger.syntax_checker import SyntaxChecker
from ai_debugger.runtime_err_checker import detect_runtime_error
from ai_debugger.static_analyzer import StaticAnalyzer
from ai_debugger.llm_analyzer import analyze_code_with_llm
from ai_debugger.pylint_analyzer import analyze_code_with_pylint

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def analyze_file(file_path: str) -> dict:
    errors = []

    logging.info(f"Analyzing file: {file_path}")

    syntax_err = SyntaxChecker.analyze_file(file_path)
    if syntax_err:
        errors.append(syntax_err)
        logging.error(f"Syntax error found: {syntax_err}")

    runtime_err = detect_runtime_error(file_path)
    if runtime_err:
        errors.append(runtime_err)
        logging.error(f"Runtime error found: {runtime_err}")

    with open(file_path, "r", encoding="utf-8") as file:
        code = file.read()
    static_issues = StaticAnalyzer.analyze_code(code)
    if static_issues:
        errors.extend(static_issues)
        logging.error(f"Static analysis issues found: {static_issues}")

    llm_analysis = analyze_code_with_llm(code)
    if llm_analysis:
        errors.append({"issue": "LLM Analysis", "message": llm_analysis})
        logging.info(f"LLM analysis: {llm_analysis}")

    pylint_analysis = analyze_code_with_pylint(file_path)
    if pylint_analysis['errors']:
        errors.append({"issue": "Pylint Analysis", "message": pylint_analysis['errors']})
        logging.error(f"Pylint analysis errors: {pylint_analysis['errors']}")
    else:
        logging.info(f"Pylint analysis output: {pylint_analysis['output']}")

    if errors:
        return {"errors": errors}

    logging.info("No errors found.")
    return {}