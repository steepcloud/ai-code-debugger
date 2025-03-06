from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from ai_debugger.debugger import Debugger

app = Flask(__name__)
CORS(app)

sessions = {}


@app.route('/api/debugger/create', methods=['POST'])
def create_session():
    data = request.json
    if not data or 'file_path' not in data:
        return jsonify({"error": "Missing file_path parameter"}), 400

    file_path = data['file_path']
    if not os.path.exists(file_path):
        return jsonify({"error": f"File '{file_path}' not found"}), 404

    import uuid
    session_id = str(uuid.uuid4())

    debugger = Debugger()
    debugger.current_file = file_path
    debugger.current_line = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_lines = f.readlines()
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 500

    sessions[session_id] = {
        "debugger": debugger,
        "file_path": file_path,
        "code_lines": code_lines
    }

    return jsonify({
        "session_id": session_id,
        "file_path": file_path,
        "total_lines": len(code_lines),
        "current_line": 1
    })


@app.route('/api/debugger/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    session = sessions[session_id]
    debugger = session["debugger"]

    current_line = debugger.current_line
    code_lines = session["code_lines"]
    start_line = max(0, current_line - 2)
    end_line = min(len(code_lines), current_line + 3)

    context = []
    for i in range(start_line, end_line):
        if i < len(code_lines):
            is_current = i == current_line
            has_breakpoint = (debugger.breakpoints.get(session["file_path"], []) and
                              i in debugger.breakpoints.get(session["file_path"], []))
            context.append({
                "line_number": i + 1,
                "content": code_lines[i].rstrip(),
                "is_current": is_current,
                "has_breakpoint": has_breakpoint
            })

    call_stack = []
    if debugger.call_stack:
        for i, frame in enumerate(debugger.call_stack):
            call_stack.append({
                "index": i,
                "file": os.path.basename(frame.get('file', 'unknown')),
                "line": frame.get('line', 0) + 1,
                "function": frame.get('function', 'unknown')
            })

    variables = {}
    if debugger.variables:
        variables = debugger.variables

    return jsonify({
        "session_id": session_id,
        "file_path": session["file_path"],
        "current_line": current_line + 1,
        "context": context,
        "call_stack": call_stack,
        "variables": variables,
        "breakpoints": [bp + 1 for bp in debugger.breakpoints.get(session["file_path"], [])]
    })


@app.route('/api/debugger/<session_id>/analyze', methods=['GET'])
def analyze_session(session_id):
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    session = sessions[session_id]
    debugger = session["debugger"]
    file_path = session["file_path"]

    try:
        analysis = debugger.analyze_file(file_path)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route('/api/debugger/<session_id>/command', methods=['POST'])
def execute_command(session_id):
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    data = request.json
    if not data or 'command' not in data:
        return jsonify({"error": "Missing command parameter"}), 400

    command = data['command']
    session = sessions[session_id]
    debugger = session["debugger"]
    file_path = session["file_path"]
    code_lines = session["code_lines"]

    result = {"success": True, "message": ""}

    try:
        if command == 'step_over' or command == 'n':
            debugger.current_line += 1
            if debugger.current_line >= len(code_lines):
                result["message"] = "End of file reached"
                result["end_of_file"] = True
            else:
                result["message"] = f"Stepped to line {debugger.current_line + 1}"

        elif command == 'step_into' or command == 's':
            if debugger.step_into():
                result["message"] = f"Stepped into function at line {debugger.current_line + 1}"
            else:
                debugger.current_line += 1
                result["message"] = "No function call found at current line"

        elif command == 'step_out' or command == 'o':
            if debugger.step_out():
                result["message"] = f"Stepped out to line {debugger.current_line + 1}"
            else:
                debugger.current_line += 1
                result["message"] = "Cannot step out - not inside a function call"

        elif command.startswith('set_breakpoint '):
            try:
                line_num = int(command.split()[1]) - 1
                if 0 <= line_num < len(code_lines):
                    debugger.set_breakpoint(file_path, line_num)
                    result["message"] = f"Breakpoint set at line {line_num + 1}"
                else:
                    result["message"] = "Line number out of range"
                    result["success"] = False
            except (ValueError, IndexError):
                result["message"] = "Invalid breakpoint command. Use 'set_breakpoint <line_number>'"
                result["success"] = False

        elif command == 'continue' or command == 'c':
            next_bp = None
            if file_path in debugger.breakpoints:
                for bp in sorted(debugger.breakpoints[file_path]):
                    if bp > debugger.current_line:
                        next_bp = bp
                        break

            if next_bp:
                debugger.current_line = next_bp
                result["message"] = f"Continued to breakpoint at line {next_bp + 1}"
            else:
                debugger.current_line = len(code_lines) - 1
                result["message"] = "No breakpoint ahead, continued to end"

        elif command.startswith('inspect '):
            var_name = command.split(maxsplit=1)[1].strip()
            value = debugger.inspect_variable(var_name)
            if value is not None:
                result["message"] = f"{var_name} = {value}"
                result["variable"] = {
                    "name": var_name,
                    "value": value
                }
            else:
                result["message"] = f"Variable '{var_name}' not found"
                result["success"] = False

        else:
            result["message"] = "Unknown command"
            result["success"] = False

    except Exception as e:
        result["success"] = False
        result["message"] = f"Error executing command: {str(e)}"

    return jsonify(result)


@app.route('/api/debugger/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    del sessions[session_id]
    return jsonify({"success": True, "message": "Session deleted"})


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "active_sessions": len(sessions)})


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="AI Debugger API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")

    args = parser.parse_args()

    print(f"Starting AI Debugger API server on {args.host}:{args.port}")
    print("API Documentation:")
    print("- POST /api/debugger/create - Create a new debugging session")
    print("- GET /api/debugger/<session_id>/status - Get current session status")
    print("- POST /api/debugger/<session_id>/command - Execute a debugging command")
    print("- GET /api/debugger/<session_id>/analyze - Run analysis on the file")
    print("- DELETE /api/debugger/<session_id> - Delete a session")

    app.run(host=args.host, port=args.port, debug=args.debug)