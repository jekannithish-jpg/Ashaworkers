import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from ..database import Base

class SyncQueueItem(Base):
    __tablename__ = "sync_queue"

    id = Column(Integer, primary_key=True, index=True)
    client_tx_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entity_type = Column(String(64), nullable=False)
    # beneficiary, pregnancy, anc_visit, risk_factor, referral, home_visit, pnc_visit
    operation = Column(String(32), nullable=False) # CREATE, UPDATE
    client_version = Column(Integer, default=1)
    payload_json = Column(Text, nullable=False)
    sync_state = Column(String(32), default="WAITING_TO_SYNC")
    # WAITING_TO_SYNC, SYNCHRONIZED, CONFLICT_REQUIRES_REVIEW, SYNCHRONIZATION_FAILED
    server_acknowledged_at = Column(DateTime, nullable=True)
    conflict_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    retry_count = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "client_tx_id": self.client_tx_id,
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "operation": self.operation,
            "client_version": self.client_version,
            "payload_json": self.payload_json,
            "sync_state": self.sync_state,
            "server_acknowledged_at": self.server_acknowledged_at.isoformat() if self.server_acknowledged_at else None,
            "conflict_details": self.conflict_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "retry_count": self.retry_count,
        }

