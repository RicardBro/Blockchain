from fastapi import APIRouter, HTTPException
from .app import bc
from simulator.storage import save_chain
import os
import threading
import time
import json
import hashlib
from simulator.storage import list_inflight
from simulator.core.block import Block

router = APIRouter()

@router.post("/add_block")
def add_block(block_payload: dict):
    # Validate incoming block: prev_hash, recomputed hash, and difficulty
    try:
        from simulator.core.block import Block
        b = Block.from_dict(block_payload)
        # verify prev_hash
        if b.prev_hash != bc.chain[-1].hash:
            raise HTTPException(status_code=400, detail="prev_hash mismatch")
        # recompute hash and compare
        provided_hash = block_payload.get("hash")
        computed = b.compute_hash()
        if provided_hash is None:
            raise HTTPException(status_code=400, detail="missing hash in payload")
        if provided_hash != computed:
            raise HTTPException(status_code=400, detail="hash mismatch")
        # verify difficulty
        prefix = "0" * bc.difficulty
        if not provided_hash.startswith(prefix):
            raise HTTPException(status_code=400, detail="insufficient difficulty")
        # append
        b.hash = provided_hash
        bc.chain.append(b)
        # persist chain to disk (local JSON) -- data folder is mounted by compose
        data_dir = os.environ.get("DATA_DIR", ".")
        chain_path = os.path.join(data_dir, "data", "chain.json")
        try:
            save_chain(chain_path, [bb.to_dict() for bb in bc.chain])
        except Exception:
            # persistence failure should not block acceptance
            pass
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def miner_status_path():
    data_dir = os.environ.get("DATA_DIR", ".")
    return os.path.join(data_dir, "data", "miner_status.json")


def write_miner_status(obj: dict):
    try:
        path = miner_status_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # add server-side timestamp and write atomically
        obj = dict(obj)
        obj.setdefault("ts", int(time.time()))
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        os.replace(path + ".tmp", path)
        # also append to miner_logs.json for historical logs
        try:
            logs_path = os.path.join(os.path.dirname(path), 'miner_logs.json')
            if os.path.exists(logs_path):
                try:
                    logs = json.load(open(logs_path, 'r', encoding='utf-8'))
                except Exception as e:
                    print('warning: could not parse existing miner_logs.json, starting fresh:', e)
                    logs = []
            else:
                logs = []
            logs.append(obj)
            try:
                with open(logs_path + '.tmp', 'w', encoding='utf-8') as lf:
                    json.dump(logs, lf, ensure_ascii=False, indent=2)
                os.replace(logs_path + '.tmp', logs_path)
            except Exception as e:
                print('error writing miner_logs.json:', e)
        except Exception:
            # surface internal errors so we can diagnose persistence issues
            import traceback
            print('exception during miner_logs append:', traceback.format_exc())
    except Exception:
        import traceback
        print('exception in write_miner_status:', traceback.format_exc())


def read_miner_status():
    try:
        path = miner_status_path()
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"state": "idle"}


def _background_mine_using_inflight(claim_file_path: str, claim_id: str):
    # read txs
    try:
        with open(claim_file_path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception:
        write_miner_status({"state": "error", "msg": "could not read claim"})
        return

    txs = doc.get("txs", [])
    write_miner_status({"state": "mining", "claim_id": claim_id, "txs": len(txs), "nonce": 0, "attempts": 0})

    # build block template
    try:
        prev_hash = bc.chain[-1].hash
        index = bc.chain[-1].index + 1
    except Exception:
        prev_hash = "0"
        index = 0
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    block = {
        "index": index,
        "timestamp": timestamp,
        "txs": txs,
        "prev_hash": prev_hash,
        "nonce": 0,
    }

    prefix = "0" * bc.difficulty
    nonce = 0
    attempts = 0
    try:
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
            attempts += 1
            if nonce % 100 == 0:
                write_miner_status({
                    "state": "mining",
                    "claim_id": claim_id,
                    "txs": len(txs),
                    "nonce": nonce,
                    "hash": h,
                    "attempts": attempts,
                    "difficulty": bc.difficulty,
                })
            if h.startswith(prefix):
                block["hash"] = h
                # append to bc.chain
                b = Block.from_dict(block)
                b.hash = h
                bc.chain.append(b)
                # persist chain
                data_dir = os.environ.get("DATA_DIR", ".")
                chain_path = os.path.join(data_dir, "data", "chain.json")
                try:
                    save_chain(chain_path, [bb.to_dict() for bb in bc.chain])
                except Exception:
                    pass
                # remove inflight claim file
                try:
                    os.remove(claim_file_path)
                except Exception:
                    pass
                write_miner_status({"state": "done", "claim_id": claim_id, "block_index": index, "hash": h, "attempts": attempts})
                # server-side record: miner finished
                try:
                    from simulator.storage import append_ui_event
                    append_ui_event(data_dir, f"Miner finished claim {claim_id} -> block {index} (attempts={attempts})")
                except Exception:
                    pass
                return
            nonce += 1
    except Exception as e:
        write_miner_status({"state": "error", "msg": str(e)})


@router.post("/force_mine")
def force_mine():
    """Start a background mining job using the first available inflight claim or mempool.
    Returns 202 if started or 409 if already mining.
    """
    status = read_miner_status()
    if status.get("state") == "mining":
        raise HTTPException(status_code=409, detail="miner already active")

    data_dir = os.environ.get("DATA_DIR", ".")
    d = os.path.join(data_dir, "data")
    # prefer existing inflight
    infls = [f for f in os.listdir(d) if f.startswith("mempool_inflight_")] if os.path.isdir(d) else []
    if infls:
        fpath = os.path.join(d, infls[0])
        claim_id = infls[0].replace("mempool_inflight_", "").replace('.json','')
        # server-side record: force_mine started on existing inflight
        try:
            from simulator.storage import append_ui_event
            append_ui_event(data_dir, f"Force_mine arrancado (inflight): {claim_id}")
        except Exception:
            pass
        t = threading.Thread(target=_background_mine_using_inflight, args=(fpath, claim_id), daemon=True)
        t.start()
        return {"status": "started", "claim_id": claim_id}

    # fallback: try to mine directly from mempool.json if present
    mp = os.path.join(d, "mempool.json")
    try:
        if os.path.exists(mp):
            with open(mp, "r", encoding="utf-8") as fh:
                arr = json.load(fh)
            if arr:
                claim_id = str(__import__('uuid').uuid4())
                fpath = os.path.join(d, f"mempool_inflight_{claim_id}.json")
                with open(fpath + ".tmp", "w", encoding="utf-8") as out:
                    json.dump({"ts": int(time.time()), "claim_id": claim_id, "txs": arr}, out, ensure_ascii=False)
                os.replace(fpath + ".tmp", fpath)
                try:
                    os.remove(mp)
                except Exception:
                    pass
                # server-side record: force_mine started on mempool
                try:
                    from simulator.storage import append_ui_event
                    append_ui_event(data_dir, f"Force_mine arrancado (mempool->inflight): {claim_id}")
                except Exception:
                    pass
                t = threading.Thread(target=_background_mine_using_inflight, args=(fpath, claim_id), daemon=True)
                t.start()
                return {"status": "started", "claim_id": claim_id}
    except Exception:
        pass

    # nothing to mine
    raise HTTPException(status_code=404, detail="no inflight or mempool to mine")


@router.get("/miner_status")
def miner_status():
    return read_miner_status()


@router.post("/report_status")
def report_status(payload: dict):
    """Endpoint for external miners to report status snapshots.
    This accepts a dict and writes it via write_miner_status so historical logs are kept.
    """
    try:
        write_miner_status(payload)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
