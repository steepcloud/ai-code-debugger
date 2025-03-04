import argparse
from ai_debugger.syntax_checker import SyntaxChecker
from ai_debugger.runtime_err_checker import detect_runtime_error
from ai_debugger.utils import format_code, analyze_complexity
from ai_debugger.static_analyzer import StaticAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Check the syntax of a Python script.")
    parser.add_argument("file_path", type=str, help="Path to the Python script file")
    parser.add_argument("--format", action="store_true", help="Format the code")
    parser.add_argument("--complexity", action="store_true", help="Analyze code complexity")
    parser.add_argument("--static", action="store_true", help="Perform static analysis")
    parser.add_argument("--log", type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")
    args = parser.parse_args()

    if args.log:
        import logging
        logging.basicConfig(level=getattr(logging, args.log), format='%(asctime)s - %(levelname)s - %(message)s')
    if args.format():
        formatted_output = format_code(args.file_path)
        print(formatted_output)
    if args.complexity:
        complexity_output = analyze_complexity(args.file_path)
        print(complexity_output)
    if args.static:
        with open(args.file_path, "r", encoding="utf-8") as file:
            code = file.read()
        static_issues = StaticAnalyzer.analyze_code(code)
        for issue in static_issues:
            print(f"{issue['issue']}: {issue['message']} at line {issue['line']}")

    error = SyntaxChecker.analyze_file(args.file_path)
    if error:
        print(f"Syntax Error: {error['message']} at line {error['line']}, column {error['column']}")
        if 'fix_suggestion' in error:
            print(error['fix_suggestion'])
    else:
        runtime_error = detect_runtime_error(args.file_path)
        if runtime_error:
            print(f"Runtime Error: {runtime_error['message']}")
            if 'fix_suggestion' in runtime_error:
                print(runtime_error['fix_suggestion'])
        else:
            print("No syntax errors found in the script.")

if __name__ == "__main__":
    main()