import requests
from src.config import OLLAMA_API_URL, OLLAMA_MODEL

def get_ollama_answer(prompt: str, stream: bool = False):
    """
    Send a prompt to the Ollama local LLM and return the response as JSON.
    Args:
        prompt (str): The full formatted prompt to send
        stream (bool): Whether to use streaming output from Ollama
    Returns:
        dict: Response from Ollama
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": stream
    }
    response = requests.post(OLLAMA_API_URL, json=payload)
    response.raise_for_status()
    return response.json()
