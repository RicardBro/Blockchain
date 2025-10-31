import pytest
from simulator.core.transaction import Transaction
from simulator.core.block import Block
from simulator.core.blockchain import Blockchain


def test_transaction_valid():
    tx = Transaction(sender="A", recipient="B", amount=10.5, message="hola")
    d = tx.to_dict()
    assert d["sender"] == "A"
    assert d["amount"] == 10.5


def test_block_hash_consistency():
    txs = [{"sender":"A","recipient":"B","amount":1}]
    b = Block(index=0, timestamp="2025-01-01T00:00:00", txs=txs, prev_hash="0", nonce=0)
    h1 = b.compute_hash()
    h2 = b.compute_hash()
    assert h1 == h2


def test_chain_mining_and_validation():
    bc = Blockchain(difficulty=1)
    tx = Transaction("A","B",1)
    bc.add_transaction(tx)
    block = bc.mine_block()
    assert len(bc.chain) == 2
    valid, details = bc.validate_chain()
    assert valid


def test_tamper_detection():
    bc = Blockchain(difficulty=1)
    bc.add_transaction(Transaction("A","B",1))
    bc.mine_block()
    bc.add_transaction(Transaction("A","B",2))
    bc.mine_block()
    # tamper block 1
    bc.tamper_block(1, {"txs":[{"sender":"A","recipient":"B","amount":999}]}, recompute_hash=False)
    valid, details = bc.validate_chain()
    assert not valid
    # block 1 should be invalid
    assert details[1]["valid"] == False
