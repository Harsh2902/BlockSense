from flask import Flask, render_template, request, jsonify
from ollama_utils import explain_contract, chat_evm
from blockdag import get_blockdag_data
from evm_utils import (
    send_eth, get_balance, estimate_gas, check_tx_status,
    deploy_contract, interact_with_contract, set_current_account,
    get_current_address, clear_current_account, set_evm_node # Import new function
)
import re, json
import os

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/set_wallet_config', methods=['POST'])
def set_wallet_config():
    """
    Sets the wallet configuration (private key and EVM node URL) for the backend.
    WARNING: In a real application, private keys should NEVER be sent to the backend.
    This is for demonstration purposes only.
    """
    try:
        data = request.get_json()
        private_key = data.get('private_key')
        node_url = data.get('node_url')

        if not private_key:
            return jsonify({'status': 'error', 'message': 'Private key is required.'}), 400
        if not node_url:
            return jsonify({'status': 'error', 'message': 'EVM Node URL is required.'}), 400

        # Attempt to set the EVM node first, then the account
        try:
            set_evm_node(node_url) # Call the new function to set the node
            set_current_account(private_key, node_url) # Pass node_url to set_current_account
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400

        connected_address = get_current_address()

        return jsonify(
            {'status': 'success', 'message': 'Wallet configured successfully.', 'address': connected_address}
        ), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/clear_wallet_config', methods=['POST'])
def clear_wallet_config():
    """Clears the wallet configuration from the backend."""
    try:
        clear_current_account()
        return jsonify({'status': 'success', 'message': 'Wallet configuration cleared.'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/explain', methods=['POST'])
def explain():
    try:
        data = request.get_json()
        contract_code = data['contract']
        explanation = explain_contract(contract_code)
        return jsonify({'explanation': explanation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_input = data['chat_input'].lower() # Convert to lower for easier matching

        # Enhanced AI parsing for commands
        # Check if the user is asking for balance
        if "balance of" in user_input:
            match = re.search(r'balance of (0x[0-9a-fA-F]{40})', user_input)
            if match:
                address = match.group(1)
                balance_result = get_balance(address)
                return jsonify({'response': balance_result})
            else:
                return jsonify({'response': "Please provide a valid Ethereum address to check its balance (e.g., 'balance of 0x...')."})
        elif user_input == "my balance" or user_input == "balance":
            current_address = get_current_address()
            if current_address:
                balance_result = get_balance(current_address)
                return jsonify({'response': balance_result})
            else:
                return jsonify({'response': "No private key wallet connected to backend. Please connect your private key wallet to check its balance."})
        # Check if the user is trying to send ETH
        elif "transfer" in user_input and "eth to" in user_input:
            match = re.search(r'transfer\s+([\d.]+)\s*eth\s+to\s+(0x[0-9a-fA-F]{40})', user_input)
            if match:
                amount_eth = float(match.group(1))
                to_address = match.group(2)
                # Convert ETH to Wei for the transaction
                amount_wei = WEB3.to_wei(amount_eth, 'ether') # WEB3 needs to be connected here
                send_result = send_eth(to_address, amount_wei)
                return jsonify({'response': send_result})
            else:
                return jsonify({'response': "Please specify a valid amount and recipient (e.g., 'transfer 0.1 ETH to 0x...')."})
        # Check if the user is asking to estimate gas
        elif "estimate gas for" in user_input:
            # This would require more sophisticated parsing or a structured input from frontend
            return jsonify({'response': "For gas estimation, please provide the full transaction data in a structured way."})
        # Check transaction status
        elif "check transaction status" in user_input or "tx status" in user_input:
            match = re.search(r'(0x[0-9a-fA-F]{64})', user_input) # Regex for transaction hash
            if match:
                tx_hash = match.group(1)
                status_result = check_tx_status(tx_hash)
                return jsonify({'response': status_result})
            else:
                return jsonify({'response': "Please provide a transaction hash to check its status (e.g., 'check tx status 0x...')."})
        else:
            # Default to AI chat for other queries
            chat_response = chat_evm(user_input)
            return jsonify({'response': chat_response})

    except Exception as e:
        # Catch errors if WEB3 is not initialized here, or other parsing errors
        return jsonify({'error': str(e)}), 500


@app.route('/deploy', methods=['POST'])
def deploy():
    try:
        data = request.get_json()
        abi = data['abi']
        bytecode = data['bytecode']
        # constructor_args = data.get('constructor_args', []) # Removed from HTML, so safe to remove here

        contract_address = deploy_contract(abi, bytecode) # Pass no args
        return jsonify({'contract_address': contract_address})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/interact', methods=['POST'])
def interact():
    try:
        data = request.get_json()
        abi = data['abi']
        address = data['contract_address']
        method = data['method']
        args = data.get('args', [])

        # Parse ABI to check method's stateMutability
        is_read_only = False
        method_abi_entry = next((item for item in abi if item.get('name') == method and item.get('type') == 'function'),
                                None)

        if method_abi_entry and method_abi_entry.get('stateMutability') in ['view', 'pure']:#
            is_read_only = True

        # Only require wallet if it's a non-read-only (transaction) method
        if not is_read_only and not get_current_address():
            return jsonify(
                {'error': "No wallet connected. Please connect your wallet first for transaction methods."}), 400

        result = interact_with_contract(abi, address, method, args, is_transaction=not is_read_only)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/blockdag', methods=['GET'])
def blockdag():
    try:
        dag_data = get_blockdag_data()
        return jsonify(dag_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

