"""claim(保険金請求)サービス。

有効な契約(policy)に対する保険金請求(50件)を提供するREST API。
請求種別は対象契約の商品カテゴリと整合している。
"""
from fastapi import FastAPI, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("claim"), id_field="claim_id", id_prefix="CLM", id_width=6)

app = FastAPI(
    title="Property Insurance Claim API",
    description=(
        "Manage property insurance claim (claims) against insurance policies. "
        "Find claimants, claim types, incident dates, requested and paid amounts, "
        "and claim review or payment status."
    ),
    version="1.0.0",
    openapi_tags=[{"name": "claims", "description": "Read and manage property insurance claim (claims)."}],
)


class ClaimBase(BaseModel):
    policy_id: str = Field(..., description="Insurance policy ID against which the claim is filed.", examples=["POL-000001"])
    customer_id: str = Field(..., description="Customer ID of the insurance claimant.", examples=["CUS-000001"])
    claim_type: str = Field(..., description="Type of insurance claim or covered loss; depends on the policy's product category. Values remain in Japanese.", examples=["入院"])
    incident_date: str = Field(..., description="Date of the accident, loss, or event behind the claim (YYYY-MM-DD).")
    claim_date: str = Field(..., description="Date the insurance claim was filed (YYYY-MM-DD).")
    claim_amount_requested: int = Field(..., description="Insurance claim amount requested in Japanese yen.")
    claim_amount_paid: int | None = Field(None, description="Final insurance claim payment amount in Japanese yen, if determined.")
    status: str = Field(..., description="Insurance claim review or payment status. Values remain in Japanese.", examples=["支払済"])
    description: str | None = Field(None, description="Details of the insurance claim, incident, and covered loss.")
    processed_at: str | None = Field(None, description="Date and time the insurance claim review finished.")


class Claim(ClaimBase):
    claim_id: str = Field(..., description="Insurance claim ID (CLM-NNNNNN).", examples=["CLM-000001"])
    created_at: str
    updated_at: str


class ClaimList(BaseModel):
    total: int
    items: list[Claim]


@app.get("/health", tags=["health"], summary="Check service health")
def health():
    return {"status": "ok", "service": "claim"}


@app.get("/claims", response_model=ClaimList, tags=["claims"], summary="List insurance claims", description="List property insurance claim (claims), optionally filtered by insurance policy, claimant customer, or claim review status.")
def list_claims(
    policy_id: str | None = Query(None, description="Filter insurance claims by the policy ID (POL-NNNNNN) on which the claims were filed."),
    customer_id: str | None = Query(None, description="Filter insurance claims by claimant customer ID (CUS-NNNNNN)."),
    status_: str | None = Query(None, alias="status", description="Filter insurance claims by claim review or payment status. Values remain in Japanese."),
    skip: int = Query(0, ge=0, description="Number of insurance claims to skip for pagination."),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of insurance claims to return (1 to 100)."),
):
    filters = {"policy_id": policy_id, "customer_id": customer_id, "status": status_}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/claims/{claim_id}", response_model=Claim, tags=["claims"], summary="Get an insurance claim", description="Get one property insurance claim by claim ID, including the loss, requested amount, and payment status.")
def get_claim(claim_id: str = Path(..., description="ID of the insurance claim to retrieve (CLM-NNNNNN).")):
    record = store.get(claim_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"請求が見つかりません: {claim_id}")
    return record


@app.post("/claims", response_model=Claim, status_code=status.HTTP_201_CREATED, tags=["claims"], summary="Create an insurance claim", description="File a property insurance claim against an insurance policy.")
def create_claim(payload: ClaimBase):
    now = now_jst()
    return store.create({**payload.model_dump(), "created_at": now, "updated_at": now})


@app.put("/claims/{claim_id}", response_model=Claim, tags=["claims"], summary="Update an insurance claim", description="Replace a property insurance claim by claim ID, including review and payment details.")
def update_claim(payload: ClaimBase, claim_id: str = Path(..., description="ID of the insurance claim to update (CLM-NNNNNN).")):
    record = store.update(claim_id, {**payload.model_dump(), "updated_at": now_jst()})
    if record is None:
        raise HTTPException(status_code=404, detail=f"請求が見つかりません: {claim_id}")
    return record


@app.delete("/claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["claims"], summary="Delete an insurance claim", description="Delete a property insurance claim by claim ID.")
def delete_claim(claim_id: str = Path(..., description="ID of the insurance claim to delete (CLM-NNNNNN).")):
    if not store.delete(claim_id):
        raise HTTPException(status_code=404, detail=f"請求が見つかりません: {claim_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
