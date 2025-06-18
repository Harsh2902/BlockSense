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
    prompt = f"Explain this Solidity code concisely:\n\n{code}"
    return _call_hf(prompt)

def chat_evm(user_input):
    prompt = f"You are an EVM assistant. {user_input}"
    return _call_hf(prompt)
