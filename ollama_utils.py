import ollama

def explain_contract(code: str) -> str:
    response = ollama.chat(
        model="gemma:2b-instruct",
        messages=[
            {"role": "system", "content": "You are a smart contract expert. Explain solidity code."},
            {"role": "user", "content": code}
        ]
    )
    return response['message']['content']

def chat_evm(user_input: str) -> str:
    # Changed model from "mistral:chat" to "gemma:2b-instruct" for better availability
    response = ollama.chat(
        model="gemma:2b-instruct", # Use gemma:2b-instruct as a generally available model
        messages=[
            {"role": "system", "content": "You can analyze transactions or generate web3 commands, and answer general questions about EVM and blockchain. Be concise."},
            {"role": "user", "content": user_input}
        ]
    )
    return response['message']['content']

