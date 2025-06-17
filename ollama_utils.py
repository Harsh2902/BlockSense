import ollama

def explain_contract(code: str) -> str:
    try:
        response = ollama.chat(
            model="gemma:2b-instruct",
            messages=[
                {"role": "system", "content": "You are a smart contract expert. Explain solidity code."},
                {"role": "user", "content": code}
            ]
        )
        # Safely access nested keys. If 'message' or 'content' is missing,
        # return a default error string instead of causing an AttributeError/TypeError.
        explanation_text = response.get('message', {}).get('content', "No explanation received from AI. The AI response structure was unexpected.")
        return explanation_text
    except Exception as e:
        # Catch any exceptions during the Ollama API call itself
        return f"Error communicating with the AI model: {str(e)}"

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

