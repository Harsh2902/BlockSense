import json
import requests
import os

API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def _call_gemini_api(messages: list) -> str:
    if not API_KEY:
        return "Error: Gemini API key not found. Please set the GEMINI_API_KEY environment variable on your hosting platform."

    headers = {
        'Content-Type': 'application/json'
    }
    params = {
        'key': API_KEY
    }

    # Convert chat-style messages to Gemini API format
    formatted_messages = []
    for msg in messages:
        if msg["role"] == "system":
            # Gemini API doesn't support "system" role; can prepend it to user message or skip
            formatted_messages.insert(0, {
                "parts": [{"text": msg["content"]}]
            })
        elif msg["role"] == "user":
            formatted_messages.append({
                "parts": [{"text": msg["content"]}]
            })

    payload = {
        'contents': formatted_messages
    }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"No content generated or unexpected response: {result}"
    except requests.exceptions.RequestException as e:
        return f"Error communicating with Gemini API: {e}. Ensure the API is enabled and billing is set."
    except json.JSONDecodeError:
        return "Error parsing JSON response."
    except Exception as e:
        return f"Unexpected error during Gemini API call: {e}"

def explain_contract(code: str) -> str:
    messages = [
        {"role": "system", "content": "You are a smart contract expert. Explain solidity code concisely."},
        {"role": "user", "content": code}
    ]
    return _call_gemini_api(messages)

def chat_evm(user_input: str) -> str:
    messages = [
        {"role": "system", "content": "You are an EVM chatbot. You can analyze transactions or generate web3 commands, and answer general questions about EVM and blockchain. Be concise and helpful."},
        {"role": "user", "content": user_input}
    ]
    return _call_gemini_api(messages)
