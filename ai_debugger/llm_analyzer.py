from transformers import pipeline

def analyze_code_with_llm(code: str) -> str:
    code_analyzer = pipeline('text-generation', model='microsoft/CodeGPT-small-py')
    response = code_analyzer(code, max_length=150, num_return_sequences=1)
    return response[0]['generated_text']

