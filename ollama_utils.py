import os
import requests

HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_CHAT_URL = "https://api-inference.huggingface.co/v1/chat/completions"

def _call_huggingface_chat(messages: list) -> str:
    if not HF_API_KEY:
        return "Error: HF_API_KEY not set."
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "microsoft/Phi-3-mini-4k-instruct",
        "messages": messages
    }
    try:
        resp = requests.post(HF_CHAT_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

def explain_contract(code: str) -> str:
    return _call_huggingface_chat([
        {"role": "system", "content": "You are a smart contract expert. Explain Solidity code concisely."},
        {"role": "user", "content": code}
    ])

def chat_evm(user_input: str) -> str:
    return _call_huggingface_chat([
        {"role": "system", "content": "You are an EVM chatbot. Be concise and helpful."},
        {"role": "user", "content": user_input}
    ])
