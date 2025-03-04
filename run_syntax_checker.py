import argparse
from ai_debugger.syntax_checker import SyntaxChecker


def main():
    parser = argparse.ArgumentParser(description="Check the syntax of a Python script.")
    parser.add_argument("file_path", type=str, help="Path to the Python script file")
    args = parser.parse_args()

    error = SyntaxChecker.analyze_file(args.file_path)
    if error:
        print(f"Syntax Error: {error['message']} at line {error['line']}, column {error['column']}")
        if 'fix_suggestion' in error:
            print(error['fix_suggestion'])
    else:
        print("No syntax errors found in the script.")

if __name__ == "__main__":
    main()