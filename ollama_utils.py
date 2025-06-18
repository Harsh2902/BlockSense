import os, requests
import json  # Import json for JSONDecodeError

# Featherless AI endpoint for deepseek-ai/DeepSeek-R1-0528-Qwen3-8B
# IMPORTANT: This URL is based on a common LLM API pattern (like OpenAI's chat completions).
# Please verify Featherless AI's official documentation for the exact API endpoint.
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY", "")
MODEL_URL = "https://featherless.ai/v1/chat/completions"  # Changed to a common chat completions endpoint


def _call_api(prompt, model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"):
    """
    Calls the Featherless AI inference API using a chat completions pattern.
    """
    headers = {
        "Content-Type": "application/json",
    }
    if FEATHERLESS_API_KEY:
        headers["Authorization"] = f"Bearer {FEATHERLESS_API_KEY}"  # Ensure API key is correctly passed

    payload = {
        "model": model,
        "messages": [  # Changed 'input' to 'messages' for chat completions
            {"role": "user", "content": prompt}
        ],
        # Only popular sampler settings from the provided image
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": -1,  # Set to -1 to consider all tokens as per Featherless AI image
        "frequency_penalty": 0.0,  # Default to 0, adjust as needed
        "presence_penalty": 0.0,  # Default to 0, adjust as needed
        "repetition_penalty": 1.0,  # Default to 1.0 (no penalty), adjust as needed
        "min_p": 0.0  # Default to 0.0 (no minimum probability), adjust as needed
    }

    try:
        resp = requests.post(MODEL_URL, headers=headers, json=payload)

        # --- DEBUGGING ADDITION ---
        print(f"\nDEBUG: Featherless AI API Response Status Code: {resp.status_code}")
        print(f"DEBUG: Featherless AI API Raw Response Text: {resp.text}\n")
        # --- END DEBUGGING ADDITION ---

        resp.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        try:
            out = resp.json()
        except json.JSONDecodeError as e:
            return (f"Error decoding JSON response from Featherless AI: {e}. "
                    f"Raw response was: '{resp.text}'. This often means the API returned a non-JSON error or an empty response. "
                    "Please double-check your API key and request parameters against Featherless AI documentation.")

        # Featherless AI's response structure for chat completions should typically follow:
        # out['choices'][0]['message']['content']
        if isinstance(out, dict) and 'choices' in out and out['choices']:
            first_choice = out['choices'][0]
            if 'message' in first_choice and 'content' in first_choice['message']:
                return first_choice['message']['content']
            elif 'text' in first_choice:  # Fallback for older/different completion APIs
                return first_choice['text']

        return f"Unexpected API response format: {str(out)}"  # If parsing fails

    except requests.exceptions.RequestException as e:
        return (f"Error calling Featherless AI API: {str(e)}. "
                f"Please double-check your `MODEL_URL` ({MODEL_URL}), "
                "API key (`FEATHERLESS_API_KEY`), and consult the official Featherless AI API documentation for exact requirements.")
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


def explain_contract(code):
    # The original prompt string
    initial_prompt = (
        "You are a Solidity expert. Provide a concise explanation of the following smart contract code. "
        "Do not repeat the question. Just give the explanation directly:\n\n"
    )

    # Full prompt sent to the model
    full_prompt_sent = initial_prompt + code.strip()

    # Call the Featherless AI model
    raw_output = _call_api(full_prompt_sent)

    # --- Post-processing logic to remove unwanted parts ---
    # 1. Remove the initial prompt if it's repeated in the output
    if raw_output.startswith(initial_prompt):
        raw_output = raw_output[len(initial_prompt):].strip()

    # 2. Remove the input code block if it's repeated in the output
    # We use rstrip() for the code to handle potential trailing newlines and make matching robust
    if raw_output.startswith(code.strip()):
        raw_output = raw_output[len(code.strip()):].strip()

    # 3. Remove "## Solution:" header if present
    if raw_output.lower().startswith("## solution:"):
        raw_output = raw_output[len("## solution:"):].strip()
    elif raw_output.lower().startswith("solution:"):  # Also check for "Solution:" without "##"
        raw_output = raw_output[len("solution:"):].strip()

    # Ensure any leading/trailing whitespace is removed
    return raw_output.strip()


def chat_evm(user_input):
    prompt = (
        "You are an EVM assistant. Respond directly to the following request without repeating the question:\n\n"
        f"{user_input.strip()}"
    )
    return _call_api(prompt)
