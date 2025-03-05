import subprocess
import json
from typing import Dict, Any


def analyze_code_with_pylint(file_path: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "pylint",
                "--output-format=json",
                file_path
            ],
            capture_output=True,
            text=True,
            check=False
        )

        if result.stdout.strip():
            try:
                pylint_issues = json.loads(result.stdout)
                errors = []
                for issue in pylint_issues:
                    errors.append({
                        "line": issue.get("line", 0),
                        "column": issue.get("column", 0),
                        "message": issue.get("message", ""),
                        "message-id": issue.get("message-id", ""),
                        "symbol": issue.get("symbol", ""),
                        "fix_suggestion": f"Fix {issue.get('symbol', '')} issue: {issue.get('message', '')}"
                    })
                return {"errors": errors, "output": result.stdout}
            except json.JSONDecodeError:
                return {"errors": [{"message": f"Failed to parse pylint output: {result.stdout}"}],
                        "output": result.stdout}
        else:
            return {"errors": [], "output": "No issues found by pylint"}

    except Exception as e:
        return {"errors": [{"message": f"Pylint analysis error: {str(e)}"}], "output": f"Error: {str(e)}"}