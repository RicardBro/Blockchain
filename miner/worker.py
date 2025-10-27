import time
import requests

API_URL = "http://api:8000"

POLL_INTERVAL = 1.0

while True:
    try:
        # For this minimal worker, we'll simply request the chain and if there are txs in mempool, mine one block locally
        mem = requests.get(f"{API_URL}/mempool").json()
        if mem:
            # build a block template by calling /chain to get prev_hash
            chain = requests.get(f"{API_URL}/chain").json()
            prev_hash = chain[-1]["hash"]
            index = chain[-1]["index"] + 1
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
            block = {
                "index": index,
                "timestamp": timestamp,
                "txs": mem,
                "prev_hash": prev_hash,
                "nonce": 0,
            }
            # naive PoW
            import hashlib

            difficulty = 3
            prefix = "0" * difficulty
            nonce = 0
            while True:
                block["nonce"] = nonce
                s = f"{block['index']}{block['timestamp']}{block['txs']}{block['prev_hash']}{block['nonce']}"
                h = hashlib.sha256(s.encode("utf-8")).hexdigest()
                if h.startswith(prefix):
                    block["hash"] = h
                    # send complete block to API by invoking import (not ideal but minimal)
                    # In a proper flow we'd POST /jobs/{id}/complete; here we'll call an endpoint to accept block
                    requests.post(f"{API_URL}/_internal/add_block", json=block)
                    break
                nonce += 1
        time.sleep(POLL_INTERVAL)
    except Exception as e:
        print("worker error:", e)
        time.sleep(POLL_INTERVAL)
