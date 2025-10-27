from fastapi import APIRouter, HTTPException
from .app import bc

router = APIRouter()

@router.post("/add_block")
def add_block(block_payload: dict):
    # Minimal acceptance: append block if prev_hash matches
    try:
        from simulator.core.block import Block
        b = Block.from_dict(block_payload)
        if b.prev_hash != bc.chain[-1].hash:
            raise HTTPException(status_code=400, detail="prev_hash mismatch")
        # set as is
        bc.chain.append(b)
        return {"status":"ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
