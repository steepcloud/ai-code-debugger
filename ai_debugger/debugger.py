import logging
import difflib
import re
from ai_debugger.syntax_checker import SyntaxChecker
from ai_debugger.runtime_err_checker import detect_runtime_error
from ai_debugger.static_analyzer import StaticAnalyzer
from ai_debugger.llm_analyzer import analyze_code_with_llm
from ai_debugger.pylint_analyzer import analyze_code_with_pylint

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def analyze_file(file_path: str, should_generate_report=False, llm_model='microsoft/CodeGPT-small-py', max_length=150) -> dict:
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

    try:
        llm_analysis = analyze_code_with_llm(code, model_name=llm_model, max_length=max_length)
        if llm_analysis:
            errors.append({"issue": "LLM Analysis", "message": llm_analysis})
            logging.info(f"LLM analysis: {llm_analysis}")
    except (ImportError, RuntimeError):
        llm_analysis = None
        logging.warning("LLM analysis skipped due to missing dependencies")

    pylint_analysis = analyze_code_with_pylint(file_path)
    if pylint_analysis['errors']:
        errors.append({"issue": "Pylint Analysis", "message": pylint_analysis['errors']})
        logging.error(f"Pylint analysis errors: {pylint_analysis['errors']}")
    else:
        logging.info(f"Pylint analysis output: {pylint_analysis['output']}")

    if errors:
        prioritized_errors = prioritize_errors(errors)
        consolidated_fixes = consolidate_fixes(prioritized_errors)
        validated_issues = cross_validate_analysis(syntax_err, runtime_err, static_issues,
                                                  llm_analysis, pylint_analysis)

        result = {"errors": prioritized_errors, "fixes": consolidated_fixes,
                  "validated_issues": validated_issues}

        if should_generate_report:
            result["report"] = generate_report(file_path, {"errors": prioritized_errors})

        return result

    logging.info("No errors found.")
    return {}

def prioritize_errors(errors: list) -> list:
    priority_order = {"Syntax Error": 1, "Runtime Error": 2, "Pylint Analysis": 3,
                     "Static Analysis": 4, "LLM Analysis": 5}
    return sorted(errors, key=lambda x: priority_order.get(x.get("issue", ""), 999))


def consolidate_fixes(errors: list) -> dict:
    fixes = {}
    for error in errors:
        if "fix_suggestion" in error:
            line = error.get("line", 0)
            if line not in fixes:
                fixes[line] = []
            fixes[line].append(error["fix_suggestion"])
    return fixes


def cross_validate_analysis(syntax_err, runtime_err, static_issues, llm_analysis, pylint_analysis):
    validated_issues = []

    if static_issues:
        for i, issue in enumerate(static_issues):
            if i == 0:
                issue["confidence"] = "High"
            else:
                issue["confidence"] = "Medium"
            validated_issues.append(issue)

    return validated_issues


def generate_report(file_path: str, errors: dict) -> str:
    report = f"Debug Report for {file_path}\n"
    report += "=" * 50 + "\n\n"

    if not errors:
        report += "No issues detected!\n"
        return report

    for i, error in enumerate(errors.get("errors", [])):
        report += f"Issue #{i + 1}: {error.get('issue', 'Unknown')}\n"
        report += f"Message: {error.get('message', 'No details')}\n"
        if "line" in error:
            report += f"Line: {error['line']}\n"
        if "fix_suggestion" in error:
            report += f"Suggested fix: {error['fix_suggestion']}\n"
        report += "-" * 40 + "\n"

    return report


def analyze_changes(old_file_path: str, new_file_path: str) -> dict:
    with open(old_file_path, 'r', encoding='utf-8') as f1:
        old_content = f1.readlines()
    with open(new_file_path, 'r', encoding='utf-8') as f2:
        new_content = f2.readlines()

    diff = difflib.unified_diff(old_content, new_content, n=3)
    changes = {
        "changed_lines": [],
        "added_lines": [],
        "removed_lines": [],
        "lines_info": {}
    }

    current_line_num = None

    for line in diff:
        if line.startswith('@@'):
            match = re.search(r'\+(\d+)', line)
            if match:
                current_line_num = int(match.group(1)) - 1
            continue
        if line.startswith('---') or line.startswith('+++'):
            continue
        if line.startswith('+'):
            if current_line_num is not None:
                current_line_num += 1
                changes["added_lines"].append(current_line_num)
                changes["changed_lines"].append(current_line_num)
                changes["lines_info"][current_line_num] = {
                    "change_type": "addition",
                    "content": line[1:].strip(),
                }
        elif line.startswith('-'):
            if current_line_num is not None:
                changes["removed_lines"].append(current_line_num)
                changes["changed_lines"].append(current_line_num)
                changes["lines_info"][current_line_num] = {
                    "change_type": "removal",
                    "content": line[1:].strip(),
                }
        else:
            if current_line_num is not None:
                current_line_num += 1

    return changes