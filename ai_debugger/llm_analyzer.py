from transformers import pipeline


def analyze_code_with_llm(code: str, model_name='microsoft/CodeGPT-small-py', max_length=150) -> str:
    code_analyzer = pipeline('text-generation', model=model_name)
    response = code_analyzer(code, max_length=max_length, num_return_sequences=1, truncation=True)
    return response[0]['generated_text']