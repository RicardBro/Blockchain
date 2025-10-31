from fastapi import APIRouter, HTTPException
from simulator.storage import claim_mempool, release_claim, load_mempool, save_mempool
import os
import json
from .app import bc

router = APIRouter()


@router.post("/claim")
def claim():
    base = os.environ.get("DATA_DIR", ".")
    # JOB_TTL controls how long a claim is considered valid before
    # another worker may steal it. Default changed to 30s for demo responsiveness.
    ttl = int(os.environ.get("JOB_TTL", "30"))
    # If the in-memory mempool has transactions, prefer creating a claim from memory
    # (this avoids relying on disk persistence for demos).
    try:
        if getattr(bc, 'mempool', None):
            txs = [t.to_dict() for t in bc.mempool]
            if txs:
                claim_id = str(__import__('uuid').uuid4())
                data_dir = os.path.join(base, 'data')
                os.makedirs(data_dir, exist_ok=True)
                inflight = os.path.join(data_dir, f"mempool_inflight_{claim_id}.json")
                with open(inflight + '.tmp', 'w', encoding='utf-8') as out:
                    json.dump({'ts': int(__import__('time').time()), 'claim_id': claim_id, 'txs': txs}, out, ensure_ascii=False, indent=2)
                os.replace(inflight + '.tmp', inflight)
                # clear in-memory mempool
                try:
                    bc.mempool = []
                except Exception:
                    pass
                # also remove persisted mempool.json if exists to avoid duplicate claims
                try:
                    mp = os.path.join(base, 'data', 'mempool.json')
                    if os.path.exists(mp):
                        os.remove(mp)
                except Exception:
                    pass
                # persist UI event: claim created
                try:
                    from simulator.storage import append_ui_event
                    append_ui_event(base, f"Claim creado: {claim_id} (txs={len(txs)})")
                except Exception:
                    pass
                return {"claim_id": claim_id, "txs": txs}
    except Exception:
        # on any error, fall back to disk-based claim logic
        pass

    # Persist the in-memory mempool to disk so claim_mempool can atomically move it.
    try:
        save_mempool(base, [t.to_dict() for t in bc.mempool])
    except Exception:
        pass
    claim_id, txs = claim_mempool(base, ttl=ttl)
    if claim_id is None:
        return {"claim_id": None, "txs": []}
    return {"claim_id": claim_id, "txs": txs}


@router.post("/release")
def release(payload: dict):
    claim_id = payload.get("claim_id")
    if not claim_id:
        raise HTTPException(status_code=400, detail="missing claim_id")
    base = os.environ.get("DATA_DIR", ".")
    release_claim(base, claim_id)
    return {"status": "ok"}


@router.get("/inflight")
def inflight():
    base = os.environ.get("DATA_DIR", ".")
    files = list(load_mempool(base) or [])
    # list inflight metadata files
    infl = []
    data_dir = os.path.join(base, "data")
    if os.path.isdir(data_dir):
        for f in os.listdir(data_dir):
            if f.startswith("mempool_inflight_"):
                try:
                    with open(os.path.join(data_dir, f), "r", encoding="utf-8") as fh:
                        infl.append(json.load(fh))
                except Exception:
                    continue
    return {"inflight": infl}
