import json
from typing import List
import os
import uuid
import time


def save_chain(path: str, chain_list: List[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chain_list, f, ensure_ascii=False, indent=2)


def load_chain(path: str) -> List[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def mempool_path(base_dir: str) -> str:
    return os.path.join(base_dir, "data", "mempool.json")


def save_mempool(base_dir: str, mempool: List[dict]) -> None:
    path = mempool_path(base_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(mempool, f, ensure_ascii=False, indent=2)
    os.replace(path + ".tmp", path)


def load_mempool(base_dir: str) -> List[dict]:
    path = mempool_path(base_dir)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def list_inflight(base_dir: str):
    d = os.path.join(base_dir, "data")
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in os.listdir(d) if f.startswith("mempool_inflight_")]


def claim_mempool(base_dir: str, ttl: int = 60):
    """
    Atomically claim the mempool: move mempool.json -> mempool_inflight_<uuid>.json and return (claim_id, mempool_list)
    If mempool.json empty, attempt to steal stale inflight claims older than ttl.
    """
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    mp = mempool_path(base_dir)
    # if mempool exists and non-empty, take it
    try:
        with open(mp, "r", encoding="utf-8") as f:
            arr = json.load(f)
        if arr:
            claim_id = str(uuid.uuid4())
            inflight = os.path.join(data_dir, f"mempool_inflight_{claim_id}.json")
            # write inflight atomically
            with open(inflight + ".tmp", "w", encoding="utf-8") as out:
                json.dump({"ts": int(time.time()), "claim_id": claim_id, "txs": arr}, out, ensure_ascii=False, indent=2)
            os.replace(inflight + ".tmp", inflight)
            # remove original mempool
            try:
                os.remove(mp)
            except Exception:
                pass
            return claim_id, arr
    except FileNotFoundError:
        pass

    # try to find stale inflight to steal
    now = int(time.time())
    for fpath in list_inflight(base_dir):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                doc = json.load(f)
            if now - doc.get("ts", 0) > ttl:
                # rename to new claim id
                new_claim = str(uuid.uuid4())
                newpath = os.path.join(data_dir, f"mempool_inflight_{new_claim}.json")
                os.replace(fpath, newpath)
                return new_claim, doc.get("txs", [])
        except Exception:
            continue
    return None, []


def release_claim(base_dir: str, claim_id: str) -> None:
    path = os.path.join(base_dir, "data", f"mempool_inflight_{claim_id}.json")
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def append_ui_event(base_dir: str, msg: str):
    """Append a [ts,msg] event to data/ui_events.json atomically.
    This is used by server-side endpoints to record timeline events for the UI.
    """
    try:
        import json
        import time
        d = os.path.join(base_dir, 'data')
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, 'ui_events.json')
        try:
            if os.path.exists(path):
                arr = json.load(open(path, 'r', encoding='utf-8'))
            else:
                arr = []
        except Exception:
            arr = []
        arr.append([int(time.time()), msg])
        with open(path + '.tmp', 'w', encoding='utf-8') as fh:
            json.dump(arr, fh, ensure_ascii=False, indent=2)
        os.replace(path + '.tmp', path)
    except Exception:
        pass
