"""policy(契約)サービス。

成立した保険契約(200件)を提供するREST API。証券番号を持ち、claimの
請求対象となる。全件が承認済みの申込(application)に紐づく。
"""
from fastapi import FastAPI, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("policy"), id_field="policy_id", id_prefix="POL", id_width=6)

app = FastAPI(
    title="Property Insurance Policy API",
    description=(
        "Manage property insurance policy (policies) created from approved applications. "
        "Find policy numbers, policyholders, insured products, coverage amounts, premiums, terms, "
        "beneficiaries, and status. Insurance claims refer to these policies."
    ),
    version="1.0.0",
    openapi_tags=[{"name": "policies", "description": "Read and manage property insurance policy (policies)."}],
)


class Beneficiary(BaseModel):
    name: str = Field(..., description="Name of the insurance benefit beneficiary.")
    relationship: str = Field(..., description="Beneficiary's relationship to the insured person.")


class InsuredPet(BaseModel):
    species: str = Field(..., description="Species of the pet covered by pet insurance.")
    breed: str = Field(..., description="Breed of the insured pet.")
    name: str = Field(..., description="Name of the insured pet.")
    age: int = Field(..., description="Age of the insured pet in years.")


class PolicyBase(BaseModel):
    policy_number: str = Field(..., description="Insurance policy number printed on the policy document.", examples=["2025-FIRE-000001"])
    application_id: str = Field(..., description="Approved insurance application ID that resulted in this policy.", examples=["APP-000001"])
    customer_id: str = Field(..., description="Customer ID of the insurance policyholder.", examples=["CUS-000001"])
    product_id: str = Field(..., description="Insurance product ID covered by this policy.", examples=["PRD-001"])
    contract_date: str = Field(..., description="Date the insurance policy was contracted (YYYY-MM-DD).")
    effective_date: str = Field(..., description="Date insurance coverage begins (YYYY-MM-DD).")
    expiry_date: str | None = Field(None, description="Date insurance coverage ends (YYYY-MM-DD), if set.")
    sum_insured: int = Field(..., description="Insurance policy coverage amount or sum insured in Japanese yen.")
    premium_amount: int = Field(..., description="Insurance policy premium amount in Japanese yen.")
    premium_payment_cycle: str = Field(..., description="Frequency of insurance premium payments.", examples=["月払"])
    payment_method: str = Field(..., description="Method for paying the insurance premium.", examples=["口座振替"])
    status: str = Field(..., description="Insurance policy status. Values remain in Japanese.", examples=["有効"])
    beneficiary: Beneficiary | None = Field(None, description="Insurance benefit beneficiary information.")
    insured_pet: InsuredPet | None = Field(None, description="Pet covered by this pet insurance policy.")
    riders: list[str] = Field(default_factory=list, description="Optional insurance riders attached to this policy.")


class Policy(PolicyBase):
    policy_id: str = Field(..., description="Insurance policy ID (POL-NNNNNN).", examples=["POL-000001"])
    created_at: str
    updated_at: str


class PolicyList(BaseModel):
    total: int
    items: list[Policy]


@app.get("/health", tags=["health"], summary="Check service health")
def health():
    return {"status": "ok", "service": "policy"}


@app.get("/policies", response_model=PolicyList, tags=["policies"], summary="List insurance policies", description="List property insurance policy (policies), optionally filtered by policyholder customer, insurance product, or policy status.")
def list_policies(
    customer_id: str | None = Query(None, description="Filter insurance policies by policyholder customer ID (CUS-NNNNNN)."),
    product_id: str | None = Query(None, description="Filter insurance policies by covered insurance product ID (PRD-NNN)."),
    status_: str | None = Query(None, alias="status", description="Filter insurance policies by policy status. Values remain in Japanese."),
    skip: int = Query(0, ge=0, description="Number of insurance policies to skip for pagination."),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of insurance policies to return (1 to 100)."),
):
    filters = {"customer_id": customer_id, "product_id": product_id, "status": status_}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/policies/{policy_id}", response_model=Policy, tags=["policies"], summary="Get an insurance policy", description="Get one property insurance policy by policy ID, including coverage, premium, and policyholder details.")
def get_policy(policy_id: str = Path(..., description="ID of the insurance policy to retrieve (POL-NNNNNN).")):
    record = store.get(policy_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"契約が見つかりません: {policy_id}")
    return record


@app.post("/policies", response_model=Policy, status_code=status.HTTP_201_CREATED, tags=["policies"], summary="Create an insurance policy", description="Create a property insurance policy from an approved application.")
def create_policy(payload: PolicyBase):
    now = now_jst()
    return store.create({**payload.model_dump(), "created_at": now, "updated_at": now})


@app.put("/policies/{policy_id}", response_model=Policy, tags=["policies"], summary="Update an insurance policy", description="Replace a property insurance policy by policy ID.")
def update_policy(payload: PolicyBase, policy_id: str = Path(..., description="ID of the insurance policy to update (POL-NNNNNN).")):
    record = store.update(policy_id, {**payload.model_dump(), "updated_at": now_jst()})
    if record is None:
        raise HTTPException(status_code=404, detail=f"契約が見つかりません: {policy_id}")
    return record


@app.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["policies"], summary="Delete an insurance policy", description="Delete a property insurance policy by policy ID.")
def delete_policy(policy_id: str = Path(..., description="ID of the insurance policy to delete (POL-NNNNNN).")):
    if not store.delete(policy_id):
        raise HTTPException(status_code=404, detail=f"契約が見つかりません: {policy_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
