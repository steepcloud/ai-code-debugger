import ast


class StaticAnalyzer:
    @staticmethod
    def analyze_code(code: str) -> dict:
        issues = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and len(node.body) == 0:
                    issues.append({
                        "issue": "Empty Function",
                        "message": f"Function '{node.name}' is empty.",
                        "line": node.lineno
                    })
                elif isinstance(node, ast.ClassDef) and len(node.body) == 0:
                    issues.append({
                        "issue": "Empty Class",
                        "message": f"Class '{node.name}' is empty.",
                        "line": node.lineno
                    })
                elif isinstance(node, ast.Import) and not node.names:
                    issues.append({
                        "issue": "Empty Import",
                        "message": "Import statement is empty.",
                        "line": node.lineno
                    })
                elif isinstance(node, ast.Import) and not node.names:
                    issues.append({
                        "issue": "Empty Import",
                        "message": "Import statement is empty.",
                        "line": node.lineno
                    })
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'eval':
                    issues.append({
                        "issue": "Use of eval",
                        "message": "Use of 'eval' is discouraged due to security risks.",
                        "line": node.lineno
                    })
                #TODO: add more static analysis checks
        except SyntaxError as e:
            issues.append({
                "issue": "Syntax Error",
                "message": e.msg,
                "line": e.lineno,
                "column": e.offset
            })
        return issues