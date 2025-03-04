import ast
import logging

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

