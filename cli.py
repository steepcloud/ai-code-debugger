import argparse
import json
import sys
import logging
from pathlib import Path
from ai_debugger.syntax_checker import SyntaxChecker
from ai_debugger.runtime_err_checker import detect_runtime_error
from ai_debugger.utils import format_code, analyze_complexity
from ai_debugger.static_analyzer import StaticAnalyzer
from ai_debugger.debugger import analyze_file, analyze_changes
from ai_debugger.llm_analyzer import analyze_code_with_llm
from ai_debugger.pylint_analyzer import analyze_code_with_pylint


def main():
    parser = argparse.ArgumentParser(description="AI-powered Python code debugger.")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    check_parser = subparsers.add_parser('check', help='Basic syntax and runtime check')
    check_parser.add_argument("file_path", type=str, help="Path to the Python script file")
    check_parser.add_argument("--format", action="store_true", help="Format the code")
    check_parser.add_argument("--complexity", action="store_true", help="Analyze code complexity")
    check_parser.add_argument("--static", action="store_true", help="Perform static analysis")

    analyze_parser = subparsers.add_parser('analyze', help='Full analysis of a Python file')
    analyze_parser.add_argument('file_path', type=str, help='Path to the Python file to analyze')
    analyze_parser.add_argument('--report', action='store_true', help='Generate a detailed report')
    analyze_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    analyze_parser.add_argument('--no-llm', action='store_true', help='Skip LLM analysis')
    analyze_parser.add_argument('--model', type=str,
                                default='microsoft/CodeGPT-small-py',
                                help='Name of the model to use (default: microsoft/CodeGPT-small-py)')
    analyze_parser.add_argument('--max-length', type=int, default=150,
                                help='Maximum length of generated text for LLM analysis (default: 150)')

    diff_parser = subparsers.add_parser('diff', help='Analyze changes between two Python files')
    diff_parser.add_argument('old_file', type=str, help='Path to the original Python file')
    diff_parser.add_argument('new_file', type=str, help='Path to the updated Python file')
    diff_parser.add_argument('--json', action='store_true', help='Output in JSON format')

    llm_parser = subparsers.add_parser('llm', help='Analyze code with language model only')
    llm_parser.add_argument('file_path', type=str, help='Path to the Python file to analyze')
    llm_parser.add_argument('--model', type=str,
                            default='microsoft/CodeGPT-small-py',
                            help='Name of the model to use (default: microsoft/CodeGPT-small-py)')
    llm_parser.add_argument('--max-length', type=int, default=150,
                            help='Maximum length of generated text (default: 150)')

    parser.add_argument("--log", type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

    args = parser.parse_args()

    if args.log:
        logging.basicConfig(level=getattr(logging, args.log),
                            format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    if args.command == 'check':
        if args.format:
            formatted_output = format_code(args.file_path)
            print(formatted_output)

        if args.complexity:
            complexity_output = analyze_complexity(args.file_path)
            print(complexity_output)

        if args.static:
            try:
                with open(args.file_path, "r", encoding="utf-8") as file:
                    code = file.read()
                static_issues = StaticAnalyzer.analyze_code(code)
                if static_issues:
                    for issue in static_issues:
                        line_info = f"at line {issue.get('line', 'unknown')}" if 'line' in issue else ""
                        print(f"{issue['issue']}: {issue['message']} {line_info}")
                else:
                    print("No static issues found.")
            except Exception as e:
                print(f"Error analyzing file: {e}")

        error = SyntaxChecker.analyze_file(args.file_path)
        if error:
            print(f"Syntax Error: {error['message']} at line {error.get('line', '?')}")
            if 'fix_suggestion' in error:
                print(f"Suggestion: {error['fix_suggestion']}")
        else:
            runtime_error = detect_runtime_error(args.file_path)
            if runtime_error:
                print(f"Runtime Error: {runtime_error['message']}")
                if 'fix_suggestion' in runtime_error:
                    print(f"Suggestion: {runtime_error['fix_suggestion']}")
            else:
                print("No syntax or runtime errors found in the script.")


    elif args.command == 'analyze':
        file_path = args.file_path

        if not Path(file_path).exists():
            print(f"Error: File '{file_path}' not found", file=sys.stderr)
            sys.exit(1)

        print(f"Analyzing {file_path}...")
        result = analyze_file(file_path, should_generate_report=args.report, llm_model=args.model,
                              max_length=args.max_length)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if "errors" in result and result["errors"]:
                print(f"\nFound {len(result['errors'])} issues:")
                for i, error in enumerate(result["errors"], 1):
                    issue_type = error.get("issue", "Unknown")
                    message = error.get("message", "No details")
                    line = error.get("line", "Unknown")
                    print(f"{i}. {issue_type} at line {line}: {message}")

                    if "fix_suggestion" in error:
                        print(f"   Suggested fix: {error['fix_suggestion']}")
            else:
                print("No issues found!")

            if "validated_issues" in result and result["validated_issues"]:
                print("\nValidated Issues:")
                for issue in result["validated_issues"]:
                    confidence = issue.get("confidence", "Unknown")
                    message = issue.get("message", "No details")
                    print(f"- [{confidence}] {message}")

            if "report" in result:
                print("\n" + "=" * 40)
                print("DETAILED REPORT")
                print("=" * 40)
                print(result["report"])

    elif args.command == 'diff':
        old_file = args.old_file
        new_file = args.new_file

        if not Path(old_file).exists():
            print(f"Error: File '{old_file}' not found", file=sys.stderr)
            sys.exit(1)

        if not Path(new_file).exists():
            print(f"Error: File '{new_file}' not found", file=sys.stderr)
            sys.exit(1)

        print(f"Analyzing changes between {old_file} and {new_file}...")
        changes = analyze_changes(old_file, new_file)

        if args.json:
            print(json.dumps(changes, indent=2))
        else:
            added = len(changes["added_lines"])
            removed = len(changes["removed_lines"])
            total = len(changes["changed_lines"])

            print(f"\nChanges detected: {total} total ({added} additions, {removed} removals)")
            print("\nModified lines:")
            for line_num in sorted(changes["lines_info"].keys()):
                info = changes["lines_info"][line_num]
                change_type = info["change_type"]
                content = info["content"]
                marker = "+" if change_type == "addition" else "-"
                print(f"{marker} Line {line_num}: {content}")

    elif args.command == 'llm':
        file_path = args.file_path

        if not Path(file_path).exists():
            print(f"Error: File '{file_path}' not found", file=sys.stderr)
            sys.exit(1)

        try:
            print(f"Analyzing {file_path} with language model {args.model}...")
            with open(file_path, "r", encoding="utf-8") as file:
                code = file.read()

            analysis = analyze_code_with_llm(code, model_name=args.model, max_length=args.max_length)
            print("\nLanguage Model Analysis:")
            print(analysis)
        except Exception as e:
            print(f"Error during LLM analysis: {e}", file=sys.stderr)
            print("Make sure you have the required dependencies installed:")
            print("pip install transformers torch")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()