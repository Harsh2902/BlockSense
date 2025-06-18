import json
import requests  # Import requests for making HTTP calls
import os  # Import os to access environment variables

# NOTE: The Hugging Face API token MUST be set as an environment variable
# on your hosting platform (e.g., Render). DO NOT hardcode it here.
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")  # Fetch from environment, default to empty string if not found

# Hugging Face Inference API endpoint for a generally accessible generative model.
# Changed to 'gpt2' as 'google/gemma-2b-it' and 'google/gemma-2-2b-it' caused 404 errors,
# indicating they might not be publicly available via the standard Inference API.
HF_INFERENCE_API_URL = "https://api-inference.huggingface.co/models/gpt2"


def _call_huggingface_api(messages: list) -> str:
    """Internal helper to call the Hugging Face Inference API."""
    if not HF_API_TOKEN:
        return "Error: Hugging Face API token not found. Please set the HF_API_TOKEN environment variable."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # For general generative models like GPT-2, the API expects a single string prompt.
    # We'll concatenate the messages into a single prompt string.
    final_prompt = ""
    system_message = ""
    user_message = ""

    for message in messages:
        if message["role"] == "system":
            system_message = message["content"]
        elif message["role"] == "user":
            user_message = message["content"]

    # Structure the prompt for a general generative model.
    # You might need to refine this prompt engineering based on the specific model's fine-tuning.
    if system_message:
        final_prompt = f"System instruction: {system_message}\nUser query: {user_message}\nAI Response:"
    else:
        final_prompt = f"User query: {user_message}\nAI Response:"

    payload = {
        "inputs": final_prompt,
        "parameters": {
            "max_new_tokens": 200,  # Adjust as needed, GPT-2 is smaller
            "temperature": 0.7,
            "do_sample": True,
            # Removed "return_full_text": False to avoid potential API compatibility issues
        },
        "options": {
            "wait_for_model": True  # Important for free tier to avoid timeouts if model is not active
        }
    }

    try:
        response = requests.post(HF_INFERENCE_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()

        # Hugging Face Inference API for text generation usually returns a list of dictionaries,
        # with 'generated_text' being a common key for the result.
        if isinstance(result, list) and result and result[0].get('generated_text'):
            generated_text = result[0]['generated_text'].strip()
            # Since return_full_text is removed, we might get the prompt back.
            # Attempt to strip the prompt from the generated text.
            if generated_text.startswith(final_prompt):
                return generated_text[len(final_prompt):].strip()
            return generated_text
        else:
            return f"No content generated from AI or unexpected response structure: {result}"
    except requests.exceptions.RequestException as e:
        return f"Error communicating with Hugging Face API: {e}. Ensure the model is available and your HF_API_TOKEN is correct and has sufficient permissions."
    except json.JSONDecodeError:
        return "Error parsing JSON response from Hugging Face API."
    except Exception as e:
        return f"An unexpected error occurred during Hugging Face API call: {e}"


def explain_contract(code: str) -> str:
    """
    Explains Solidity contract code using a Hugging Face generative model.
    """
    messages = [
        {"role": "system", "content": "You are a smart contract expert. Explain solidity code concisely."},
        {"role": "user", "content": code}
    ]
    return _call_huggingface_api(messages)


def chat_evm(user_input: str) -> str:
    """
    Analyzes transactions or generates web3 commands using a Hugging Face generative model.
    """
    messages = [
        {"role": "system",
         "content": "You are an EVM chatbot. You can analyze transactions or generate web3 commands, and answer general questions about EVM and blockchain. Be concise and helpful."},
        {"role": "user", "content": user_input}
    ]
    return _call_huggingface_api(messages)

