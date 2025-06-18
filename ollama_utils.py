import os, requests

HF_API_KEY = os.getenv("HF_API_KEY", "")
MODEL_URL = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"

def _call_hf(prompt):
    if not HF_API_KEY:
        return "Error: HF_API_KEY missing."
    resp = requests.post(MODEL_URL,
        headers={"Authorization": f"Bearer {HF_API_KEY}"},
        json={"inputs": prompt, "parameters": {"max_new_tokens":300}})
    if resp.status_code == 404:
        return "Model not available via text API."
    resp.raise_for_status()
    out = resp.json()
    return out[0].get("generated_text", str(out))

def explain_contract(code):
    # The original prompt string
    initial_prompt = (
        "You are a Solidity expert. Provide a concise explanation of the following smart contract code. "
        "Do not repeat the question. Just give the explanation directly:\n\n"
    )

    # Full prompt sent to the model
    full_prompt_sent = initial_prompt + code.strip()

    # Call the Hugging Face model
    raw_output = _call_hf(full_prompt_sent)

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
    return _call_hf(prompt)