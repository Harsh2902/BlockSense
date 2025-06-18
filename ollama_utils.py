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
    prompt = (
        "You are a Solidity expert. Provide a concise explanation of the following smart contract code. "
        "Do not repeat the question. Just give the explanation directly:\n\n"
        f"{code.strip()}"
    )
    return _call_hf(prompt)

def chat_evm(user_input):
    prompt = (
        "You are an EVM assistant. Respond directly to the following request without repeating the question:\n\n"
        f"{user_input.strip()}"
    )
    return _call_hf(prompt)