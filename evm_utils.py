import os
from web3 import Web3
from web3.exceptions import TransactionNotFound, ContractLogicError
from dotenv import load_dotenv

# Load environment variables (important for local development)
load_dotenv()

# Initialize WEB3_INSTANCE as None initially. It will be set by set_node_url.
WEB3_INSTANCE = None
ACCOUNT = None  # Account will be set dynamically by the user

def set_node_url(node_url: str):
    """
    Sets or updates the global WEB3_INSTANCE with the given node URL.
    This allows the application to connect to different EVM nodes dynamically.
    """
    global WEB3_INSTANCE
    try:
        WEB3_INSTANCE = Web3(Web3.HTTPProvider(node_url))
        # Optional: Verify connection immediately
        if not WEB3_INSTANCE.is_connected():
            raise ConnectionError(f"Could not connect to EVM node at {node_url}")
        print(f"Successfully connected to EVM node: {node_url}")
    except Exception as e:
        WEB3_INSTANCE = None # Reset on failure
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
    if not WEB3_INSTANCE:
        raise Exception("EVM node is not connected. Please set the node URL first.")
    try:
        # Ensure the private key starts with '0x' if it doesn't already
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        ACCOUNT = WEB3_INSTANCE.eth.account.from_key(private_key)
        # Verify if the account was successfully loaded
        if not ACCOUNT.address:
            raise ValueError("Could not derive address from private key.")
    except Exception as e:
        ACCOUNT = None  # Reset account on failure
        raise ValueError(f"Invalid private key: {str(e)}")


def get_current_address() -> str | None:
    """Returns the address of the currently set account, or None if not set."""
    return ACCOUNT.address if ACCOUNT else None


def clear_current_account():
    """Clears the currently set global WEB3 account."""
    global ACCOUNT
    ACCOUNT = None


def send_eth(to_address: str, amount_eth: float) -> str:
    """Sends a specified amount of Ether from the connected account to a target address."""
    if not ACCOUNT:
        raise Exception("No wallet connected. Please connect your wallet to send transactions.")
    if not WEB3_INSTANCE or not WEB3_INSTANCE.is_connected():
        raise Exception("EVM node is not connected. Cannot send ETH.")

    try:
        value_wei = WEB3_INSTANCE.to_wei(amount_eth, 'ether')
        nonce = WEB3_INSTANCE.eth.get_transaction_count(ACCOUNT.address)

        tx = {
            'to': to_address,
            'value': value_wei,
            'nonce': nonce,
            'gas': 21000,  # Standard gas limit for ETH transfer
            'gasPrice': WEB3_INSTANCE.to_wei('50', 'gwei')  # Example gas price
        }

        signed_tx = ACCOUNT.sign_transaction(tx)
        tx_hash = WEB3_INSTANCE.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for the transaction to be mined
        tx_receipt = WEB3_INSTANCE.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

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
        # Check if the Web3 instance is connected
        if not WEB3_INSTANCE or not WEB3_INSTANCE.is_connected():
            return "❌ Web3 is not connected to an Ethereum node. Please ensure your node (e.g., Ganache) is running or a valid URL is provided."
        balance_wei = WEB3_INSTANCE.eth.get_balance(address)
        balance_eth = WEB3_INSTANCE.from_wei(balance_wei, 'ether')
        return f"{balance_eth:.4f} ETH"
    except Exception as e:
        return f"❌ Error getting balance for {address}: {str(e)}"


def estimate_gas(from_address: str, to_address: str | None = None, value: float = 0, data: str | None = None) -> str:
    """Estimates the gas required for a transaction."""
    try:
        if not WEB3_INSTANCE or not WEB3_INSTANCE.is_connected():
            return "❌ Web3 is not connected to an Ethereum node. Cannot estimate gas."
        tx_params = {'from': from_address}
        if to_address:
            tx_params['to'] = to_address
        if value > 0:
            tx_params['value'] = WEB3_INSTANCE.to_wei(value, 'ether')
        if data:
            tx_params['data'] = data

        gas_estimate = WEB3_INSTANCE.eth.estimate_gas(tx_params)
        return f"Estimated Gas: {gas_estimate}"
    except Exception as e:
        return f"❌ Error estimating gas: {str(e)}"


def check_tx_status(tx_hash: str) -> str:
    """Checks the status of a transaction given its hash."""
    try:
        if not WEB3_INSTANCE or not WEB3_INSTANCE.is_connected():
            return "❌ Web3 is not connected to an Ethereum node. Cannot check transaction status."
        receipt = WEB3_INSTANCE.eth.get_transaction_receipt(tx_hash)
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
    if not WEB3_INSTANCE or not WEB3_INSTANCE.is_connected():
        raise Exception("❌ Web3 is not connected to an Ethereum node. Cannot deploy contract.")
    try:
        contract = WEB3_INSTANCE.eth.contract(abi=abi, bytecode=bytecode)
        nonce = WEB3_INSTANCE.eth.get_transaction_count(ACCOUNT.address)

        gas_estimate = contract.constructor().estimate_gas({'from': ACCOUNT.address})

        tx_dict = contract.constructor().build_transaction({
            'from': ACCOUNT.address,
            'nonce': nonce,
            'gas': gas_estimate + 200000,  # Add a buffer
            'gasPrice': WEB3_INSTANCE.to_wei('50', 'gwei')  # Example gas price
        })

        signed_tx = ACCOUNT.sign_transaction(tx_dict)
        tx_hash = WEB3_INSTANCE.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for the transaction receipt
        tx_receipt = WEB3_INSTANCE.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

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
    try:
        if not WEB3_INSTANCE or not WEB3_INSTANCE.is_connected():
            return "❌ Web3 is not connected to an Ethereum node. Cannot interact with contract."
        # Check if the method is a transaction (non-view/pure function)
        is_transaction = False
        for f in abi:
            if f.get('name') == method and f.get('type') == 'function' and f.get('stateMutability') not in ['view',
                                                                                                            'pure']:
                is_transaction = True
                break

        contract = WEB3_INSTANCE.eth.contract(address=contract_address, abi=abi)
        # Use getattr with a default to avoid AttributeError if method not found
        fn = getattr(contract.functions, method, None)
        if fn is None:
            return f"❌ Method '{method}' not found in contract ABI."

        if is_transaction:
            if not ACCOUNT:
                raise Exception("No wallet connected. Please connect your wallet to send transactions.")
            # Build and send transaction
            nonce = WEB3_INSTANCE.eth.get_transaction_count(ACCOUNT.address)
            tx_dict = fn(*(args or [])).build_transaction({
                'from': ACCOUNT.address,
                'nonce': nonce,
                'gas': 2000000,  # Reasonable gas limit for interactions
                'gasPrice': WEB3_INSTANCE.to_wei('50', 'gwei')
            })
            signed_tx = ACCOUNT.sign_transaction(tx_dict)
            tx_hash = WEB3_INSTANCE.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_receipt = WEB3_INSTANCE.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
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
