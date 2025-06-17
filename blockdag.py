import random
import datetime

# Simulate a DAG of blocks with multiple parents and mock transactions
def get_blockdag_data(num_blocks=12):
    blocks = []
    for i in range(num_blocks):
        block_id = f"B{i}"
        timestamp = datetime.datetime.now() - datetime.timedelta(minutes=(num_blocks - i) * 2)

        # Assign 1-2 parents randomly from earlier blocks (except for genesis)
        if i == 0:
            parents = []
        elif i == 1:
            parents = [blocks[0]['id']]
        else:
            parents = random.sample([b['id'] for b in blocks[:i]], k=random.randint(1, 2))

        tx_count = random.randint(1, 6)
        transactions = [
            {
                "from": f"0x{random.randint(10**15, 10**16 - 1):x}",
                "to": f"0x{random.randint(10**15, 10**16 - 1):x}",
                "value": round(random.uniform(0.01, 1.0), 4)
            }
            for _ in range(tx_count)
        ]

        block = {
            "id": block_id,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "parents": parents,
            "tx_count": tx_count,
            "transactions": transactions,
            "producer": f"Miner-{random.randint(1, 4)}"
        }
        blocks.append(block)

    return blocks[::-1]  # Return with newest block last
