import os
import requests # Added for making HTTP requests
from web3 import Web3
from web3.exceptions import TransactionNotFound, ContractLogicError
from eth_account import Account # Explicitly import Account for clarity and robustness
from dotenv import load_dotenv

# Load environment variables (important for local development)
load_dotenv()

# Private global variables to store the Web3 instance and the last set node URL
_web3_instance = None
_current_node_url = None
ACCOUNT = None  # Account will be set dynamically by the user

# Etherscan API key from environment variables
# User needs to get a free API key from Etherscan (or equivalent explorer)
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")

# Base URL for Etherscan API (Mainnet).
# IMPORTANT: Change this URL if you are deploying to a different network
# (e.g., Goerli, Sepolia, Polygon, BSC).
# Examples:
# Goerli: "https://api-goerli.etherscan.io/api"
# Sepolia: "https://api-sepolia.etherscan.io/api"
# Polygon Mainnet: "https://api.polygonscan.com/api"
# BSC Mainnet: "https://api.bscscan.com/api"
ETHERSCAN_API_BASE_URL = os.getenv("ETHERSCAN_API_BASE_URL", "https://api.etherscan.io/api")


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
                print(f"ERROR: Failed to re-connect to EVM node: {e}")
        else:
            print("WARNING: No node URL set. Cannot get Web3 instance.")
            raise ConnectionError("EVM node URL not set. Please configure your wallet.")
    return _web3_instance


def set_node_url(node_url):
    """Sets the EVM node URL and initializes the Web3 instance."""
    global _web3_instance, _current_node_url
    _current_node_url = node_url
    try:
        _web3_instance = Web3(Web3.HTTPProvider(_current_node_url))
        if not _web3_instance.is_connected():
            raise ConnectionError(f"Could not connect to EVM node at {_current_node_url}")
        print(f"DEBUG: Successfully connected to EVM node: {_current_node_url}")
    except Exception as e:
        _web3_instance = None
        raise ConnectionError(f"Failed to connect to EVM node: {e}")


def set_current_account(private_key):
    """Sets the global account using a private key."""
    global ACCOUNT
    try:
        # Use the imported Account class directly to create the account object
        ACCOUNT = Account.from_key(private_key)
        print(f"DEBUG: Account set: {ACCOUNT.address}")
    except Exception as e:
        ACCOUNT = None
        # Re-raise with a more informative message if it's a key issue
        if "Bad input" in str(e) or "Invalid private key" in str(e):
            raise Exception(f"Invalid private key format: {e}. Ensure it starts with '0x' and is 66 characters long.")
        else:
            raise Exception(f"Wallet connection or private key issue: {e}")


def clear_current_account():
    """Clears the global account."""
    global ACCOUNT
    ACCOUNT = None


def get_current_address():
    """Returns the address of the currently connected account, or None if not connected."""
    return ACCOUNT.address if ACCOUNT else None


def send_eth(to_address, amount_eth):
    """Sends Ether from the connected account to a specified address."""
    if not ACCOUNT:
        return "Error: No wallet connected. Please connect your wallet to send transactions."
    try:
        web3_client = get_web3_instance()
        nonce = web3_client.eth.get_transaction_count(ACCOUNT.address)
        amount_wei = web3_client.to_wei(amount_eth, 'ether')

        tx = {
            'from': ACCOUNT.address,
            'to': web3_client.to_checksum_address(to_address),
            'value': amount_wei,
            'gas': 21000,  # Standard gas limit for ETH transfer
            'gasPrice': web3_client.eth.gas_price,  # Use current gas price
            'nonce': nonce,
        }

        signed_tx = web3_client.eth.account.sign_transaction(tx, private_key=ACCOUNT.key)
        # --- DEBUGGING START ---
        print(f"DEBUG (send_eth): Type of signed_tx: {type(signed_tx)}")
        print(f"DEBUG (send_eth): dir(signed_tx): {dir(signed_tx)}")
        # --- DEBUGGING END ---
        # Corrected: changed signed_tx.rawTransaction to signed_tx.raw_transaction
        tx_hash = web3_client.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

        status = "Success" if tx_receipt.status == 1 else "Failed"
        return f"Transaction sent: {tx_hash.hex()}. Status: {status}"
    except ConnectionError as ce:
        return f"Connection Error: {str(ce)}. Ensure your EVM node is running and accessible."
    except ValueError as ve:
        return f"Input Error: {str(ve)}. Check address format or amount."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


def get_balance(address):
    """Gets the balance of an address in Ether."""
    try:
        web3_client = get_web3_instance()
        balance_wei = web3_client.eth.get_balance(web3_client.to_checksum_address(address))
        balance_eth = web3_client.from_wei(balance_wei, 'ether')
        return f"{balance_eth} ETH"
    except ConnectionError as ce:
        return f"Connection Error: {str(ce)}. Ensure your EVM node is running and accessible."
    except ValueError as ve:
        return f"Invalid address format: {str(ve)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


def estimate_gas(from_address, to_address, value):
    """Estimates gas for a simple ETH transfer."""
    try:
        web3_client = get_web3_instance()
        tx = {
            'from': web3_client.to_checksum_address(from_address),
            'to': web3_client.to_checksum_address(to_address),
            'value': web3_client.to_wei(value, 'ether')
        }
        gas_estimate = web3_client.eth.estimate_gas(tx)
        return f"{gas_estimate} units"
    except ConnectionError as ce:
        return f"Connection Error: {str(ce)}. Ensure your EVM node is running and accessible."
    except Exception as e:
        return f"Error estimating gas: {str(e)}"


def check_tx_status(tx_hash):
    """Checks the status of a transaction."""
    try:
        web3_client = get_web3_instance()
        tx_receipt = web3_client.eth.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            return "Transaction not found or not yet mined."
        status = "Success" if tx_receipt.status == 1 else "Failed"
        return f"Transaction Status: {status} (Block: {tx_receipt.blockNumber})"
    except ConnectionError as ce:
        return f"Connection Error: {str(ce)}. Ensure your EVM node is running and accessible."
    except TransactionNotFound:
        return "Transaction not found."
    except Exception as e:
        return f"Error checking transaction status: {str(e)}"


def deploy_contract(bytecode, abi):
    """Deploys a smart contract."""
    if not ACCOUNT:
        raise Exception("No wallet connected. Please connect your wallet to deploy contracts.")
    try:
        web3_client = get_web3_instance()
        contract = web3_client.eth.contract(abi=abi, bytecode=bytecode)
        nonce = web3_client.eth.get_transaction_count(ACCOUNT.address)

        # Build transaction
        tx_dict = contract.constructor().build_transaction({
            'from': ACCOUNT.address,
            'nonce': nonce,
            'gas': 5000000,  # High gas limit for deployment
            'gasPrice': web3_client.eth.gas_price # Use current gas price
        })

        # Sign and send
        signed_tx = web3_client.eth.account.sign_transaction(tx_dict, private_key=ACCOUNT.key)
        # --- DEBUGGING START ---
        print(f"DEBUG (deploy_contract): Type of signed_tx: {type(signed_tx)}")
        print(f"DEBUG (deploy_contract): dir(signed_tx): {dir(signed_tx)}")
        # --- DEBUGGING END ---
        # Corrected: changed signed_tx.rawTransaction to signed_tx.raw_transaction
        tx_hash = web3_client.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

        if tx_receipt.status == 1:
            return tx_receipt.contractAddress
        else:
            raise Exception(f"Contract deployment failed. Transaction hash: {tx_hash.hex()}")
    except ConnectionError as ce:
        raise ConnectionError(f"Connection Error: {str(ce)}. Ensure your EVM node is running and accessible.")
    except Exception as e:
        raise Exception(f"Error deploying contract: {str(e)}")


def interact_with_contract(abi, address, method, args=None):
    """Interacts with a deployed smart contract."""
    if args is None:
        args = []
    try:
        web3_client = get_web3_instance()
        contract = web3_client.eth.contract(address=web3_client.to_checksum_address(address), abi=abi)

        # Get the function object
        # Use getattr to avoid AttributeError if method not found
        fn = getattr(contract.functions, method, None)
        if fn is None:
            return f"❌ Method '{method}' not found in contract ABI."

        # Determine if it's a transaction (state-changing) or a call (read-only)
        # by checking stateMutability in ABI
        method_abi_entry = next((item for item in abi if item.get('name') == method and item.get('type') == 'function'), None)
        is_transaction = method_abi_entry and method_abi_entry.get('stateMutability') not in ['view', 'pure']

        if is_transaction:
            if not ACCOUNT:
                raise Exception("No wallet connected. Please connect your wallet to send transactions.")
            # Build and send transaction
            nonce = web3_client.eth.get_transaction_count(ACCOUNT.address)
            tx_dict = fn(*(args or [])).build_transaction({
                'from': ACCOUNT.address,
                'nonce': nonce,
                'gas': 2000000,  # Reasonable gas limit for interactions
                'gasPrice': web3_client.eth.gas_price # Use current gas price
            })
            signed_tx = web3_client.eth.account.sign_transaction(tx_dict, private_key=ACCOUNT.key)
            # --- DEBUGGING START ---
            print(f"DEBUG (interact_with_contract): Type of signed_tx: {type(signed_tx)}")
            print(f"DEBUG (interact_with_contract): dir(signed_tx): {dir(signed_tx)}")
            # --- DEBUGGING END ---
            # Corrected: changed signed_tx.rawTransaction to signed_tx.raw_transaction
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
        # Catch all other exceptions
        return f"❌ An error occurred during contract interaction: {str(e)}"


def verify_contract_source(contract_address, source_code, contract_name, compiler_version, optimization_used, runs):
    """
    Submits contract source code for verification to an Etherscan-compatible block explorer.
    Requires ETHERSCAN_API_KEY and ETHERSCAN_API_BASE_URL to be set in environment variables.
    """
    if not ETHERSCAN_API_KEY:
        return "Error: ETHERSCAN_API_KEY environment variable is not set. Cannot verify contract."
    if not ETHERSCAN_API_BASE_URL:
        return "Error: ETHERSCAN_API_BASE_URL environment variable is not set. Cannot verify contract."

    # Etherscan API expects specific compiler version format, e.g., 'v0.8.17+commit.8df45f5f'
    # Ensure the provided compiler_version matches this format.
    # If optimization_used is a boolean, convert to '1' or '0'
    optimization_used_str = '1' if optimization_used else '0'

    payload = {
        'apikey': ETHERSCAN_API_KEY,
        'module': 'contract',
        'action': 'verifysourcecode',
        'contractaddress': contract_address,
        'sourceCode': source_code,
        'codeformat': 'solidity-single-file',  # Assuming single file for simplicity
        'contractname': contract_name,
        'compilerversion': compiler_version,
        'optimizationUsed': optimization_used_str,
        'runs': str(runs),
    }

    try:
        print(f"DEBUG: Sending verification request to {ETHERSCAN_API_BASE_URL} for {contract_address}")
        response = requests.post(ETHERSCAN_API_BASE_URL, data=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()
        print(f"DEBUG: Etherscan verification response: {result}")

        # Etherscan API returns a 'status' (0=fail, 1=success) and 'result' message
        if result.get('status') == '1':
            # Verification typically returns a GUID as a result, which you can then check status with 'checkverifystatus'
            return f"Verification initiated successfully! GUID: {result.get('result')}. Check status on block explorer."
        else:
            return f"Verification failed: {result.get('result', 'Unknown error.')}"
    except requests.exceptions.RequestException as e:
        return f"Network or API request error: {str(e)}. Check ETHERSCAN_API_BASE_URL and network connectivity."
    except Exception as e:
        return f"An unexpected error occurred during verification: {str(e)}"
