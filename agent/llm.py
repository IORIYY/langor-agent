import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import ollama

MODEL_NAME = "qwen2.5:7b"


def call_llm(prompt: str, temperature: float = 0.1) -> str:
    """调用 Qwen2.5 7B，返回文本"""
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": temperature}
    )
    return response["message"]["content"]
