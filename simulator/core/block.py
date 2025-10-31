import json
from typing import List, Optional
import hashlib


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
            "merkle_root": self.merkle_root() if hasattr(self, 'merkle_root') else None,
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

    def merkle_root(self) -> Optional[str]:
        """Compute a simple Merkle root over the TXs (hash of tx JSON canonical). Returns hex str or None."""
        try:
            if not self.txs:
                return None
            leaves = []
            for tx in self.txs:
                s = json.dumps(tx, sort_keys=True, separators=(",",":"), ensure_ascii=False)
                leaves.append(hashlib.sha256(s.encode('utf-8')).hexdigest())
            # build up the tree
            while len(leaves) > 1:
                if len(leaves) % 2 == 1:
                    leaves.append(leaves[-1])
                new = []
                for i in range(0, len(leaves), 2):
                    new.append(hashlib.sha256((leaves[i] + leaves[i+1]).encode('utf-8')).hexdigest())
                leaves = new
            return leaves[0]
        except Exception:
            return None
