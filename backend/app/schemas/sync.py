from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ClientSyncItem(BaseModel):
    client_tx_id: str
    entity_type: str # beneficiary, pregnancy, anc_visit, risk_factor, referral, home_visit, pnc_visit
    operation: str   # CREATE, UPDATE
    client_version: int = 1
    payload: Dict[str, Any]

class SyncPushRequest(BaseModel):
    items: List[ClientSyncItem]

class SyncPushResponse(BaseModel):
    acknowledged_ids: List[str]
    conflicts: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]

class SyncPullRequest(BaseModel):
    since_timestamp: Optional[str] = None
    village: Optional[str] = None

class ConflictResolveRequest(BaseModel):
    client_tx_id: str
    resolution_strategy: str # SERVER_WINS, CLIENT_WINS, MERGE
    resolved_payload: Optional[Dict[str, Any]] = None

