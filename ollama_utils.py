import json
import requests # Import requests for making HTTP calls
import os # Import os to access environment variables

# NOTE: The API key for Gemini is handled by the Canvas environment and should be left as an empty string.
# DO NOT add any API key validation logic here.
API_KEY = "" # Leave this empty. Canvas will provide it at runtime.
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def _call_gemini_api(messages: list) -> str:
    """Internal helper to call the Gemini API."""
    headers = {
        'Content-Type': 'application/json'
    }
    params = {
        'key': API_KEY
    }
    payload = {
        'contents': messages
    }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()

        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
            generated_content = result['candidates'][0]['content']['parts'][0]['text']
            return generated_content
        else:
            return f"No content generated from AI or unexpected response structure: {result}"
    except requests.exceptions.RequestException as e:
        return f"Error communicating with Gemini API: {e}. Please ensure the Generative Language API is enabled in your Google Cloud Project and your environment has access."
    except json.JSONDecodeError:
        return "Error parsing JSON response from Gemini API."
    except Exception as e:
        return f"An unexpected error occurred during Gemini API call: {e}"


def explain_contract(code: str) -> str:
    """
    Explains Solidity contract code using the Gemini AI model.
    """
    messages = [
        {"role": "system", "content": "You are a smart contract expert. Explain solidity code concisely."},
        {"role": "user", "content": code}
    ]
    return _call_gemini_api(messages)

def chat_evm(user_input: str) -> str:
    """
    Analyzes transactions or generates web3 commands using the Gemini AI model.
    """
    messages = [
        {"role": "system", "content": "You are an EVM chatbot. You can analyze transactions or generate web3 commands, and answer general questions about EVM and blockchain. Be concise and helpful."},
        {"role": "user", "content": user_input}
    ]
    return _call_gemini_api(messages)

