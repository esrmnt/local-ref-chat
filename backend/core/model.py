import requests
from typing import Dict, Any
from backend.settings import settings
from backend.logging_config import get_logger

logger = get_logger(__name__)

def check_ollama_health() -> bool:
    """Check if Ollama service is available."""
    try:
        # Use a simple endpoint to check if Ollama is running
        health_url = settings.OLLAMA_API_URL.replace('/api/generate', '/api/tags')
        response = requests.get(health_url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        return False

def get_ollama_answer(prompt: str, stream: bool = False) -> Dict[str, Any]:
    """
    Send a prompt to the Ollama local LLM and return the response as JSON.
    
    Args:
        prompt (str): The full formatted prompt to send
        stream (bool): Whether to use streaming output from Ollama
        
    Returns:
        dict: Response from Ollama
        
    Raises:
        requests.RequestException: If the request to Ollama fails
        ValueError: If the response is invalid
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt.strip(),
        "stream": stream
    }
    
    try:
        logger.info(f"Sending request to Ollama with model: {settings.OLLAMA_MODEL}")
        
        response = requests.post(
            settings.OLLAMA_API_URL, 
            json=payload,
            timeout=settings.OLLAMA_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        if not isinstance(result, dict):
            raise ValueError("Invalid response format from Ollama")
        
        logger.info("Successfully received response from Ollama")
        return result
        
    except requests.exceptions.Timeout:
        logger.error(f"Ollama request timed out after {settings.OLLAMA_TIMEOUT} seconds")
        raise requests.RequestException("Ollama request timed out")
    
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Ollama service")
        raise requests.RequestException("Cannot connect to Ollama service")
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"Ollama HTTP error: {e}")
        raise requests.RequestException(f"Ollama service error: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error calling Ollama: {e}")
        raise
