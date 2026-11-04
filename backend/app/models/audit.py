import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Date
from ..database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(64), nullable=True)
    user_role = Column(String(32), nullable=True)
    action = Column(String(64), nullable=False) # LOGIN, VIEW_BENEFICIARY, CREATE_BENEFICIARY, UPDATE_ANC, FLAG_HIGH_RISK, EMERGENCY_REFERRAL, EXPORT_REPORT, RESOLVE_CONFLICT
    target_entity = Column(String(64), nullable=True)
    target_id = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "username": self.username,
            "user_role": self.user_role,
            "action": self.action,
            "target_entity": self.target_entity,
            "target_id": self.target_id,
            "details": self.details,
            "ip_address": self.ip_address,
        }

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_code = Column(String(64), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    organization = Column(String(128), nullable=False) # MoHFW, NHM, TNHSP
    version = Column(String(32), nullable=False)
    publication_date = Column(Date, nullable=True)
    content_json = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "document_code": self.document_code,
            "title": self.title,
            "organization": self.organization,
            "version": self.version,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "is_approved": self.is_approved,
        }

