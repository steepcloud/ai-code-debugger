from setuptools import setup, find_packages

setup(
    name="ai-debugger",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "transformers",
        "torch",
        "pyyaml",
        "pylint",
        "black"
    ],
    entry_points={
        "console_scripts": [
            "ai-debugger=cli:main",
        ],
    },
    author="David Carboveanu",
    description="AI-powered Python code debugging and analysis tool",
    keywords="debugging, static analysis, AI, code quality",
    python_requires=">=3.8",
)