"""application(申込)サービス。

顧客が商品に対して行う申込(300件)を提供するREST API。審査を経て
一部(200件)が契約(policy)に接続される。
"""
from fastapi import FastAPI, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("application"), id_field="application_id", id_prefix="APP", id_width=6)

app = FastAPI(
    title="Property Insurance Application API",
    description=(
        "Manage property insurance application (applications) submitted by customers for insurance products. "
        "Track underwriting review status, requested coverage and payment details, and the policy ID "
        "created when an application is approved."
    ),
    version="1.0.0",
    openapi_tags=[{"name": "applications", "description": "Read and manage property insurance application (applications)."}],
)


class HealthDeclaration(BaseModel):
    has_pre_existing_condition: bool = Field(..., description="Whether the applicant has a pre-existing medical condition.")
    notes: str | None = Field(None, description="Additional health declaration or medical disclosure notes.")


class Beneficiary(BaseModel):
    name: str = Field(..., description="Name of the insurance benefit beneficiary.")
    relationship: str = Field(..., description="Beneficiary's relationship to the insured person.", examples=["配偶者"])


class InsuredPet(BaseModel):
    species: str = Field(..., description="Species of the pet covered by pet insurance.", examples=["犬"])
    breed: str = Field(..., description="Breed of the insured pet.", examples=["トイプードル"])
    name: str = Field(..., description="Name of the insured pet.", examples=["ポチ"])
    age: int = Field(..., description="Age of the insured pet in years.")


class ApplicationBase(BaseModel):
    customer_id: str = Field(..., description="Customer ID of the property insurance applicant.", examples=["CUS-000001"])
    product_id: str = Field(..., description="Insurance product ID selected in the application.", examples=["PRD-001"])
    application_date: str = Field(..., description="Date the insurance application was submitted (YYYY-MM-DD).")
    desired_sum_insured: int = Field(..., description="Requested insurance coverage amount or sum insured in Japanese yen.")
    desired_payment_period: str = Field(..., description="Requested insurance premium payment period.")
    payment_method: str = Field(..., description="Method for paying the insurance premium.", examples=["口座振替"])
    health_declaration: HealthDeclaration | None = Field(None, description="Health declaration for medical or accident insurance applications.")
    beneficiary: Beneficiary | None = Field(None, description="Benefit beneficiary for accident insurance death coverage.")
    insured_pet: InsuredPet | None = Field(None, description="Pet covered by a pet insurance application.")
    status: str = Field(..., description="Insurance application underwriting review status. Values remain in Japanese.", examples=["承認"])
    reviewed_at: str | None = Field(None, description="Date and time the insurance application review finished.")
    rejection_reason: str | None = Field(None, description="Reason the insurance application was rejected, if applicable.")
    resulting_policy_id: str | None = Field(None, description="Policy ID created from an approved insurance application, if applicable.")


class Application(ApplicationBase):
    application_id: str = Field(..., description="Insurance application ID (APP-NNNNNN).", examples=["APP-000001"])
    created_at: str
    updated_at: str


class ApplicationList(BaseModel):
    total: int
    items: list[Application]


@app.get("/health", tags=["health"], summary="Check service health")
def health():
    return {"status": "ok", "service": "application"}


@app.get("/applications", response_model=ApplicationList, tags=["applications"], summary="List insurance applications", description="List property insurance application (applications), optionally filtered by customer, product, or underwriting review status.")
def list_applications(
    customer_id: str | None = Query(None, description="Filter insurance applications by applicant customer ID (CUS-NNNNNN)."),
    product_id: str | None = Query(None, description="Filter insurance applications by selected insurance product ID (PRD-NNN)."),
    status_: str | None = Query(None, alias="status", description="Filter insurance applications by underwriting review status. Values remain in Japanese."),
    skip: int = Query(0, ge=0, description="Number of insurance applications to skip for pagination."),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of insurance applications to return (1 to 100)."),
):
    filters = {"customer_id": customer_id, "product_id": product_id, "status": status_}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/applications/{application_id}", response_model=Application, tags=["applications"], summary="Get an insurance application", description="Get one property insurance application by application ID, including its review outcome and resulting policy ID.")
def get_application(application_id: str = Path(..., description="ID of the insurance application to retrieve (APP-NNNNNN).")):
    record = store.get(application_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"申込が見つかりません: {application_id}")
    return record


@app.post("/applications", response_model=Application, status_code=status.HTTP_201_CREATED, tags=["applications"], summary="Create an insurance application", description="Submit a property insurance application for a customer and insurance product.")
def create_application(payload: ApplicationBase):
    now = now_jst()
    return store.create({**payload.model_dump(), "created_at": now, "updated_at": now})


@app.put("/applications/{application_id}", response_model=Application, tags=["applications"], summary="Update an insurance application", description="Replace a property insurance application by application ID, including its underwriting review status.")
def update_application(payload: ApplicationBase, application_id: str = Path(..., description="ID of the insurance application to update (APP-NNNNNN).")):
    record = store.update(application_id, {**payload.model_dump(), "updated_at": now_jst()})
    if record is None:
        raise HTTPException(status_code=404, detail=f"申込が見つかりません: {application_id}")
    return record


@app.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["applications"], summary="Delete an insurance application", description="Delete a property insurance application by application ID.")
def delete_application(application_id: str = Path(..., description="ID of the insurance application to delete (APP-NNNNNN).")):
    if not store.delete(application_id):
        raise HTTPException(status_code=404, detail=f"申込が見つかりません: {application_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
