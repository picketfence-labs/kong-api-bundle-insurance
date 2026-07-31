"""policy(契約)サービス。

成立した保険契約(200件)を提供するREST API。証券番号を持ち、claimの
請求対象となる。全件が承認済みの申込(application)に紐づく。
"""
from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("policy"), id_field="policy_id", id_prefix="POL", id_width=6)

app = FastAPI(
    title="契約サービス (Policy Service)",
    description="成立した保険契約を管理するAPI。証券番号・保険金額・保険料・契約ステータスを保持します。",
    version="1.0.0",
    openapi_tags=[{"name": "policies", "description": "契約の参照・管理"}],
)


class Beneficiary(BaseModel):
    name: str = Field(..., description="受取人氏名")
    relationship: str = Field(..., description="続柄")


class InsuredPet(BaseModel):
    species: str = Field(..., description="種別")
    breed: str = Field(..., description="品種")
    name: str = Field(..., description="ペットの名前")
    age: int = Field(..., description="ペットの年齢")


class PolicyBase(BaseModel):
    policy_number: str = Field(..., description="証券番号", examples=["2025-FIRE-000001"])
    application_id: str = Field(..., description="由来の申込ID", examples=["APP-000001"])
    customer_id: str = Field(..., description="契約者(顧客ID)", examples=["CUS-000001"])
    product_id: str = Field(..., description="契約商品(商品ID)", examples=["PRD-001"])
    contract_date: str = Field(..., description="契約日(YYYY-MM-DD)")
    effective_date: str = Field(..., description="保険始期日(YYYY-MM-DD)")
    expiry_date: str | None = Field(None, description="保険終期日(YYYY-MM-DD)")
    sum_insured: int = Field(..., description="契約保険金額(円)")
    premium_amount: int = Field(..., description="保険料(円)")
    premium_payment_cycle: str = Field(..., description="払込周期", examples=["月払"])
    payment_method: str = Field(..., description="支払方法", examples=["口座振替"])
    status: str = Field(..., description="契約ステータス", examples=["有効"])
    beneficiary: Beneficiary | None = Field(None, description="受取人情報")
    insured_pet: InsuredPet | None = Field(None, description="被保険動物(ペット保険のみ)")
    riders: list[str] = Field(default_factory=list, description="付帯特約")


class Policy(PolicyBase):
    policy_id: str = Field(..., description="契約ID(POL-NNNNNN)", examples=["POL-000001"])
    created_at: str
    updated_at: str


class PolicyList(BaseModel):
    total: int
    items: list[Policy]


@app.get("/health", tags=["health"], summary="ヘルスチェック")
def health():
    return {"status": "ok", "service": "policy"}


@app.get("/policies", response_model=PolicyList, tags=["policies"], summary="契約一覧の取得")
def list_policies(
    customer_id: str | None = Query(None, description="顧客IDで絞り込み"),
    product_id: str | None = Query(None, description="商品IDで絞り込み"),
    status_: str | None = Query(None, alias="status", description="ステータスで絞り込み"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    filters = {"customer_id": customer_id, "product_id": product_id, "status": status_}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/policies/{policy_id}", response_model=Policy, tags=["policies"], summary="契約の取得")
def get_policy(policy_id: str):
    record = store.get(policy_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"契約が見つかりません: {policy_id}")
    return record


@app.post("/policies", response_model=Policy, status_code=status.HTTP_201_CREATED, tags=["policies"], summary="契約の新規登録")
def create_policy(payload: PolicyBase):
    now = now_jst()
    return store.create({**payload.model_dump(), "created_at": now, "updated_at": now})


@app.put("/policies/{policy_id}", response_model=Policy, tags=["policies"], summary="契約の更新")
def update_policy(policy_id: str, payload: PolicyBase):
    record = store.update(policy_id, {**payload.model_dump(), "updated_at": now_jst()})
    if record is None:
        raise HTTPException(status_code=404, detail=f"契約が見つかりません: {policy_id}")
    return record


@app.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["policies"], summary="契約の削除")
def delete_policy(policy_id: str):
    if not store.delete(policy_id):
        raise HTTPException(status_code=404, detail=f"契約が見つかりません: {policy_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
