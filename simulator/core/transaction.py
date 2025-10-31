from dataclasses import dataclass, asdict
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    sender: str
    recipient: str
    amount: float
    message: Optional[str] = None

    def __post_init__(self):
        if not self.sender or not self.recipient:
            raise ValueError("sender and recipient must be non-empty")
        if not isinstance(self.amount, (int, float)) or self.amount <= 0:
            raise ValueError("amount must be a positive number")

    def to_dict(self) -> dict:
        d = {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": float(self.amount),
        }
        if self.message:
            d["message"] = self.message
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Transaction":
        return cls(
            sender=d.get("sender", ""),
            recipient=d.get("recipient", ""),
            amount=d.get("amount", 0),
            message=d.get("message"),
        )
