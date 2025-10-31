import json
from typing import List
from .block import Block


def save_chain(chain: List[Block], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([b.to_dict() for b in chain], f, ensure_ascii=False, indent=2)


def load_chain(path: str) -> List[Block]:
    with open(path, "r", encoding="utf-8") as f:
        arr = json.load(f)
    return [Block.from_dict(d) for d in arr]
