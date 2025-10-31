import threading
import time
import json
import hashlib
from typing import Callable, Optional


class Miner:
    """Background miner that performs Proof-of-Work in a separate thread.

    Usage:
      miner = Miner(blockchain, difficulty)
      miner.start(miner_callback=cb, max_txs=10)
      miner.stop()
    """

    def __init__(self, blockchain, difficulty: int):
        self.blockchain = blockchain
        self.difficulty = difficulty
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self, miner_callback: Optional[Callable[[int, str], None]] = None, max_txs: Optional[int] = None):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, args=(miner_callback, max_txs), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self, miner_callback: Optional[Callable[[int, str], None]], max_txs: Optional[int]):
        # Build block template from current mempool
        # We snapshot mempool to avoid long locks in blockchain
        with getattr(self.blockchain, "_lock", threading.Lock()):
            txs = [t.to_dict() for t in self.blockchain.mempool]
        if max_txs is not None:
            txs = txs[:max_txs]

        index = len(self.blockchain.chain)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        prev_hash = self.blockchain.chain[-1].hash
        block = self.blockchain.chain[-1].__class__(index=index, timestamp=timestamp, txs=txs, prev_hash=prev_hash, nonce=0)

        prefix = "0" * self.difficulty
        nonce = 0
        while not self._stop_event.is_set():
            block.nonce = nonce
            # compute hash
            block_string = json.dumps(block.to_dict(include_hash=False), sort_keys=True, separators=(",",":"), ensure_ascii=False)
            h = hashlib.sha256(block_string.encode("utf-8")).hexdigest()
            if miner_callback and nonce % 100 == 0:
                try:
                    miner_callback(nonce, h)
                except Exception:
                    # don't let callback exceptions kill the miner
                    pass
            if h.startswith(prefix):
                block.hash = h
                # append block to blockchain in a thread-safe way
                num_included = None
                if max_txs is None:
                    num_included = len(txs)
                else:
                    num_included = len(txs)
                try:
                    self.blockchain._append_block(block, num_included)
                except Exception:
                    # if append fails, stop mining
                    pass
                return
            nonce += 1
