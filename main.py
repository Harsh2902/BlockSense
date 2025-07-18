from flask import Flask, render_template, request, jsonify
from ollama_utils import explain_contract, chat_evm
from blockdag import get_blockdag_data
from evm_utils import (
    send_eth, get_balance, estimate_gas, check_tx_status,
    deploy_contract, interact_with_contract, set_current_account, get_current_address, clear_current_account,
    set_node_url, get_web3_instance, # Import the new function
    verify_contract_source # Import the new verification function
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
    Sets the wallet configuration (private key) and EVM node URL for the backend.
    WARNING: In a real application, private keys should NEVER be sent to the backend.
    This is for demonstration purposes only.
    """
    try:
        data = request.get_json()
        private_key = data.get('private_key')
        node_url = data.get('node_url')  # Get the node URL

        if not private_key:
            return jsonify({'status': 'error', 'message': 'Private key is required.'}), 400
        if not node_url:
            return jsonify({'status': 'error', 'message': 'EVM Node URL is required.'}), 400

        # Set the node URL first. This also initializes WEB3_INSTANCE internally in evm_utils
        set_node_url(node_url)

        # Attempt to set the account in evm_utils
        set_current_account(private_key)
        connected_address = get_current_address()

        print(
            f"DEBUG: Wallet set_wallet_config successful. Node URL: {node_url}, Connected Address: {connected_address}")
        try:
            # Try to get the instance to print its connection status
            web3_client_for_debug = get_web3_instance()
            print(
                f"DEBUG: WEB3_INSTANCE after set_wallet_config: {web3_client_for_debug}, Is Connected: {web3_client_for_debug.is_connected()}")
        except Exception as e:
            print(f"DEBUG: Could not get WEB3_INSTANCE after set_wallet_config: {e}")

        return jsonify(
            {'status': 'success', 'message': 'Wallet configured successfully.', 'address': connected_address})
    except Exception as e:
        print(f"DEBUG: Error in set_wallet_config: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/clear_wallet_config', methods=['POST'])
def clear_wallet_config():
    """Clears the wallet configuration from the backend."""
    try:
        clear_current_account()
        print("DEBUG: Wallet configuration cleared.")
        return jsonify({'status': 'success', 'message': 'Wallet configuration cleared.'})
    except Exception as e:
        print(f"DEBUG: Error in clear_wallet_config: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/explain', methods=['POST'])
def explain():
    try:
        data = request.get_json()
        contract_code = data['contract']
        explanation = explain_contract(contract_code)
        return jsonify({'explanation': explanation})
    except Exception as e:
        print(f"DEBUG: Error in /explain: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_input = data['chat_input'].strip()  # <--- Added .strip() here

        # Check for specific commands first
        balance_match = re.match(r'check balance of (0x[0-9a-fA-F]{40})', user_input, re.IGNORECASE)
        my_balance_match = re.match(r'^(my\s+)?balance(?:\s*\?)?$', user_input, re.IGNORECASE)
        send_eth_match = re.match(r'transfer\s+([\d.]+)\s+eth\s+to\s+(0x[0-9a-fA-F]{40})', user_input, re.IGNORECASE)
        check_tx_status_match = re.match(r'check transaction status of (0x[0-9a-fA-F]{64})', user_input, re.IGNORECASE)

        if balance_match:
            address = balance_match.group(1)
            # --- DEBUGGING START ---
            print(f"\nDEBUG: Processing 'check balance of' for {address}")
            try:
                web3_client_for_debug = get_web3_instance()
                print(
                    f"DEBUG: WEB3_INSTANCE in balance_match: {web3_client_for_debug}, Is Connected: {web3_client_for_debug.is_connected()}")
            except Exception as e:
                print(f"DEBUG: Could not get WEB3_INSTANCE for balance_match: {e}")
            # --- DEBUGGING END ---
            balance = get_balance(address)
            return jsonify({'response': f"Backend: Balance of {address}: {balance}"})
        elif my_balance_match:
            current_address = get_current_address()
            if current_address:
                # --- DEBUGGING START ---
                print(f"\nDEBUG: Processing 'my balance' for {current_address}")
                try:
                    web3_client_for_debug = get_web3_instance()
                    print(
                        f"DEBUG: WEB3_INSTANCE in my_balance_match: {web3_client_for_debug}, Is Connected: {web3_client_for_debug.is_connected()}")
                except Exception as e:
                    print(f"DEBUG: Could not get WEB3_INSTANCE for my_balance_match: {e}")
                # --- DEBUGGING END ---
                balance = get_balance(current_address)
                return jsonify(
                    {'response': f"Backend: Balance of your connected backend wallet ({current_address}): {balance}"})
            else:
                return jsonify({
                    'response': "No private key wallet connected to backend. Please connect your private key wallet to check its balance."})
        elif send_eth_match:
            amount = float(send_eth_match.group(1))
            to_address = send_eth_match.group(2)
            try:
                # --- DEBUGGING START ---
                print(f"\nDEBUG: Processing 'transfer' for amount={amount}, to={to_address}")
                # Get the Web3 instance right before using it
                web3_client = get_web3_instance()
                print(
                    f"DEBUG: WEB3_INSTANCE in send_eth_match (after get_web3_instance): {web3_client}, Is Connected: {web3_client.is_connected()}")
                # --- DEBUGGING END ---

                # Convert to checksum address before sending to evm_utils
                checksum_to_address = web3_client.to_checksum_address(to_address)
                print(f"DEBUG: Checksummed address: {checksum_to_address}")
                result = send_eth(checksum_to_address, amount)
                print(f"DEBUG: send_eth result: {result}")
                return jsonify({'response': result})
            except ConnectionError as ce:  # Catch specific connection errors
                print(f"DEBUG: ConnectionError during transfer: {str(ce)}")
                return jsonify({
                                   'response': f"Backend EVM node connection issue: {str(ce)}. Please ensure your node is running and try reconnecting."})
            except ValueError as ve:
                print(f"DEBUG: ValueError during transfer: {str(ve)}")
                return jsonify({'error': f"Invalid Ethereum address: {str(ve)}"})
            except Exception as e:
                print(f"DEBUG: General Exception during transfer: {str(e)}")
                return jsonify({'error': str(e)})
        elif check_tx_status_match:
            tx_hash = check_tx_status_match.group(1)
            status = check_tx_status(tx_hash)
            return jsonify({'response': f"Transaction status for {tx_hash}: {status}"})
        else:
            # If no specific command, use LLM for general chat
            response = chat_evm(user_input)
            return jsonify({'response': response})
    except Exception as e:
        print(f"DEBUG: Top-level error in /chat route: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/deploy', methods=['POST'])
def deploy():
    try:
        data = request.get_json()
        bytecode = data['bytecode']
        abi = data['abi']

        address = deploy_contract(bytecode, abi)
        return jsonify({'contract_address': address})
    except Exception as e:
        print(f"DEBUG: Error during contract deployment in Flask route: {e}")
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

        if method_abi_entry and method_abi_entry.get('stateMutability') in ['view',
                                                                            'pure']:  # Only require wallet if it's a non-read-only (transaction) method
            is_read_only = True

        # Only require wallet if it's a non-read-only (transaction) method
        if not is_read_only and not get_current_address():
            return jsonify(
                {'error': "No wallet connected. Please connect your wallet first for transaction methods."}), 400

        result = interact_with_contract(abi, address, method, args)
        return jsonify({'result': result})
    except Exception as e:
        print(f"DEBUG: Error during contract interaction in Flask route: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/verify_contract', methods=['POST'])
def verify_contract():
    """
    Endpoint to trigger smart contract source code verification on a block explorer.
    """
    try:
        data = request.get_json()
        contract_address = data.get('contract_address')
        source_code = data.get('source_code')
        contract_name = data.get('contract_name')
        compiler_version = data.get('compiler_version')
        optimization_used = data.get('optimization_used', False) # Default to False
        runs = data.get('runs', 200) # Default runs for optimizer

        if not all([contract_address, source_code, contract_name, compiler_version]):
            return jsonify({'error': 'Missing required fields for contract verification.'}), 400

        result = verify_contract_source(
            contract_address, source_code, contract_name, compiler_version, optimization_used, runs
        )
        return jsonify({'status': 'success', 'message': result})
    except Exception as e:
        print(f"DEBUG: Error during contract verification in Flask route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/blockdag', methods=['GET'])
def blockdag():
    try:
        dag_data = get_blockdag_data()
        return jsonify(dag_data)
    except Exception as e:
        print(f"DEBUG: Error in /blockdag: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)