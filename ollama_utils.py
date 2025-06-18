import os, requests
import json  # Import json for JSONDecodeError

# Hugging Face Inference API endpoint for microsoft/Phi-3-mini-4k-instruct
# This model is generally available on Hugging Face's free tier.
HF_API_KEY = os.getenv("HF_API_KEY", "")
MODEL_URL = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"


def _call_api(prompt, model_id="microsoft/Phi-3-mini-4k-instruct"):
    """
    Calls the Hugging Face Inference API.
    """
    headers = {
        "Content-Type": "application/json",
    }
    if not HF_API_KEY:
        return "Error: HF_API_KEY missing. Please set your Hugging Face API key."
    headers["Authorization"] = f"Bearer {HF_API_KEY}"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1000,  # Kept increased max_new_tokens for detailed responses
            "temperature": 0.7,
            "top_p": 0.9,
        },
        "options": {
            "wait_for_model": True  # Useful for initial calls to a new model
        }
    }

    try:
        resp = requests.post(MODEL_URL, headers=headers, json=payload)

        # --- DEBUGGING ADDITION ---
        print(f"\nDEBUG: Hugging Face API Response Status Code: {resp.status_code}")
        print(f"DEBUG: Hugging Face API Raw Response Text: {resp.text}\n")
        # --- END DEBUGGING ADDING ---

        resp.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        try:
            out = resp.json()
        except json.JSONDecodeError as e:
            return (f"Error decoding JSON response from Hugging Face API: {e}. "
                    f"Raw response was: '{resp.text}'. This often means the API returned a non-JSON error. "
                    "Please double-check your API key and request parameters against Hugging Face documentation.")

        # Hugging Face API's response structure typically returns a list of dictionaries
        if isinstance(out, list) and out and 'generated_text' in out[0]:
            return out[0].get("generated_text", str(out))

        return f"Unexpected API response format from Hugging Face: {str(out)}"

    except requests.exceptions.RequestException as e:
        return (f"Error calling Hugging Face API: {str(e)}. "
                f"Please double-check your `MODEL_URL` ({MODEL_URL}), "
                "API key (`HF_API_KEY`), and consult the official Hugging Face API documentation for exact requirements.")
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


def explain_contract(code):
    # The updated prompt string to request a line-by-line explanation
    initial_prompt = (
        "You are a Solidity expert. Provide a detailed, line-by-line explanation of the following smart contract code. "
        "For each line or distinct code block, explain its purpose and functionality. "
        "Do not repeat the question. Just give the explanation directly:\n\n"
    )

    # Full prompt sent to the model
    full_prompt_sent = initial_prompt + code.strip()

    # Call the Hugging Face model
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
