def detect_runtime_error(file_path: str) -> dict:
    try:
        with open(file_path, "r") as file:
            code = file.read()
        exec(code)
    except ZeroDivisionError:
        return {
            "error": "Runtime Error",
            "message": "division by zero",
            "fix_suggestion": "Suggestion: Check if the denominator is zero before division."
        }
    except Exception as e:
        return {
            "error": "Runtime Error",
            "message": str(e),
            "fix_suggestion": "Suggestion: Investigate the error further."
        }
    return {}