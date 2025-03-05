class StaticAnalyzer:
    @staticmethod
    def analyze_code(code: str) -> list:
        import ast
        issues = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and (not node.body or
                                                          (len(node.body) == 1 and isinstance(node.body[0], ast.Pass))):
                    issues.append({
                        "issue": "Empty Function",
                        "message": f"Function '{node.name}' is empty",
                        "fix_suggestion": f"Implement function '{node.name}' or remove it"
                    })

                if isinstance(node, ast.ClassDef) and (not node.body or
                                                       (len(node.body) == 1 and isinstance(node.body[0], ast.Pass))):
                    issues.append({
                        "issue": "Empty Class",
                        "message": f"Class '{node.name}' is empty",
                        "fix_suggestion": f"Implement class '{node.name}' or remove it"
                    })

            return issues

        except SyntaxError as e:
            return [{
                "issue": "Syntax Error",
                "line": e.lineno,
                "message": str(e),
                "fix_suggestion": "Fix syntax error"
            }]
