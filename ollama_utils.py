import os, requests

# Featherless AI endpoint for deepseek-ai/DeepSeek-R1-0528-Qwen3-8B
# Note: You might need to provide an API key specific to Featherless AI if required.
# Assuming API key is handled by the platform or is not strictly necessary for this endpoint.
# If an API key is needed, it would typically be passed in the headers or body.
# For now, let's keep HF_API_KEY for consistency in environment variable handling,
# but note that Featherless AI might use a different key name or system.
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY", "") # Renamed for clarity
MODEL_URL = "https://featherless.ai/api/v1/infer"

def _call_api(prompt, model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"):
    """
    Calls the Featherless AI inference API.
    """
    headers = {
        "Content-Type": "application/json",
    }
    if FEATHERLESS_API_KEY:
        headers["Authorization"] = f"Bearer {FEATHERLESS_API_KEY}"

    payload = {
        "model": model,
        "input": prompt,
        # Featherless AI might have specific parameters like max_tokens, temperature etc.
        # You may need to consult their API documentation for exact parameter names.
        "parameters": {
            "max_new_tokens": 300,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    try:
        resp = requests.post(MODEL_URL, headers=headers, json=payload)
        resp.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        out = resp.json()

        # Featherless AI's response structure might differ from Hugging Face.
        # Assuming a common structure where the generated text is under 'generated_text' or similar.
        # You may need to adjust this parsing based on actual Featherless AI response format.
        if isinstance(out, list) and out and 'generated_text' in out[0]:
            return out[0].get("generated_text", str(out))
        elif isinstance(out, dict) and 'generated_text' in out:
            return out.get("generated_text", str(out))
        elif isinstance(out, dict) and 'output' in out: # Common alternative for some APIs
            return out.get("output", str(out))
        else:
            return f"Unexpected API response format: {str(out)}"
    except requests.exceptions.RequestException as e:
        return f"Error calling Featherless AI API: {str(e)}. Please check your network, API key, and the API documentation."
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
    elif raw_output.lower().startswith("solution:"): # Also check for "Solution:" without "##"
        raw_output = raw_output[len("solution:"):].strip()

    # Ensure any leading/trailing whitespace is removed
    return raw_output.strip()

def chat_evm(user_input):
    prompt = (
        "You are an EVM assistant. Respond directly to the following request without repeating the question:\n\n"
        f"{user_input.strip()}"
    )
    return _call_api(prompt)
