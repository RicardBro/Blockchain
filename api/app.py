from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from simulator.core.blockchain import Blockchain
from simulator.core.transaction import Transaction

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Estado global simple (in-memory)
bc = Blockchain(difficulty=3)

@app.post("/transactions")
def add_transaction(payload: dict):
    try:
        tx = Transaction.from_dict(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    bc.add_transaction(tx)
    return {"status":"ok"}

@app.get("/mempool")
def get_mempool():
    return [t.to_dict() for t in bc.mempool]

@app.get("/chain")
def get_chain():
    return [b.to_dict() for b in bc.chain]

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
