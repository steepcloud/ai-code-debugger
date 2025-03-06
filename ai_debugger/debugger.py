import logging
import difflib
import re
import os
import ast
from pathlib import Path
from ai_debugger.config import Config
from ai_debugger.syntax_checker import SyntaxChecker
from ai_debugger.runtime_err_checker import detect_runtime_error
from ai_debugger.static_analyzer import StaticAnalyzer
from ai_debugger.llm_analyzer import analyze_code_with_llm
from ai_debugger.pylint_analyzer import analyze_code_with_pylint

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Debugger:
    def __init__(self, config_path=None, llm_model=None, max_length=None):
        self.config = Config(config_path)
        self.breakpoints = {}
        self.current_file = None
        self.current_line = 0
        self.variables = {}
        self.call_stack = []
        self.return_value = None
        self.llm_model = llm_model or "microsoft/CodeGPT-small-py"
        self.max_length = max_length or 150


    def analyze_file(self, file_path: str, should_generate_report=False) -> dict:
        errors = []

        logging.info(f"Analyzing file: {file_path}")

        max_size = self.config.get("max_file_size_mb", 5) * 1024 * 1024
        if os.path.getsize(file_path) > max_size:
            return {"error": f"File size exceeds the configured limit of {self.config.get('max_file_size_mb')}MB"}

        llm_model = self.config.get("models.default", "microsoft/CodeGPT-small-py")

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
            llm_analysis = analyze_code_with_llm(code,
                                                 model_name=self.llm_model,
                                                 max_length=self.max_length)
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
            prioritized_errors = self._prioritize_errors(errors)
            consolidated_fixes = self._consolidate_fixes(prioritized_errors)
            validated_issues = self._cross_validate_analysis(syntax_err, runtime_err, static_issues,
                                                      llm_analysis, pylint_analysis)

            result = {"errors": prioritized_errors, "fixes": consolidated_fixes,
                      "validated_issues": validated_issues}

            if should_generate_report:
                result["report"] = self._generate_report(file_path, {"errors": prioritized_errors})

            return result

        logging.info("No errors found.")
        return {}


    def set_breakpoint(self, file, line):
        if file not in self.breakpoints:
            self.breakpoints[file] = []
        if line not in self.breakpoints[file]:
            self.breakpoints[file].append(line)
            return True
        return False


    def remove_breakpoint(self, file, line):
        if file in self.breakpoints and line in self.breakpoints[file]:
            self.breakpoints[file].remove(line)
            return True
        return False


    def list_breakpoints(self):
        return self.breakpoints


    def step_over(self):
        if self.current_file:
            self.current_line += 1
            return True
        return False


    def step_into(self):
        if not self.current_file or self.current_line is None:
            return False

        try:
            with open(self.current_file, 'r', encoding='utf-8') as file:
                code = file.read()

            tree = ast.parse(code)
            function_calls = []

            class FunctionCallVisitor(ast.NodeVisitor):
                def __init__(self, current_line):
                    self.current_line = current_line
                    super().__init__()

                def visit_Call(self, node):
                    if hasattr(node, 'lineno') and node.lineno == self.current_line + 1:
                        if isinstance(node.func, ast.Name):
                            function_calls.append(node.func.id)
                        elif isinstance(node.func, ast.Attribute):
                            function_calls.append(node.func.attr)
                    self.generic_visit(node)

            visitor = FunctionCallVisitor(self.current_line)
            visitor.visit(tree)

            if not function_calls:
                logging.debug(f"No function calls found at line {self.current_line + 1}")
                return False

            function_name = function_calls[0]
            function_def_lineno = self._find_function_definition(function_name)

            if function_def_lineno is None:
                logging.debug(f"Could not find definition for function '{function_name}'")
                return False

            if not hasattr(self, 'call_stack'):
                self.call_stack = []

            self.call_stack.append({
                'file': self.current_file,
                'line': self.current_line,
                'function': function_name,
                'locals': self.variables.copy() if hasattr(self, 'variables') else {}
            })

            self.current_line = function_def_lineno
            logging.info(f"Stepped into function '{function_name}' at line {function_def_lineno + 1}")

            self.variables = self._extract_function_parameters(function_name, code)
            return True

        except Exception as e:
            logging.error(f"Error stepping into function: {str(e)}")
            return False


    def step_out(self):
        if not hasattr(self, 'call_stack') or not self.call_stack:
            logging.debug("Cannot step out: call stack is empty")
            return False

        try:
            call_frame = self.call_stack.pop()

            self.current_file = call_frame['file']
            self.current_line = call_frame['line'] + 1

            stored_locals = call_frame.get('locals', {})

            if hasattr(self, 'return_value') and self.return_value is not None:
                stored_locals['_return'] = self.return_value
                self.return_value = None

            self.variables = stored_locals
            logging.info(f"Stepped out to line {self.current_line + 1}")
            return True

        except Exception as e:
            logging.error(f"Error stepping out: {str(e)}")
            return False


    def _find_function_definition(self, function_name):
        try:
            with open(self.current_file, 'r', encoding='utf-8') as file:
                code = file.read()

            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    return node.lineno - 1
            return None

        except Exception as e:
            logging.error(f"Error finding function definition: {str(e)}")
            return None


    def _extract_function_parameters(self, function_name, code):
        try:
            tree = ast.parse(code)
            parameters = {}

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    for arg in node.args.args:
                        parameters[arg.arg] = None

                    defaults = node.args.defaults
                    if defaults:
                        default_offset = len(node.args.args) - len(defaults)
                        for i, default in enumerate(defaults):
                            arg_index = default_offset + i
                            if arg_index < len(node.args.args):
                                arg_name = node.args.args[arg_index].arg
                                parameters[arg_name] = '<default value>'
                    break
            return parameters

        except Exception as e:
            logging.error(f"Error extracting function parameters: {str(e)}")
            return {}


    def inspect_variable(self, variable_name):
        if variable_name in self.variables:
            return self.variables[variable_name]
        return None


    def analyze_changes(self, old_file_path: str, new_file_path: str) -> dict:
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


    def suggest_fix_for_line(self, file_path, line_number):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                code_lines = file.readlines()

            if line_number < 0 or line_number >= len(code_lines):
                return ["Invalid line number"]

            start = max(0, line_number - 2)
            end = min(len(code_lines), line_number + 3)
            context = ''.join(code_lines[start:end])

            target_line = code_lines[line_number].strip()

            suggestions = []

            syntax_check = SyntaxChecker.analyze_line(target_line, line_number)
            if syntax_check:
                suggestions.append(syntax_check.get("fix_suggestion", "Add missing syntax element"))

            try:
                prompt = (
                    f"The following Python code has an issue on line {line_number + 1}:\n\n"
                    f"{context}\n\n"
                    f"Line {line_number + 1} is: {target_line}\n\n"
                    "Provide exactly three suggestions to fix this code. Each suggestion should be a complete, corrected version of the line."
                )

                llm_suggestions = analyze_code_with_llm(
                    prompt,
                    model_name=self.llm_model,
                    max_length=self.max_length
                )

                if isinstance(llm_suggestions, str):
                    import re
                    fixes = re.findall(r'(\d+\.\s*`.*?`)', llm_suggestions, re.DOTALL)
                    if fixes:
                        for fix in fixes:
                            code = re.search(r'`(.*?)`', fix)
                            if code:
                                suggestions.append(code.group(1))
                    else:
                        suggestions.append(llm_suggestions)
            except Exception as e:
                logging.warning(f"LLM suggestion failed: {str(e)}")

            if not suggestions:
                if ":" not in target_line and ("if " in target_line or "def " in target_line or "else" in target_line):
                    suggestions.append(f"{target_line}:")
                elif "==" in target_line and "if" in target_line:
                    suggestions.append(target_line.replace("=", "=="))
                elif "=" in target_line and "if" in target_line:
                    suggestions.append(target_line.replace("=", "=="))
                else:
                    suggestions.append("Check indentation and syntax")

            return suggestions

        except Exception as e:
            logging.error(f"Error suggesting fix for line: {str(e)}")
            return [f"Error analyzing line: {str(e)}"]


    def explain_code(self, code_segment):
        try:
            if not code_segment or code_segment.strip() == "":
                return "No code provided to explain."

            prompt = (
                f"Explain the following Python code in simple terms:\n\n"
                f"```python\n{code_segment}\n```\n\n"
                "Provide a concise explanation that covers:\n"
                "1. What the code does\n"
                "2. How it works\n"
                "3. Any potential issues or improvements\n"
            )

            explanation = analyze_code_with_llm(
                prompt,
                model_name=self.llm_model,
                max_length=max(500, self.max_length * 2)
            )

            if not explanation or explanation.strip() == "":
                return "Could not generate an explanation for the provided code."

            return explanation

        except Exception as e:
            logging.error(f"Error explaining code: {str(e)}")
            return f"Error generating explanation: {str(e)}"


    def auto_fix_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            analysis = self.analyze_file(file_path)

            if not analysis or not analysis.get('errors') or len(analysis.get('errors', [])) == 0:
                return original_code, []

            errors_by_line = {}
            for error in analysis.get('errors', []):
                if 'line' in error:
                    line = error.get('line', 0)
                    if line not in errors_by_line:
                        errors_by_line[line] = []
                    errors_by_line[line].append(error)

            if not errors_by_line:
                prompt = (
                    f"Fix all syntax and logical errors in the following Python code:\n\n"
                    f"```python\n{original_code}\n```\n\n"
                    "Return only the corrected code without explanations."
                )

                fixed_code = analyze_code_with_llm(
                    prompt,
                    model_name=self.llm_model,
                    max_length=max(len(original_code) * 2, self.max_length)
                )

                code_match = re.search(r'```(?:python)?\n(.*?)\n```', fixed_code, re.DOTALL)
                if code_match:
                    fixed_code = code_match.group(1)

                changes = [{
                    "type": "full_replacement",
                    "message": "Applied AI-generated fixes to the entire file"
                }]

                return fixed_code, changes

            lines = original_code.split('\n')
            changes = []

            for line_num in sorted(errors_by_line.keys()):
                idx = line_num - 1
                if idx < 0 or idx >= len(lines):
                    continue

                errors = errors_by_line[line_num]
                original_line = lines[idx]

                fix_suggestion = None
                for error in errors:
                    if 'fix_suggestion' in error:
                        fix_suggestion = error['fix_suggestion']
                        break

                if fix_suggestion:
                    lines[idx] = fix_suggestion
                    changes.append({
                        "line": line_num,
                        "original": original_line,
                        "fixed": fix_suggestion,
                        "message": errors[0].get('message', 'Fixed syntax error')
                    })
                else:
                    context_start = max(0, idx - 2)
                    context_end = min(len(lines), idx + 3)
                    context_code = '\n'.join(lines[context_start:context_end])

                    prompt = (
                        f"Fix the error on line {idx + 1} in this Python code:\n\n"
                        f"```python\n{context_code}\n```\n\n"
                        f"The specific line is: {original_line}\n\n"
                        f"Error: {errors[0].get('message', 'Unknown error')}\n\n"
                        "Return only the corrected line of code."
                    )

                    llm_fix = analyze_code_with_llm(
                        prompt,
                        model_name=self.llm_model,
                        max_length=self.max_length
                    )

                    if llm_fix:
                        llm_fix = llm_fix.replace('```python', '').replace('```', '')
                        fixed_line = next((line.strip() for line in llm_fix.split('\n') if line.strip()), '')

                        if fixed_line and fixed_line != original_line:
                            lines[idx] = fixed_line
                            changes.append({
                                "line": line_num,
                                "original": original_line,
                                "fixed": fixed_line,
                                "message": errors[0].get('message', 'Fixed with AI assistance')
                            })

            fixed_code = '\n'.join(lines)
            return fixed_code, changes

        except Exception as e:
            logging.error(f"Auto-fix failed: {str(e)}")
            raise


    def _prioritize_errors(self, errors: list) -> list:
        priority_order = {"Syntax Error": 1, "Runtime Error": 2, "Pylint Analysis": 3,
                          "Static Analysis": 4, "LLM Analysis": 5}
        return sorted(errors, key=lambda x: priority_order.get(x.get("issue", ""), 999))


    def _consolidate_fixes(self, errors: list) -> dict:
        fixes = {}
        for error in errors:
            if "fix_suggestion" in error:
                line = error.get("line", 0)
                if line not in fixes:
                    fixes[line] = []
                fixes[line].append(error["fix_suggestion"])
        return fixes


    def _cross_validate_analysis(self, syntax_err, runtime_err, static_issues, llm_analysis, pylint_analysis):
        validated_issues = []

        if syntax_err:
            syntax_err_copy = syntax_err.copy() if isinstance(syntax_err, dict) else {"message": str(syntax_err)}
            syntax_err_copy["confidence"] = "High"
            validated_issues.append(syntax_err_copy)

        if runtime_err:
            runtime_err_copy = runtime_err.copy() if isinstance(runtime_err, dict) else {"message": str(runtime_err)}
            runtime_err_copy["confidence"] = "High"
            validated_issues.append(runtime_err_copy)

        issues_by_line = {}

        if isinstance(pylint_analysis, dict) and isinstance(pylint_analysis.get('errors'), list):
            for error in pylint_analysis['errors']:
                if isinstance(error, dict) and "line" in error:
                    line = error.get("line", 0)
                    if line not in issues_by_line:
                        issues_by_line[line] = []
                    issues_by_line[line].append({"source": "pylint", "details": error})

        if isinstance(llm_analysis, dict) and "line" in llm_analysis:
            line = llm_analysis.get("line", 0)
            if line not in issues_by_line:
                issues_by_line[line] = []
            issues_by_line[line].append({"source": "llm", "details": llm_analysis})

        for line, detections in issues_by_line.items():
            if len(detections) > 1:
                for detection in detections:
                    issue = detection["details"].copy()
                    issue["confidence"] = "High"
                    issue["cross_validated"] = True
                    validated_issues.append(issue)
            else:
                issue = detections[0]["details"].copy()
                issue["confidence"] = "Medium"
                validated_issues.append(issue)

        if static_issues:
            for issue in static_issues:
                issue_copy = issue.copy() if isinstance(issue, dict) else {"message": str(issue)}
                issue_copy["confidence"] = "Medium"
                validated_issues.append(issue_copy)

        return validated_issues


    def _generate_report(self, file_path: str, errors: dict) -> str:
        report = f"Debug Report for {file_path}\n"
        report += "=" * 50 + "\n\n"

        if not errors or not errors.get("errors"):
            report += "No issues detected!\n"
            return report

        total_issues = len(errors.get("errors", []))
        report += f"Summary: Found {total_issues} issue(s)\n\n"

        issue_types = {}
        for error in errors.get("errors", []):
            issue_type = error.get("issue", "Unknown")
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        report += "Issue breakdown:\n"
        for issue_type, count in issue_types.items():
            report += f"- {issue_type}: {count}\n"
        report += "\n"

        report += "Detailed Issues:\n" + "-" * 50 + "\n\n"
        for i, error in enumerate(errors.get("errors", [])):
            report += f"Issue #{i + 1}: {error.get('issue', 'Unknown')}\n"

            if "confidence" in error:
                confidence = error.get("confidence")
                report += f"Confidence: {confidence}"
                if error.get("cross_validated"):
                    report += " (cross-validated by multiple analyzers)\n"
                else:
                    report += "\n"

            report += f"Message: {error.get('message', 'No details')}\n"

            if "line" in error:
                report += f"Line: {error['line']}\n"
            if "fix_suggestion" in error:
                report += "Suggested fix:\n"
                report += f"```python\n{error['fix_suggestion']}\n```\n"

            report += "-" * 40 + "\n"

        report += "\nRecommended actions:\n"
        report += "- Start by addressing high confidence issues first\n"
        report += "- Cross-validated issues should be prioritized\n"
        report += "- Run the debugger again after fixing issues to verify changes\n"

        return report


def prioritize_errors(errors):
    return Debugger._prioritize_errors(errors)


def consolidate_fixes(errors):
    return Debugger._consolidate_fixes(errors)


def cross_validate_analysis(syntax_err, runtime_err, static_issues, llm_analysis, pylint_analysis):
    return Debugger()._cross_validate_analysis(syntax_err, runtime_err, static_issues, llm_analysis, pylint_analysis)