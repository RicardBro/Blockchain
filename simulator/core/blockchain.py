import time
from typing import List, Tuple, Callable, Optional
from .block import Block
from .transaction import Transaction


class Blockchain:
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []
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
