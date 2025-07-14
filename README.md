# BlockSense

BlockSense is a powerful web application built with Flask that provides an intuitive interface for interacting with EVM-compatible blockchains, managing wallet operations, deploying and interacting with smart contracts, and leveraging AI for explanations and chat. It also includes a simulated BlockDAG visualization feature.

**Disclaimer**: This project is for **demonstration and educational purposes only**. The method of handling private keys on the backend is **highly insecure** and should **NEVER** be used in a production environment.

## ✨ Features

* **EVM Wallet & Transaction Management:**
    * **Wallet Configuration:** Connect a private key to the backend for transaction signing (for demonstration purposes only).
    * **Balance Check:** Query the ETH balance of any address or the connected backend wallet.
    * **ETH Transfer:** Send Ethereum from your connected backend wallet to any recipient address.
    * **Transaction Status:** Check the confirmation status of any transaction using its hash.
* **Smart Contract Interaction:**
    * **AI-Powered Explanation:** Get detailed explanations of Solidity smart contract code using an integrated Large Language Model (LLM).
    * **Contract Deployment:** Deploy smart contracts to an EVM network using their bytecode and ABI.
    * **Contract Interaction:** Call methods on deployed smart contracts, supporting both read-only (view/pure) and transactional functions.
* **AI Chat Integration:**
    * Engage in a conversational chat about EVM-related topics.
    * Directly issue commands within the chat for wallet operations (e.g., "check balance of `0x...`", "transfer `1.5` eth to `0x...`").
* **BlockDAG Visualization:**
    * Simulated BlockDAG data generation and visualization, offering insights into directed acyclic graph blockchain structures.

## 🚀 Technologies Used

* **Backend:**
    * [Flask](https://flask.palletsprojects.com/): Python web framework
    * [Web3.py](https://web3py.readthedocs.io/): Python library for interacting with Ethereum
    * [Ollama](https://ollama.ai/): For running large language models locally (or any compatible LLM API like Google Gemini)
    * `python-dotenv`: For managing environment variables
* **Frontend (implied):**
    * HTML, CSS, JavaScript
    * [Bootstrap 5](https://getbootstrap.com/): Responsive UI framework
    * [Vis.js Network](https://visjs.github.io/vis-network/docs/network/): For network graph visualization (BlockDAG)
    * [Highlight.js](https://highlightjs.org/): For code syntax highlighting
    * [Animate.css](https://animate.style/): For CSS animations

## ⚙️ Setup and Installation

Follow these steps to get BlockSense up and running on your local machine.

### Prerequisites

* **Python 3.8+**
* **pip** (Python package installer)
* **An EVM-compatible blockchain node:**
    * For local development, you can use [Ganache](https://trufflesuite.com/ganache/) (recommended) or a local Geth/Hardhat node.
    * Ensure your node is running and accessible (e.g., `http://127.0.0.1:8545`).
* **Ollama (for LLM features):**
    * Download and install [Ollama](https://ollama.ai/download).
    * Pull a model, e.g., `ollama pull gemini-1.5-flash` or `ollama pull llama2`. The `ollama_utils.py` is configured to use `gemini-1.5-flash` by default. If you want to use Google Gemini API, you need to set `GEMINI_API_KEY` in your environment.

### Steps

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/your-username/BlockSense.git](https://github.com/your-username/BlockSense.git)
    cd BlockSense
    ```

2.  **Create a virtual environment (recommended)::**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**

    Create a `.env` file in the root directory of the project and add your Google Gemini API key (if using the Google Gemini API instead of a local Ollama instance):

    ```
    GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
    # If using Ollama locally, you don't need GEMINI_API_KEY,
    # but ensure your Ollama server is running and the model is pulled.
    ```
    If you are using Ollama, ensure your Ollama server is running. The `ollama_utils.py` file uses `gemini-1.5-flash` by default. If you want to use a different model, you might need to adjust the `MODEL_URL` in `ollama_utils.py`.

5.  **Run the Flask Backend:**

    ```bash
    python main.py
    ```

    The application will typically run on `http://127.0.0.1:5000`.

## 💡 Usage

Once the backend is running, open your web browser and navigate to `http://127.0.0.1:5000`.

### Connecting a Wallet (Backend Private Key)

1.  Go to the "Wallet" or "Settings" section (as per your `index.html` UI).
2.  Enter your EVM Node URL (e.g., `http://127.0.0.1:8545` for Ganache).
3.  Enter a private key. **Remember the security warning above.** This private key will be used by the backend to sign transactions.
4.  Click "Connect Wallet". Your wallet address should appear.

### Chat & Commands

Use the chat interface to interact with the backend and the LLM:

* **General Questions:** Ask questions about blockchain, EVM, etc. (e.g., "What is a smart contract?").
* **Check Balance:** Type `check balance of 0x...` (replace `0x...` with an Ethereum address) or `my balance` to check the balance of your connected wallet.
* **Send ETH:** Type `transfer <amount> eth to 0x...` (e.g., `transfer 0.5 eth to 0xAbCd...`).
* **Check Transaction Status:** Type `check transaction status of 0x...` (replace `0x...` with a transaction hash).

### Smart Contract Features

* **Explain Contract:** Paste Solidity code into the designated area and click "Explain" to get an LLM-generated explanation.
* **Deploy Contract:** Provide the contract's bytecode and ABI, then click "Deploy" to deploy it to the connected EVM network.
* **Interact with Contract:** Enter the deployed contract's address, its ABI, the method name, and any required arguments to call a contract function.

### BlockDAG Visualization

Navigate to the BlockDAG section of the application (if present in `index.html`) to see a simulated visualization of a Directed Acyclic Graph of blocks.

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## 📄 License

This project is open-sourced under the MIT License. See the `LICENSE` file for more details.
