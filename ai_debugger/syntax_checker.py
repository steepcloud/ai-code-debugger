import ast
import logging
import re

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class SyntaxChecker:
    @staticmethod
    def check_syntax(code: str) -> dict:
        try:
            ast.parse(code)
            logging.info("Code syntax is correct.")
            return {}
        except SyntaxError as e:
            logging.error(f"Syntax Error: {e.msg} at line {e.lineno}, column {e.offset}")
            return {
                "error": "Syntax Error",
                "message": e.msg,
                "line": e.lineno,
                "column": e.offset,
                "fix_suggestion": SyntaxChecker.get_fix_suggestion(e)
            }


    @staticmethod
    def analyze_file(fpath: str) -> dict:
        try:
            with open(fpath, "r", encoding="utf-8") as file:
                code = file.read()
            compile(code, fpath, 'exec')
            logging.info(f"File {fpath} parsed successfully.")
        except SyntaxError as e:
            logging.error(f"Syntax Error in {fpath}: {e.msg} at line {e.lineno}, column {e.offset}")
            return {
                "error": "Syntax Error",
                "line": e.lineno,
                "column": e.offset,
                "message": e.msg,
                "fix_suggestion": SyntaxChecker.get_fix_suggestion(e)
            }
        except Exception as e:
            logging.exception(f"Unexpected error occurred while analyzing file {fpath}: {e}")
            return {
                "error": "Unexpected Error",
                "message": str(e)
            }
        return {}


    @staticmethod
    def analyze_line(line, line_number):
        issues = []

        if re.search(r'\b(if|elif|else|def|class|for|while|try|except|finally)\b.*\s*$', line) and not line.endswith(
                ':'):
            return {
                "issue": "Syntax Error",
                "line": line_number + 1,
                "message": "Missing colon at the end of statement",
                "fix_suggestion": f"{line}:"
            }

        quote_chars = ["'", '"', '"""', "'''"]
        for quote in quote_chars:
            if line.count(quote) % 2 == 1:
                return {
                    "issue": "Syntax Error",
                    "line": line_number + 1,
                    "message": f"Mismatched {quote} quotes",
                    "fix_suggestion": f"{line}{quote}"
                }

        if ('if ' in line or 'while ' in line) and '=' in line and '==' not in line and '!=' not in line:
            fixed = line.replace('=', '==', 1)
            return {
                "issue": "Syntax Error",
                "line": line_number + 1,
                "message": "Using assignment (=) instead of comparison (==) in condition",
                "fix_suggestion": fixed
            }

        return None


    @staticmethod
    def get_fix_suggestion(error) -> str:
        if "expected ':'" in error.msg:
            return "Suggestion: Add a colon ':' at the end of the line."
        elif "invalid syntax" in error.msg:
            return "Suggestion: Check for missing or misplaced characters."
        elif "unexpected indent" in error.msg:
            return "Suggestion: Check for consistent indentation (use spaces, not tabs)."
        elif "EOF in multi-line statement" in error.msg:
            return "Suggestion: Check for properly closed parentheses, brackets, or quotes."
        #TODO: add more suggestions
        return "No suggestion available."

