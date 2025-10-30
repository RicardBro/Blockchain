import time
import subprocess
import requests
import os


def wait_for_url(url, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return r
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"{url} did not become available in {timeout}s")


def test_end_to_end_mininig():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    # Start stack
    subprocess.check_call(["docker", "compose", "up", "--build", "-d"], cwd=root)
    try:
        # Wait for API to be ready
        wait_for_url("http://localhost:8000/chain", timeout=30)

        # Post a transaction
        tx = {"sender": "alice", "recipient": "bob", "amount": 1.23, "message": "e2e test"}
        r = requests.post("http://localhost:8000/transactions", json=tx, timeout=5)
        assert r.status_code == 200 or r.status_code == 201 or r.json().get("status") == "ok"

        # Wait up to 60s for miner to include transaction in chain
        deadline = time.time() + 60
        found = False
        while time.time() < deadline:
            c = requests.get("http://localhost:8000/chain", timeout=5).json()
            # search tx in chain
            for b in c:
                for t in b.get("txs", []):
                    if t.get("sender") == "alice" and t.get("recipient") == "bob" and abs(float(t.get("amount",0)) - 1.23) < 1e-6:
                        found = True
                        break
                if found:
                    break
            if found:
                break
            time.sleep(1)

        assert found, "Transaction was not mined into a block within timeout"

    finally:
        subprocess.check_call(["docker", "compose", "down"], cwd=root)
