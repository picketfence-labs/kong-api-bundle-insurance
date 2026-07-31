"""claim(保険金請求)サービス。

有効な契約(policy)に対する保険金請求(50件)を提供するREST API。
請求種別は対象契約の商品カテゴリと整合している。
"""
from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("claim"), id_field="claim_id", id_prefix="CLM", id_width=6)

app = FastAPI(
    title="保険金請求サービス (Claim Service)",
    description="保険金請求を管理するAPI。請求種別・請求金額・支払金額・審査ステータスを保持します。",
    version="1.0.0",
    openapi_tags=[{"name": "claims", "description": "保険金請求の参照・管理"}],
)


class ClaimBase(BaseModel):
    policy_id: str = Field(..., description="請求対象契約(契約ID)", examples=["POL-000001"])
    customer_id: str = Field(..., description="請求者(顧客ID)", examples=["CUS-000001"])
    claim_type: str = Field(..., description="請求種別", examples=["入院"])
    incident_date: str = Field(..., description="事故・事由発生日(YYYY-MM-DD)")
    claim_date: str = Field(..., description="請求日(YYYY-MM-DD)")
    claim_amount_requested: int = Field(..., description="請求金額(円)")
    claim_amount_paid: int | None = Field(None, description="支払確定金額(円)")
    status: str = Field(..., description="審査ステータス", examples=["支払済"])
    description: str | None = Field(None, description="請求内容の詳細")
    processed_at: str | None = Field(None, description="審査完了日時")


class Claim(ClaimBase):
    claim_id: str = Field(..., description="請求ID(CLM-NNNNNN)", examples=["CLM-000001"])
    created_at: str
    updated_at: str


class ClaimList(BaseModel):
    total: int
    items: list[Claim]


@app.get("/health", tags=["health"], summary="ヘルスチェック")
def health():
    return {"status": "ok", "service": "claim"}


@app.get("/claims", response_model=ClaimList, tags=["claims"], summary="請求一覧の取得")
def list_claims(
    policy_id: str | None = Query(None, description="契約IDで絞り込み"),
    customer_id: str | None = Query(None, description="顧客IDで絞り込み"),
    status_: str | None = Query(None, alias="status", description="ステータスで絞り込み"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    filters = {"policy_id": policy_id, "customer_id": customer_id, "status": status_}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/claims/{claim_id}", response_model=Claim, tags=["claims"], summary="請求の取得")
def get_claim(claim_id: str):
    record = store.get(claim_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"請求が見つかりません: {claim_id}")
    return record


@app.post("/claims", response_model=Claim, status_code=status.HTTP_201_CREATED, tags=["claims"], summary="請求の新規登録")
def create_claim(payload: ClaimBase):
    now = now_jst()
    return store.create({**payload.model_dump(), "created_at": now, "updated_at": now})


@app.put("/claims/{claim_id}", response_model=Claim, tags=["claims"], summary="請求の更新")
def update_claim(claim_id: str, payload: ClaimBase):
    record = store.update(claim_id, {**payload.model_dump(), "updated_at": now_jst()})
    if record is None:
        raise HTTPException(status_code=404, detail=f"請求が見つかりません: {claim_id}")
    return record


@app.delete("/claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["claims"], summary="請求の削除")
def delete_claim(claim_id: str):
    if not store.delete(claim_id):
        raise HTTPException(status_code=404, detail=f"請求が見つかりません: {claim_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
