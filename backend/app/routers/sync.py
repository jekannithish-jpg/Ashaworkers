import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.auth import User, UserRole
from ..models.sync import SyncQueueItem
from ..models.beneficiary import Beneficiary, PregnancyRecord
from ..models.clinical import ANCVisit
from ..schemas.sync import SyncPushRequest, SyncPushResponse, SyncPullRequest, ConflictResolveRequest
from ..services.auth_service import get_current_user, log_audit
from ..services.sync_service import process_sync_push
from ..services.government_portal_adapter import gov_portal_adapter

router = APIRouter(prefix="/api/sync", tags=["Offline Synchronization Engine"])

@router.post("/push", response_model=SyncPushResponse)
def sync_push(
    request: SyncPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = [item.model_dump() for item in request.items]
    result = process_sync_push(db, current_user, items)
    return SyncPushResponse(
        acknowledged_ids=result["acknowledged_ids"],
        conflicts=result["conflicts"],
        errors=result["errors"]
    )

@router.post("/pull")
def sync_pull(
    request: SyncPullRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch active beneficiaries and updated records
    query = db.query(Beneficiary).filter(Beneficiary.is_active == True)
    if current_user.role == UserRole.ASHA and current_user.village:
        query = query.filter(Beneficiary.village == current_user.village)
    elif request.village:
        query = query.filter(Beneficiary.village == request.village)

    beneficiaries = query.all()
    b_data = [b.to_dict() for b in beneficiaries]
    b_ids = [b.beneficiary_id for b in beneficiaries]

    pregnancies = db.query(PregnancyRecord).filter(PregnancyRecord.beneficiary_id.in_(b_ids)).all()
    p_data = [p.to_dict() for p in pregnancies]
    p_ids = [p.pregnancy_id for p in pregnancies]

    anc_visits = db.query(ANCVisit).filter(ANCVisit.pregnancy_id.in_(p_ids)).all()
    anc_data = [a.to_dict() for a in anc_visits]

    return {
        "sync_timestamp": datetime.datetime.utcnow().isoformat(),
        "beneficiaries": b_data,
        "pregnancies": p_data,
        "anc_visits": anc_data
    }

@router.post("/conflict/resolve")
def resolve_conflict(
    req: ConflictResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tx = db.query(SyncQueueItem).filter(SyncQueueItem.client_tx_id == req.client_tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tx.sync_state = "SYNCHRONIZED"
    tx.conflict_details = f"Resolved via {req.resolution_strategy} by {current_user.username}"
    tx.server_acknowledged_at = datetime.datetime.utcnow()
    db.commit()

    log_audit(
        db,
        action="RESOLVE_CONFLICT",
        user=current_user,
        target_entity="sync_queue",
        target_id=req.client_tx_id,
        details=f"Strategy: {req.resolution_strategy}"
    )

    return {"message": "Conflict resolved successfully", "client_tx_id": req.client_tx_id}

@router.post("/government/test")
def sync_government_portal_test(
    beneficiary_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulates / performs government gateway sync (JANANI / ANMOL) using the GovernmentPortalAdapter.
    Validates official payload format, checks constraints, and returns sandbox acknowledgment.
    """
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == beneficiary_id).first()
    if not ben:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    
    prg = db.query(PregnancyRecord).filter(PregnancyRecord.beneficiary_id == beneficiary_id).order_by(PregnancyRecord.id.desc()).first()
    if not prg:
        raise HTTPException(status_code=404, detail="Active pregnancy record not found")

    anc = db.query(ANCVisit).filter(ANCVisit.pregnancy_id == prg.pregnancy_id).order_by(ANCVisit.scheduled_date.asc()).first()

    result = gov_portal_adapter.sync_record(
        beneficiary=ben.to_dict(),
        pregnancy=prg.to_dict(),
        anc=anc.to_dict() if anc else None
    )

    log_audit(
        db,
        action="GOV_PORTAL_SYNC_TEST",
        user=current_user,
        target_entity="beneficiary",
        target_id=beneficiary_id,
        details=f"Portal: {gov_portal_adapter.portal_type}, Status: {result['status']}"
    )

    return result
