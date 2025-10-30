import time
import requests
import json
import hashlib

API_URL = "http://api:8000"
POLL_INTERVAL = 1.0

while True:
    try:
        # Claim work atomically from API
        claim = requests.post(f"{API_URL}/jobs/claim").json()
        claim_id = claim.get("claim_id")
        mem = claim.get("txs", []) or []
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

            # obtain difficulty from API endpoint for consistency
            try:
                difficulty = requests.get(f"{API_URL}/difficulty", timeout=2).json().get('difficulty')
            except Exception:
                try:
                    difficulty = chain[0].get("difficulty", None)
                except Exception:
                    difficulty = None
            if difficulty is None:
                difficulty = 4
            prefix = "0" * difficulty

            nonce = 0
            while True:
                block["nonce"] = nonce
                block_dict = {
                    "index": block["index"],
                    "timestamp": block["timestamp"],
                    "txs": block["txs"],
                    "prev_hash": block["prev_hash"],
                    "nonce": block["nonce"],
                }
                block_string = json.dumps(block_dict, sort_keys=True, separators=(",",":"), ensure_ascii=False)
                h = hashlib.sha256(block_string.encode("utf-8")).hexdigest()

                # report progress periodically so the API can persist miner_logs
                if nonce % 100 == 0:
                    try:
                        status = {
                            "state": "mining",
                            "claim_id": claim_id,
                            "txs": len(mem),
                            "nonce": nonce,
                            "hash": h,
                            "attempts": nonce,
                            "difficulty": difficulty,
                        }
                        requests.post(f"{API_URL}/_internal/report_status", json=status, timeout=1)
                    except Exception:
                        pass

                if h.startswith(prefix):
                    block["hash"] = h
                    # compute merkle_root if not present
                    try:
                        leaves = []
                        for tx in block.get('txs', []):
                            s = json.dumps(tx, sort_keys=True, separators=(",",":"), ensure_ascii=False)
                            leaves.append(hashlib.sha256(s.encode('utf-8')).hexdigest())
                        if leaves:
                            while len(leaves) > 1:
                                if len(leaves) % 2 == 1:
                                    leaves.append(leaves[-1])
                                new = []
                                for i in range(0, len(leaves), 2):
                                    new.append(hashlib.sha256((leaves[i] + leaves[i+1]).encode('utf-8')).hexdigest())
                                leaves = new
                            block['merkle_root'] = leaves[0]
                        else:
                            block['merkle_root'] = None
                    except Exception:
                        block['merkle_root'] = None

                    # send complete block to API by invoking internal import endpoint
                    try:
                        requests.post(f"{API_URL}/_internal/add_block", json=block, timeout=2)
                    except Exception:
                        pass

                    # notify API we finished the claim
                    if claim_id:
                        try:
                            requests.post(f"{API_URL}/jobs/release", json={"claim_id": claim_id}, timeout=1)
                        except Exception:
                            pass

                    # final report
                    try:
                        status = {"state": "done", "claim_id": claim_id, "block_index": block['index'], "hash": h, "attempts": nonce}
                        requests.post(f"{API_URL}/_internal/report_status", json=status, timeout=1)
                    except Exception:
                        pass

                    break

                nonce += 1
        time.sleep(POLL_INTERVAL)
    except Exception as e:
        print("worker error:", e)
        time.sleep(POLL_INTERVAL)
