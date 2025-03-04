import subprocess


def format_code(file_path: str) -> str:
    result = subprocess.run(['black', file_path], capture_output=True, text=True)
    return result.stdout

def analyze_complexity(file_path: str) -> str:
    result = subprocess.run(['radon', 'cc', file_path], capture_output=True, text=True)
    return result.stdout