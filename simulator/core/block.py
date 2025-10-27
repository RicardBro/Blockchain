import json
from typing import List, Optional


class Block:
    def __init__(self, index: int, timestamp: str, txs: List[dict], prev_hash: str, nonce: int = 0, hash: Optional[str] = None):
        self.index = index
        self.timestamp = timestamp
        self.txs = txs
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.hash = hash

    def compute_hash(self) -> str:
        # Serializar sin el campo 'hash'
        block_dict = {
            "index": self.index,
            "timestamp": self.timestamp,
            "txs": self.txs,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        import hashlib

        return hashlib.sha256(block_string.encode("utf-8")).hexdigest()

    def to_dict(self, include_hash: bool = True) -> dict:
        d = {
            "index": self.index,
            "timestamp": self.timestamp,
            "txs": self.txs,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
        }
        if include_hash:
            d["hash"] = self.hash
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Block":
        return cls(
            index=d["index"],
            timestamp=d["timestamp"],
            txs=d.get("txs", []),
            prev_hash=d.get("prev_hash", ""),
            nonce=d.get("nonce", 0),
            hash=d.get("hash"),
        )
