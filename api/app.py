from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from simulator.core.blockchain import Blockchain
from simulator.core.transaction import Transaction
from simulator.storage import load_chain
import os
from simulator.storage import save_mempool, load_mempool
from fastapi import APIRouter

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
# Estado global simple (in-memory)
bc = Blockchain(difficulty=3)

# attempt to load persisted chain from ./data/chain.json (local JSON persistence)
try:
    data_dir = os.environ.get("DATA_DIR", ".")
    chain_path = os.path.join(data_dir, "data", "chain.json")
    loaded = load_chain(chain_path)
    if loaded:
        bc.import_from_json(chain_path)
except Exception:
    # if load fails, continue with fresh chain
    pass

from .jobs import router as jobs_router
app.include_router(jobs_router, prefix="/jobs")
from .internal import router as internal_router
app.include_router(internal_router, prefix="/_internal")


@app.post("/transactions")
def add_transaction(payload: dict):
    try:
        tx = Transaction.from_dict(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    bc.add_transaction(tx)
    # persist mempool to data/mempool.json
    try:
        data_dir = os.environ.get("DATA_DIR", ".")
        save_mempool(data_dir, [t.to_dict() for t in bc.mempool])
    except Exception:
        pass
    return {"status":"ok"}

@app.get("/mempool")
def get_mempool():
    return [t.to_dict() for t in bc.mempool]

@app.get("/chain")
def get_chain():
    # normalize block representation for the UI (use 'transactions' key expected by UI)
    out = []
    for b in bc.chain:
        d = b.to_dict()
        # older code may have 'txs'; expose as 'transactions' for UI convenience
        if 'txs' in d and 'transactions' not in d:
            d['transactions'] = d['txs']
        out.append(d)
    return out


@app.get("/difficulty")
def get_difficulty():
    return {"difficulty": bc.difficulty}

@app.get("/validate")
def validate():
    valid, details = bc.validate_chain()
    return {"valid": valid, "details": details}

@app.post("/blocks/{index}/tamper")
def tamper(index: int, payload: dict):
    recompute = payload.get("recompute_hash", False)
    new_data = payload.get("new_data", {})
    try:
        bc.tamper_block(index, new_data, recompute_hash=recompute)
    except IndexError:
        raise HTTPException(status_code=404, detail="block not found")
    return {"status":"ok"}
