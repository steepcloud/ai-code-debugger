# AI Code Debugger

An intelligent debugging assistant that combines traditional debugging with AI-powered code analysis to help developers identify and fix issues in their Python code.

## Features

- **Interactive Debugging**: Set breakpoints, step through code, and inspect variables
- **AI-Powered Analysis**: Detect errors and potential issues using static analysis and AI
- **Code Fix Suggestions**: Get intelligent suggestions to fix broken code
- **Auto-Fix Capability**: Automatically apply fixes to common syntax and logical errors
- **Code Explanation**: Get plain-English explanations of what your code does
- **User-Friendly Interface**: Web-based UI for easy debugging sessions

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/steepcloud/ai-code-debugger.git
   cd ai-code-debugger
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
You can use the AI Code Debugger in three different ways:

1. Web Interface (Recommended)
-> Start the debugging API server:
   ```bash
   python debug_api.py
   ```

-> Start a simple HTTP server to serve the UI (in a new terminal):
   ```bash
   python -m http.server (PORT)
   ```

-> Open your web browser and navigate to:
   ```bash
   http://localhost:{PORT}/debug_ui.html
   ```

-> Enter the path to the Python file you want to debug and click "Start Debugging"

-> Use the interactive controls to navigate through your code and use AI-powered features:
- Step Into/Over/Out: Navigate through code execution
- Set Breakpoint: Pause execution at specific lines
- Run Analysis: Detect errors and issues in your code
- Suggest Fix: Get AI-generated suggestions for fixing errors
- Explain Code: Get plain-English explanations of selected code
- Auto Fix: Automatically apply fixes to common errors

2. API Only (Programmatic Usage)
You can interact directly with the debugging API using curl or any HTTP client:

+ Start the debugging API server:
   ```bash
   python debug_api.py
   ```

+ Create a new debugging session:
   ```bash
   #Linux/macOS
   curl -X POST http://localhost:5000/api/debugger/create \
     -H "Content-Type: application/json" \
     -d '{"file_path": "tests/test_files/broken_script.py"}'
   ```
    
   # Windows (PowerShell)
   ```bash
   curl -Uri http://localhost:5000/api/debugger/create -Method POST \
     -Headers @{"Content-Type"="application/json"} \
     -Body '{"file_path": "tests/test_files/broken_script.py"}'
   ```
+ Use the returned `session_id` to interact with other API endpoints:
   ```bash
   curl http://localhost:5000/api/debugger/{session_id}/analyze
   ```
3. Command Line Interface
For quick analysis without starting a server, use the CLI (example usage):
   ```bash
   python cli.py --log DEBUG --log-file ai_debugger.log analyze tests/test_files/broken_script.py
   ```
Additional CLI options:
   ```bash
   # Get help on available commands
   python cli.py --help
   ```

## API Endpoints
The debugger provides several API endpoints for programmatic access:
- POST /api/debugger/create: create a new debugging session
- GET /api/debugger/{session_id}/status: Get current debugging status
- POST /api/debugger/{session_id}/command: Send a debugging command
- GET /api/debugger/{session_id}/analyze: Run code analysis
- GET /api/debugger/{session_id}/suggest_fix: Get fix suggestions

## Contributing
Contributions are welcome! Please feel free to submit a pull request. Here's how you can contribute to the project:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature-name`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature-name`)
5. Open a Pull Request
