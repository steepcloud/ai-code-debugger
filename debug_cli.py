import os
import sys
import argparse
from ai_debugger.debugger import Debugger


def main():
    parser = argparse.ArgumentParser(description="Test step_into and step_out functionality")
    parser.add_argument("file", help="File to debug")
    parser.add_argument("--analyze", "-a", action="store_true", help="Perform analysis before debugging")
    args = parser.parse_args()

    file_path = args.file
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found!")
        sys.exit(1)

    debugger = Debugger()

    if args.analyze:
        print(f"Analyzing {file_path}...")
        analysis = debugger.analyze_file(file_path)
        if "errors" in analysis and analysis["errors"]:
            print("\nAnalysis found issues:")
            for error in analysis["errors"][:3]:
                print(f"- {error.get('issue', 'Issue')}: {error.get('message', 'No details')}")
        else:
            print("No issues found in static analysis")

    debugger.current_file = file_path
    debugger.current_line = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        code_lines = f.readlines()

    print(f"Loaded file: {file_path} ({len(code_lines)} lines)")
    print("\nDebugger Commands:")
    print("  n - Step over to next line")
    print("  s - Step into function")
    print("  o - Step out of function")
    print("  b <line> - Set breakpoint")
    print("  c - Continue to next breakpoint or end")
    print("  p <var> - Print variable value")
    print("  stack - Show full call stack")
    print("  vars - Show all variables")
    print("  q - Quit")

    running = True
    while running:
        start_line = max(0, debugger.current_line - 2)
        end_line = min(len(code_lines), debugger.current_line + 3)

        print("\nCode context:")
        for i in range(start_line, end_line):
            if i < len(code_lines):
                bp_marker = "*" if (debugger.breakpoints.get(file_path, []) and i in debugger.breakpoints.get(file_path,
                                                                                                              [])) else " "
                cursor = "→" if i == debugger.current_line else " "
                print(f"{bp_marker}{cursor}{i + 1:4d}: {code_lines[i].rstrip()}")

        if debugger.call_stack:
            print("\nCall stack:")
            for i, frame in enumerate(debugger.call_stack):
                file = os.path.basename(frame.get('file', 'unknown'))
                line = frame.get('line', 0) + 1
                function = frame.get('function', 'unknown')
                print(f"  #{i}: {function}() at line {line} in {file}")

        cmd = input("\nDebug> ").strip().lower()

        if cmd == 'n':
            debugger.current_line += 1
            if debugger.current_line >= len(code_lines):
                print("End of file reached")
                running = False
            else:
                print(f"Stepped to line {debugger.current_line + 1}")
        elif cmd == 's':
            if debugger.step_into():
                print(f"Stepped into function at line {debugger.current_line + 1}")
            else:
                print("No function call found at current line")
                debugger.current_line += 1
        elif cmd == 'o':
            if debugger.step_out():
                print(f"Stepped out to line {debugger.current_line + 1}")
            else:
                print("Cannot step out - not inside a function call")
                debugger.current_line += 1
        elif cmd.startswith('b '):
            try:
                line_num = int(cmd.split()[1]) - 1
                if 0 <= line_num < len(code_lines):
                    debugger.set_breakpoint(file_path, line_num)
                    print(f"Breakpoint set at line {line_num + 1}")
                else:
                    print("Line number out of range")
            except (ValueError, IndexError):
                print("Invalid breakpoint command. Use 'b <line_number>'")
        elif cmd == 'c':
            next_bp = None
            if file_path in debugger.breakpoints:
                for bp in sorted(debugger.breakpoints[file_path]):
                    if bp > debugger.current_line:
                        next_bp = bp
                        break

            if next_bp:
                print(f"Continuing to breakpoint at line {next_bp + 1}")
                debugger.current_line = next_bp
            else:
                print("No breakpoint ahead, continuing to end")
                debugger.current_line = len(code_lines) - 1
        elif cmd.startswith('p '):
            var_name = cmd.split(maxsplit=1)[1].strip()
            value = debugger.inspect_variable(var_name)
            if value is not None:
                print(f"{var_name} = {value}")
            else:
                print(f"Variable '{var_name}' not found")
        elif cmd == 'stack':
            if not debugger.call_stack:
                print("Call stack is empty")
            else:
                for i, frame in enumerate(debugger.call_stack):
                    file = os.path.basename(frame.get('file', 'unknown'))
                    line = frame.get('line', 0) + 1
                    function = frame.get('function', 'unknown')
                    print(f"  #{i}: {function}() at line {line} in {file}")
        elif cmd == 'vars':
            if not debugger.variables:
                print("No variables in current scope")
            else:
                for name, value in debugger.variables.items():
                    print(f"  {name} = {value}")
        elif cmd == 'q':
            running = False
            print("Debugging session ended")
        else:
            print("Unknown command")


if __name__ == "__main__":
    main()