import os
from web3 import Web3
from web3.exceptions import TransactionNotFound, ContractLogicError
from dotenv import load_dotenv

# Load environment variables (important for local development)
load_dotenv()

# Private global variables to store the Web3 instance and the last set node URL
_web3_instance = None
_current_node_url = None
ACCOUNT = None  # Account will be set dynamically by the user


def get_web3_instance():
    """
    Returns the global WEB3_INSTANCE, ensuring it's initialized and connected.
    If not connected, it attempts to re-initialize it using the last known node URL.
    """
    global _web3_instance, _current_node_url

    # If instance doesn't exist or isn't connected, try to establish/re-establish connection
    if _web3_instance is None or not _web3_instance.is_connected():
        if _current_node_url:
            try:
                _web3_instance = Web3(Web3.HTTPProvider(_current_node_url))
                if not _web3_instance.is_connected():
                    raise ConnectionError(f"Could not reconnect to EVM node at {_current_node_url}")
                print(f"DEBUG: Successfully re-connected to EVM node: {_current_node_url}")
            except Exception as e:
                _web3_instance = None  # Ensure it's None if re-connection fails
                print(f"ERROR: Failed to re-connect to EVM node at {_current_node_url}: {str(e)}")
                raise ConnectionError(f"EVM node connection failed: {str(e)}")
        else:
            # If no URL has ever been set, this is a critical error for web3 operations
            raise ConnectionError("EVM node URL has not been set. Cannot establish connection.")
    return _web3_instance


def set_node_url(node_url: str):
    """
    Sets the global node URL and attempts to initialize/re-initialize the WEB3_INSTANCE.
    This allows the application to connect to different EVM nodes dynamically.
    """
    global _current_node_url, _web3_instance
    _current_node_url = node_url
    try:
        # Attempt to set the instance immediately
        _web3_instance = Web3(Web3.HTTPProvider(_current_node_url))
        if not _web3_instance.is_connected():
            raise ConnectionError(f"Could not connect to EVM node at {_current_node_url}")
        print(f"DEBUG: Successfully set and connected to EVM node: {_current_node_url}")
    except Exception as e:
        _web3_instance = None  # Ensure it's None if connection fails
        print(f"ERROR: Failed to set EVM node URL to {node_url}: {str(e)}")
        raise ValueError(f"Failed to set EVM node URL to {node_url}: {str(e)}")


# Initial setup: Attempt to connect using environment variable, then fallback to Ganache default
# This ensures that if the app starts without a specific user input, it still tries to connect.
# The user's explicit input from the frontend will override this.
initial_node_url = os.getenv("INFURA_URL", "http://127.0.0.1:8545")
try:
    set_node_url(initial_node_url)
except Exception as e:
    print(f"Warning: Initial EVM node connection failed: {e}. You may need to provide a URL via the frontend.")


def set_current_account(private_key: str):
    """
    Sets the global ACCOUNT using the provided private key.
    WARNING: This is for demonstration. In production, keys should not
    be handled server-side this way.
    """
    global ACCOUNT
    try:
        # Ensure the Web3 instance is ready before creating an account
        web3_client = get_web3_instance()
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        ACCOUNT = web3_client.eth.account.from_key(private_key)
        if not ACCOUNT.address:
            raise ValueError("Could not derive address from private key.")
        print(f"DEBUG: Account set to {ACCOUNT.address}")
    except Exception as e:
        ACCOUNT = None  # Reset account on failure
        raise ValueError(f"Invalid private key or EVM node not connected: {str(e)}")


def get_current_address() -> str | None:
    """Returns the address of the currently set account, or None if not set."""
    return ACCOUNT.address if ACCOUNT else None


def clear_current_account():
    """Clears the currently set global WEB3 account."""
    global ACCOUNT
    ACCOUNT = None
    print("DEBUG: Account cleared.")


def send_eth(to_address: str, amount_eth: float) -> str:
    """Sends a specified amount of Ether from the connected account to a target address."""
    if not ACCOUNT:
        raise Exception("No wallet connected. Please connect your wallet to send transactions.")

    # Ensure WEB3_INSTANCE is connected right before use
    web3_client = get_web3_instance()

    try:
        value_wei = web3_client.to_wei(amount_eth, 'ether')
        nonce = web3_client.eth.get_transaction_count(ACCOUNT.address)

        tx = {
            'to': to_address,
            'value': value_wei,
            'nonce': nonce,
            'gas': 21000,  # Standard gas limit for ETH transfer
            'gasPrice': web3_client.to_wei('50', 'gwei')  # Example gas price
        }

        signed_tx = ACCOUNT.sign_transaction(tx)
        tx_hash = web3_client.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for the transaction to be mined
        tx_receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

        if tx_receipt.status == 1:
            return f"✅ Transaction successful! Hash: {tx_hash.hex()}"
        else:
            return f"❌ Transaction failed. Hash: {tx_hash.hex()}"
    except TransactionNotFound:
        return "❌ Transaction not found. It might still be propagating or failed silently."
    except Exception as e:
        return f"❌ Error sending ETH: {str(e)}"


def get_balance(address: str) -> str:
    """Retrieves the ETH balance of a given address."""
    try:
        # Ensure WEB3_INSTANCE is connected right before use
        web3_client = get_web3_instance()
        balance_wei = web3_client.eth.get_balance(address)
        balance_eth = web3_client.from_wei(balance_wei, 'ether')
        return f"{balance_eth:.4f} ETH"
    except Exception as e:
        return f"❌ Error getting balance for {address}: {str(e)}"


def estimate_gas(from_address: str, to_address: str | None = None, value: float = 0, data: str | None = None) -> str:
    """Estimates the gas required for a transaction."""
    try:
        web3_client = get_web3_instance()
        tx_params = {'from': from_address}
        if to_address:
            tx_params['to'] = to_address
        if value > 0:
            tx_params['value'] = web3_client.to_wei(value, 'ether')
        if data:
            tx_params['data'] = data

        gas_estimate = web3_client.eth.estimate_gas(tx_params)
        return f"Estimated Gas: {gas_estimate}"
    except Exception as e:
        return f"❌ Error estimating gas: {str(e)}"


def check_tx_status(tx_hash: str) -> str:
    """Checks the status of a transaction given its hash."""
    try:
        web3_client = get_web3_instance()
        receipt = web3_client.eth.get_transaction_receipt(tx_hash)
        if receipt is None:
            return "Transaction is pending or not found."
        elif receipt.status == 1:
            return "✅ Transaction successful."
        else:
            return "❌ Transaction failed."
    except Exception as e:
        return f"❌ Error checking transaction status: {str(e)}"


def deploy_contract(bytecode: str, abi: list) -> str:
    """
    Deploys a smart contract to the network.
    Requires a connected account to sign the transaction.
    """
    if not ACCOUNT:
        raise Exception("No wallet connected. Please connect your wallet to deploy contracts.")
    web3_client = get_web3_instance()
    try:
        contract = web3_client.eth.contract(abi=abi, bytecode=bytecode)
        nonce = web3_client.eth.get_transaction_count(ACCOUNT.address)

        gas_estimate = contract.constructor().estimate_gas({'from': ACCOUNT.address})

        tx_dict = contract.constructor().build_transaction({
            'from': ACCOUNT.address,
            'nonce': nonce,
            'gas': gas_estimate + 200000,  # Add a buffer
            'gasPrice': web3_client.to_wei('50', 'gwei')  # Example gas price
        })

        signed_tx = ACCOUNT.sign_transaction(tx_dict)
        tx_hash = web3_client.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for the transaction receipt
        tx_receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

        if tx_receipt.status == 1:
            return tx_receipt.contractAddress
        else:
            raise Exception(f"Contract deployment failed. Transaction hash: {tx_hash.hex()}")
    except Exception as e:
        raise Exception(f"Contract deployment error: {str(e)}")


def interact_with_contract(abi: list, contract_address: str, method: str, args: list = None):
    """
    Interacts with a deployed smart contract, calling a specified method.
    Automatically determines if it's a read-only call or a transaction.
    """
    web3_client = get_web3_instance()
    try:
        # Check if the method is a transaction (non-view/pure function)
        is_transaction = False
        for f in abi:
            if f.get('name') == method and f.get('type') == 'function' and f.get('stateMutability') not in ['view',
                                                                                                            'pure']:
                is_transaction = True
                break

        contract = web3_client.eth.contract(address=contract_address, abi=abi)
        # Use getattr with a default to avoid AttributeError if method not found
        fn = getattr(contract.functions, method, None)
        if fn is None:
            return f"❌ Method '{method}' not found in contract ABI."

        if is_transaction:
            if not ACCOUNT:
                raise Exception("No wallet connected. Please connect your wallet to send transactions.")
            # Build and send transaction
            nonce = web3_client.eth.get_transaction_count(ACCOUNT.address)
            tx_dict = fn(*(args or [])).build_transaction({
                'from': ACCOUNT.address,
                'nonce': nonce,
                'gas': 2000000,  # Reasonable gas limit for interactions
                'gasPrice': web3_client.to_wei('50', 'gwei')
            })
            signed_tx = ACCOUNT.sign_transaction(tx_dict)
            tx_hash = web3_client.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            return f"Transaction sent: {tx_hash.hex()}. Receipt status: {'Success' if tx_receipt.status == 1 else 'Failed'}"
        else:
            # Call (read-only)
            result = fn(*(args or [])).call()
            return result
    except ContractLogicError as e:
        return f"❌ Logic Error: {str(e)}"
    except Exception as e:
        # Catch all other exceptions during interaction and return a message
        return f"❌ Error interacting with contract: {str(e)}"
