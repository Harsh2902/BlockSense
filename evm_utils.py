from web3 import Web3
from web3.exceptions import TransactionNotFound, ContractLogicError
from dotenv import load_dotenv
import os, time, json

# Load environment variables
load_dotenv()

# Initialize WEB3 and ACCOUNT globally. They will be set dynamically.
WEB3 = None
ACCOUNT = None


def set_evm_node(node_url: str):
    """
    Sets the global WEB3 instance to connect to the specified EVM node URL.
    Performs a connection test.
    """
    global WEB3
    try:
        provider = Web3.HTTPProvider(node_url)
        WEB3 = Web3(provider)
        # Test connection by fetching the latest block number
        if not WEB3.is_connected():
            raise Exception(f"Could not connect to EVM node at {node_url}")
        WEB3.eth.get_block_number()  # Test a simple call to confirm connectivity
        print(f"Successfully connected to EVM node at: {node_url}")
        return True
    except Exception as e:
        WEB3 = None  # Reset WEB3 on failure
        raise Exception(f"Failed to set EVM node URL to {node_url}: {str(e)}")


def set_current_account(private_key: str, node_url: str = None):
    """
    Sets the global WEB3 account and optionally updates the EVM node URL.
    WARNING: This is for demonstration. In production, keys should not
    be handled server-side this way.
    """
    global ACCOUNT
    try:
        # First, set the EVM node if a new URL is provided
        if node_url:
            set_evm_node(node_url)
        elif WEB3 is None:
            # If no node_url provided and WEB3 is not initialized, try default from env
            default_node_url = os.getenv("INFURA_URL")
            if default_node_url:
                set_evm_node(default_node_url)
            else:
                raise Exception("No EVM node URL provided and no default found.")

        if not WEB3 or not WEB3.is_connected():
            raise Exception("EVM node is not connected.")

        # Ensure the private key starts with '0x' if it doesn't already
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        ACCOUNT = WEB3.eth.account.from_key(private_key)
        # Verify if the account was successfully loaded
        if not ACCOUNT.address:
            raise ValueError("Could not derive address from private key.")
        print(f"Account set for address: {ACCOUNT.address}")
    except Exception as e:
        ACCOUNT = None  # Reset account on failure
        raise ValueError(f"Invalid private key or node configuration: {str(e)}")


def get_current_address() -> str | None:
    """Returns the address of the currently set account, or None if not set."""
    return ACCOUNT.address if ACCOUNT else None


def clear_current_account():
    """Clears the currently set global account."""
    global ACCOUNT
    ACCOUNT = None
    print("Account cleared.")


def send_eth(to_address: str, amount_wei: int) -> str:
    """Sends Ether from the connected account."""
    if not WEB3 or not WEB3.is_connected():
        return "❌ Error: EVM node not connected. Please configure EVM node."
    if not ACCOUNT:
        return "❌ Error: No wallet connected. Please connect your wallet to send ETH."

    # Ensure checksum address
    to_address = WEB3.to_checksum_address(to_address)

    try:
        nonce = WEB3.eth.get_transaction_count(ACCOUNT.address)
        tx = {
            'from': ACCOUNT.address,
            'to': to_address,
            'value': amount_wei,
            'gas': 21000,  # Standard gas limit for simple ETH transfer
            'gasPrice': WEB3.to_wei('50', 'gwei'),  # Reasonable gas price
            'nonce': nonce,
            'chainId': WEB3.eth.chain_id  # Ensure chainId is included
        }

        signed_tx = ACCOUNT.sign_transaction(tx)
        tx_hash = WEB3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = WEB3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

        status_message = 'Success' if receipt.status == 1 else 'Failed'
        return f"Transaction sent: {tx_hash.hex()}. Receipt status: {status_message}. Block: {receipt.blockNumber}"
    except Exception as e:
        return f"❌ Transaction error: {str(e)}"


def get_balance(address: str) -> str:
    """Gets the balance of an address in Ether."""
    if not WEB3 or not WEB3.is_connected():
        return "❌ Error: EVM node not connected. Please configure EVM node."
    try:
        checksum_address = WEB3.to_checksum_address(address)
        balance_wei = WEB3.eth.get_balance(checksum_address)
        balance_eth = WEB3.from_wei(balance_wei, 'ether')
        return f"✅ Balance of {address}: {balance_eth} ETH"
    except Exception as e:
        return f"❌ Error getting balance for {address}: {str(e)}"


def estimate_gas(tx_data: dict) -> str:
    """Estimates gas for a transaction."""
    if not WEB3 or not WEB3.is_connected():
        return "❌ Error: EVM node not connected. Please configure EVM node."
    try:
        gas_estimate = WEB3.eth.estimate_gas(tx_data)
        return f"✅ Estimated gas: {gas_estimate}"
    except Exception as e:
        return f"❌ Gas estimation error: {str(e)}"


def check_tx_status(tx_hash: str) -> str:
    """Checks the status of a transaction hash."""
    if not WEB3 or not WEB3.is_connected():
        return "❌ Error: EVM node not connected. Please configure EVM node."
    try:
        tx_receipt = WEB3.eth.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            return f"⏳ Transaction {tx_hash} not yet mined."
        status = "Success" if tx_receipt.status == 1 else "Failed"
        return f"✅ Transaction {tx_hash} status: {status}. Block: {tx_receipt.blockNumber}"
    except TransactionNotFound:
        return f"❌ Transaction {tx_hash} not found."
    except Exception as e:
        return f"❌ Error checking transaction status: {str(e)}"


def deploy_contract(abi: list, bytecode: str) -> str:
    """Deploys a smart contract."""
    if not WEB3 or not WEB3.is_connected():
        return "❌ Error: EVM node not connected. Please configure EVM node."
    if not ACCOUNT:
        return "❌ Error: No wallet connected. Please connect your wallet to deploy contracts."

    try:
        contract = WEB3.eth.contract(abi=abi, bytecode=bytecode)
        nonce = WEB3.eth.get_transaction_count(ACCOUNT.address)

        # Build transaction (constructor args are handled by the caller, passing empty for now)
        tx_dict = contract.constructor().build_transaction({
            'from': ACCOUNT.address,
            'nonce': nonce,
            'gasPrice': WEB3.to_wei('50', 'gwei'),
            'chainId': WEB3.eth.chain_id
        })

        # Estimate gas for deployment (add a buffer)
        estimated_gas = WEB3.eth.estimate_gas(tx_dict)
        tx_dict['gas'] = estimated_gas + 100000  # Add a buffer for deployment

        signed_tx = ACCOUNT.sign_transaction(tx_dict)
        tx_hash = WEB3.eth.send_raw_transaction(signed_tx.rawTransaction)

        tx_receipt = WEB3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)  # Increased timeout for deployment

        if tx_receipt.status == 1 and tx_receipt.contractAddress:
            return tx_receipt.contractAddress
        else:
            return f"❌ Contract deployment failed. Transaction hash: {tx_hash.hex()}. Receipt: {tx_receipt}"
    except Exception as e:
        return f"❌ Contract deployment error: {str(e)}"


def interact_with_contract(abi: list, address: str, method: str, args: list = None,
                           is_transaction: bool = False) -> any:
    """Interacts with a deployed smart contract."""
    if not WEB3 or not WEB3.is_connected():
        return "❌ Error: EVM node not connected. Please configure EVM node."

    contract_address_checksum = WEB3.to_checksum_address(address)
    contract = WEB3.eth.contract(address=contract_address_checksum, abi=abi)

    try:
        # Use getattr with a default to avoid AttributeError if method not found
        fn = getattr(contract.functions, method, None)
        if fn is None:
            return f"❌ Method '{method}' not found in contract ABI."

        if is_transaction:
            if not ACCOUNT:
                raise Exception("No wallet connected. Please connect your wallet to send transactions.")
            # Build and send transaction
            nonce = WEB3.eth.get_transaction_count(ACCOUNT.address)
            tx_dict = fn(*(args or [])).build_transaction({
                'from': ACCOUNT.address,
                'nonce': nonce,
                'gas': 2000000,  # Reasonable gas limit for interactions
                'gasPrice': WEB3.to_wei('50', 'gwei'),
                'chainId': WEB3.eth.chain_id
            })
            signed_tx = ACCOUNT.sign_transaction(tx_dict)
            tx_hash = WEB3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_receipt = WEB3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            return f"Transaction sent: {tx_hash.hex()}. Receipt status: {'Success' if tx_receipt.status == 1 else 'Failed'}"
        else:
            # Call (read-only)
            result = fn(*(args or [])).call()
            return result
    except ContractLogicError as e:
        return f"❌ Logic Error: {str(e)}"
    except Exception as e:
        # Catch all other exceptions during interaction
        return f"❌ Interaction error: {str(e)}"

