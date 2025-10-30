import subprocess
import time
import requests
import os


def test_two_miners_single_mine():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    # Start stack with two miners by overriding compose to start two instances
    env = os.environ.copy()
    # Use docker compose override (temporary) by setting COMPOSE_PROJECT_NAME to avoid collisions
    subprocess.check_call(["docker", "compose", "up", "--build", "-d", "--scale", "miner=2"], cwd=root)
    try:
        # wait for API
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                r = requests.get("http://localhost:8000/chain", timeout=2)
                if r.status_code == 200:
                    break
            except Exception:
                time.sleep(0.5)

        # post a tx
        tx = {"sender": "alice", "recipient": "bob", "amount": 2.5}
        requests.post("http://localhost:8000/transactions", json=tx, timeout=5)

        # wait up to 90s for chain to include the tx exactly once
        deadline = time.time() + 90
        found_count = 0
        while time.time() < deadline:
            c = requests.get("http://localhost:8000/chain", timeout=5).json()
            found_count = 0
            for b in c:
                for t in b.get("txs", []):
                    if t.get("sender") == "alice" and t.get("recipient") == "bob" and float(t.get("amount", 0)) == 2.5:
                        found_count += 1
            if found_count >= 1:
                break
            time.sleep(1)

        assert found_count == 1, f"Expected tx to appear exactly once, found {found_count} times"
    finally:
        subprocess.check_call(["docker", "compose", "down"], cwd=root)
