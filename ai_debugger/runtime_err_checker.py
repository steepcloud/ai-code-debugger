import subprocess
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def detect_runtime_error(file_path: str) -> dict:
    try:
        result = subprocess.run(['python', file_path], capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Runtime Error: {result.stderr}")
            return {
                "error": "Runtime Error",
                "message": result.stderr,
                "fix_suggestion": get_runtime_fix_suggestion(result.stderr)
            }
        logging.info("No runtime errors detected.")
        return {}
    except Exception as e:
        logging.exception(f"Unexpected error occurred while running file {file_path}: {e}")
        return {
            "error": "Unexpected Error",
            "message": str(e)
        }

def get_runtime_fix_suggestion(error_message: str) -> str:
    if "ZeroDivisionError" in error_message:
        return "Suggestion: Check if the denominator is zero before division."
    elif "NameError" in error_message:
        return "Suggestion: Check for undefined variables or misspelled variable names."
    elif "TypeError" in error_message:
        return "Suggestion: Check for incorrect data types or function arguments."
    elif "IndexError" in error_message:
        return "Suggestion: Check for out-of-range list or array indices."
    elif "KeyError" in error_message:
        return "Suggestion: Check for missing dictionary keys."
    elif "AttributeError" in error_message:
        return "Suggestion: Check for incorrect attribute references."
    return "No suggestion available."