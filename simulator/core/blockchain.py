import time
import threading
from typing import List, Tuple, Callable, Optional
from .block import Block
from .transaction import Transaction
from .miner import Miner


class Blockchain:
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []
        # lock to protect chain and mempool when mining in background
        self._lock = threading.Lock()
        # background miner instance (if started)
        self._miner = None
        self.create_genesis_block()

    def create_genesis_block(self) -> Block:
        genesis = Block(index=0, timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), txs=[], prev_hash="0", nonce=0)
        genesis.hash = genesis.compute_hash()
        # annotate genesis with difficulty so clients can read mining cost
        g = genesis.to_dict()
        g["difficulty"] = self.difficulty
        # store Block instance but keep difficulty accessible via chain[0].difficulty when exported
        self.chain = [genesis]
        return genesis

    def add_transaction(self, tx: Transaction) -> None:
        if not isinstance(tx, Transaction):
            raise ValueError("tx must be Transaction")
        self.mempool.append(tx)

    def mine_block(self, miner_callback: Optional[Callable[[int, str], None]] = None, max_txs: Optional[int] = None) -> Block:
        txs = [t.to_dict() for t in self.mempool]
        if max_txs is not None:
            txs = txs[:max_txs]
        index = len(self.chain)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        prev_hash = self.chain[-1].hash
        block = Block(index=index, timestamp=timestamp, txs=txs, prev_hash=prev_hash, nonce=0)
        prefix = "0" * self.difficulty
        nonce = 0
        while True:
            block.nonce = nonce
            h = block.compute_hash()
            if miner_callback and nonce % 100 == 0:
                miner_callback(nonce, h)
            if h.startswith(prefix):
                block.hash = h
                # remove included txs from mempool
                if max_txs is None:
                    self.mempool = []
                else:
                    self.mempool = self.mempool[len(txs):]
                self.chain.append(block)
                return block
            nonce += 1

    def validate_chain(self) -> Tuple[bool, List[dict]]:
        details = []
        for i, block in enumerate(self.chain):
            valid = True
            reason = None
            # verify hash
            computed = block.compute_hash()
            if block.hash != computed:
                valid = False
                reason = "hash_mismatch"
            # verify prev_hash
            if i > 0 and block.prev_hash != self.chain[i - 1].hash:
                valid = False
                reason = reason or "prev_hash_mismatch"
            details.append({"index": block.index, "valid": valid, "reason": reason})
        is_valid = all(d["valid"] for d in details)
        return is_valid, details

    def tamper_block(self, index: int, new_data: dict, recompute_hash: bool = False) -> None:
        if index < 0 or index >= len(self.chain):
            raise IndexError("block index out of range")
        blk = self.chain[index]
        # Apply changes from new_data onto block fields (support txs and timestamp)
        if "txs" in new_data:
            blk.txs = new_data["txs"]
        if "timestamp" in new_data:
            blk.timestamp = new_data["timestamp"]
        if recompute_hash:
            blk.hash = blk.compute_hash()

    def _append_block(self, block: Block, num_included: int) -> None:
        """Append a mined block to the chain in a thread-safe manner and update mempool.

        num_included: number of transactions from the mempool that were included in this block.
        If num_included is None, we assume all transactions were included.
        """
        with self._lock:
            # remove included txs from mempool
            if num_included is None:
                self.mempool = []
            else:
                # guard against race: only remove up to current mempool length
                remove_n = min(len(self.mempool), int(num_included))
                self.mempool = self.mempool[remove_n:]
            self.chain.append(block)

    def start_mining_async(self, miner_callback: Optional[Callable[[int, str], None]] = None, max_txs: Optional[int] = None) -> None:
        """Start background mining using the Miner helper. Non-blocking.

        miner_callback will be called periodically with (nonce, hash).
        """
        # if already running, ignore
        if self._miner and getattr(self._miner, "_thread", None) and self._miner._thread.is_alive():
            return
        self._miner = Miner(self, self.difficulty)
        self._miner.start(miner_callback=miner_callback, max_txs=max_txs)

    def stop_mining(self) -> None:
        """Stop any running background miner."""
        if self._miner:
            try:
                self._miner.stop()
            except Exception:
                pass

    def export_to_json(self, path: str) -> None:
        import json

        with open(path, "w", encoding="utf-8") as f:
            arr = [b.to_dict() for b in self.chain]
            # include difficulty on first block for readers
            if arr:
                arr[0]["difficulty"] = self.difficulty
            json.dump(arr, f, ensure_ascii=False, indent=2)

    def import_from_json(self, path: str) -> None:
        import json

        with open(path, "r", encoding="utf-8") as f:
            arr = json.load(f)
        self.chain = [Block.from_dict(d) for d in arr]
