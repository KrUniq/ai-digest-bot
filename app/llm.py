import requests
from app.config import OLLAMA_URL

def call_ollama(prompt: str, model: str, num_predict: int = 700, timeout: int = 240) -> str:
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": num_predict,
                "top_p": 0.9,
            },
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["response"].strip()
