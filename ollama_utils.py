import os, requests
import json  # Import json for JSONDecodeError

# Google Gemini API endpoint for gemini-1.5-flash
# This API has a generous free tier for developers.
# You will need to set the GEMINI_API_KEY environment variable.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Changed API key variable name
MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def _call_api(prompt):
    """
    Calls the Google Gemini API.
    """
    headers = {
        "Content-Type": "application/json",
    }
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY missing. Please set your Google Gemini API key."

    # Gemini API uses API key directly in the URL query parameter
    api_url_with_key = f"{MODEL_URL}?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 1000  # Max output tokens for Gemini is similar to max_new_tokens
        }
    }

    try:
        resp = requests.post(api_url_with_key, headers=headers, json=payload)

        # --- DEBUGGING ADDITION ---
        print(f"\nDEBUG: Gemini API Response Status Code: {resp.status_code}")
        print(f"DEBUG: Gemini API Raw Response Text: {resp.text}\n")
        # --- END DEBUGGING ADDING ---

        resp.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        try:
            out = resp.json()
        except json.JSONDecodeError as e:
            return (f"Error decoding JSON response from Gemini API: {e}. "
                    f"Raw response was: '{resp.text}'. This often means the API returned a non-JSON error. "
                    "Please double-check your API key and request parameters against Gemini API documentation.")

        # Gemini API response structure: out['candidates'][0]['content']['parts'][0]['text']
        if isinstance(out, dict) and 'candidates' in out and out['candidates']:
            first_candidate = out['candidates'][0]
            if 'content' in first_candidate and 'parts' in first_candidate['content'] and first_candidate['content'][
                'parts']:
                return first_candidate['content']['parts'][0].get('text', str(out))

        return f"Unexpected API response format from Gemini: {str(out)}"

    except requests.exceptions.RequestException as e:
        return (f"Error calling Gemini API: {str(e)}. "
                f"Please double-check your `MODEL_URL` ({MODEL_URL}), "
                "API key (`GEMINI_API_KEY`), and consult the official Google Gemini API documentation for exact requirements.")
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

    # Call the Gemini model
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
