"""
Dispute management endpoints
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from models import DisputeForm, DisputeStatus, DisputeListResponse, DisputeDetailResponse
from constants import BANKS
from database import db
from dispute_service import DisputeService

router = APIRouter(prefix="/api", tags=["disputes"])


@router.post("/dispute", response_model=Dict[str, Any])
async def create_dispute(dispute: DisputeForm):
    """Create a new dispute"""
    try:
        return await DisputeService.create_dispute(dispute)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dispute/{dispute_id}", response_model=DisputeDetailResponse)
async def get_dispute(dispute_id: str):
    """Get dispute by ID"""
    try:
        dispute_info = DisputeService.get_dispute_status_update(dispute_id)
        return DisputeDetailResponse(
            dispute=dispute_info["dispute"],
            timeline=dispute_info["timeline"]
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Dispute not found")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disputes", response_model=DisputeListResponse)
async def list_disputes(status: Optional[DisputeStatus] = None, bank: Optional[str] = None):
    """List all disputes with optional filtering"""
    try:
        filtered_disputes = db.list_disputes(status, bank)
        summary = db.get_dispute_summary()
        
        return DisputeListResponse(
            disputes=filtered_disputes,
            total=len(filtered_disputes),
            summary=summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guidance/{dispute_type}")
async def get_guidance(dispute_type: str):
    """Get guidance for specific dispute type"""
    try:
        return await DisputeService.get_dispute_guidance(dispute_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/banks")
async def get_banks():
    """Get list of supported banks with contact information"""
    from constants import BANK_HELPLINES
    
    bank_info = []
    for bank in BANKS:
        info = {
            "name": bank,
            "helpline": BANK_HELPLINES.get(bank, "Contact bank directly"),
            "dispute_email": f"disputes@{bank.lower().replace(' ', '')}.com" if bank != "Other" else None,
            "online_portal": f"https://{bank.lower().replace(' ', '')}.com/disputes" if bank != "Other" else None
        }
        bank_info.append(info)
    
    return {"banks": bank_info}
