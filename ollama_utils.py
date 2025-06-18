import os
import requests

HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

def _call_huggingface(prompt: str) -> str:
    if not HF_API_KEY:
        return "Error: Hugging Face API key not found. Please set HF_API_KEY as an environment variable."

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.7,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(HF_MODEL_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        # The response is usually a list with one dict containing 'generated_text'
        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        else:
            return f"Unexpected Hugging Face response: {result}"
    except requests.exceptions.RequestException as e:
        return f"Error communicating with Hugging Face API: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

def explain_contract(code: str) -> str:
    prompt = f"You are a smart contract expert. Explain the following Solidity code concisely:\n\n{code}"
    return _call_huggingface(prompt)

def chat_evm(user_input: str) -> str:
    prompt = f"You are an EVM chatbot. Answer concisely:\n\n{user_input}"
    return _call_huggingface(prompt)
