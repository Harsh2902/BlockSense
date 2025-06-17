from web3 import Web3
from web3.exceptions import TransactionNotFound, ContractLogicError
from dotenv import load_dotenv
import os, time, json

# Load environment variables
load_dotenv()

# Initialize WEB3 and ACCOUNT globally, but allow them to be updated.
# INFURA_URL will be taken from .env as a default/fallback.
WEB3 = Web3(Web3.HTTPProvider(os.getenv("INFURA_URL")))
ACCOUNT = None  # Account will be set dynamically by the user


def set_current_account(private_key: str):
    """
    Sets the global WEB3 account using the provided private key.
    WARNING: This is for demonstration. In production, keys should not
    be handled server-side this way.
    """
    global ACCOUNT
    try:
        # Ensure the private key starts with '0x' if it doesn't already
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        ACCOUNT = WEB3.eth.account.from_key(private_key)
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

    try:
        value_wei = WEB3.to_wei(amount_eth, 'ether')
        nonce = WEB3.eth.get_transaction_count(ACCOUNT.address)

        tx = {
            'to': to_address,
            'value': value_wei,
            'nonce': nonce,
            'gas': 21000,  # Standard gas limit for ETH transfer
            'gasPrice': WEB3.to_wei('50', 'gwei')  # Example gas price
        }

        signed_tx = ACCOUNT.sign_transaction(tx)
        tx_hash = WEB3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for the transaction to be mined
        tx_receipt = WEB3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

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
        balance_wei = WEB3.eth.get_balance(address)
        balance_eth = WEB3.from_wei(balance_wei, 'ether')
        return f"{balance_eth:.4f} ETH"
    except Exception as e:
        return f"❌ Error getting balance for {address}: {str(e)}"


def estimate_gas(from_address: str, to_address: str | None = None, value: float = 0, data: str | None = None) -> str:
    """Estimates the gas required for a transaction."""
    try:
        tx_params = {'from': from_address}
        if to_address:
            tx_params['to'] = to_address
        if value > 0:
            tx_params['value'] = WEB3.to_wei(value, 'ether')
        if data:
            tx_params['data'] = data

        gas_estimate = WEB3.eth.estimate_gas(tx_params)
        return f"Estimated Gas: {gas_estimate}"
    except Exception as e:
        return f"❌ Error estimating gas: {str(e)}"


def check_tx_status(tx_hash: str) -> str:
    """Checks the status of a transaction given its hash."""
    try:
        receipt = WEB3.eth.get_transaction_receipt(tx_hash)
        if receipt is None:
            return "Transaction is pending or not found."
        elif receipt.status == 1:
            return "✅ Transaction successful."
        else:
            return "❌ Transaction failed."
    except Exception as e:
        return f"❌ Error checking transaction status: {str(e)}"


def deploy_contract(bytecode: str, abi: list) -> str:  # Removed constructor_args parameter
    """
    Deploys a smart contract to the network.
    Requires a connected account to sign the transaction.
    Now assumes no constructor arguments.
    """
    if not ACCOUNT:
        raise Exception("No wallet connected. Please connect your wallet to deploy contracts.")
    try:
        contract = WEB3.eth.contract(abi=abi, bytecode=bytecode)
        nonce = WEB3.eth.get_transaction_count(ACCOUNT.address)

        # No constructor arguments used here
        gas_estimate = contract.constructor().estimate_gas({'from': ACCOUNT.address})

        tx_dict = contract.constructor().build_transaction({
            'from': ACCOUNT.address,
            'nonce': nonce,
            'gas': gas_estimate + 200000,  # Add a buffer
            'gasPrice': WEB3.to_wei('50', 'gwei')  # Example gas price
        })

        signed_tx = ACCOUNT.sign_transaction(tx_dict)
        tx_hash = WEB3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for the transaction receipt
        tx_receipt = WEB3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

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
        # Check if the method is a transaction (non-view/pure function)
        is_transaction = False
        for f in abi:
            if f.get('name') == method and f.get('type') == 'function' and f.get('stateMutability') not in ['view',
                                                                                                            'pure']:
                is_transaction = True
                break

        contract = WEB3.eth.contract(address=contract_address, abi=abi)
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
                'gasPrice': WEB3.to_wei('50', 'gwei')
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
        # Catch all other exceptions during interaction and return a message
        return f"❌ Error interacting with contract: {str(e)}"
