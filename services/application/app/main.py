"""application(申込)サービス。

顧客が商品に対して行う申込(300件)を提供するREST API。審査を経て
一部(200件)が契約(policy)に接続される。
"""
from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("application"), id_field="application_id", id_prefix="APP", id_width=6)

app = FastAPI(
    title="申込サービス (Application Service)",
    description="保険の申込を管理するAPI。審査ステータス(審査中/承認/却下/取消)と、承認時の契約IDを保持します。",
    version="1.0.0",
    openapi_tags=[{"name": "applications", "description": "申込の参照・管理"}],
)


class HealthDeclaration(BaseModel):
    has_pre_existing_condition: bool = Field(..., description="既往症の有無")
    notes: str | None = Field(None, description="告知の補足")


class Beneficiary(BaseModel):
    name: str = Field(..., description="受取人氏名")
    relationship: str = Field(..., description="続柄", examples=["配偶者"])


class InsuredPet(BaseModel):
    species: str = Field(..., description="種別", examples=["犬"])
    breed: str = Field(..., description="品種", examples=["トイプードル"])
    name: str = Field(..., description="ペットの名前", examples=["ポチ"])
    age: int = Field(..., description="ペットの年齢")


class ApplicationBase(BaseModel):
    customer_id: str = Field(..., description="申込者(顧客ID)", examples=["CUS-000001"])
    product_id: str = Field(..., description="申込商品(商品ID)", examples=["PRD-001"])
    application_date: str = Field(..., description="申込日(YYYY-MM-DD)")
    desired_sum_insured: int = Field(..., description="希望保険金額(円)")
    desired_payment_period: str = Field(..., description="希望払込期間")
    payment_method: str = Field(..., description="支払方法", examples=["口座振替"])
    health_declaration: HealthDeclaration | None = Field(None, description="告知内容(医療・傷害保険のみ)")
    beneficiary: Beneficiary | None = Field(None, description="受取人(傷害保険の死亡保障のみ)")
    insured_pet: InsuredPet | None = Field(None, description="被保険動物(ペット保険のみ)")
    status: str = Field(..., description="審査ステータス", examples=["承認"])
    reviewed_at: str | None = Field(None, description="審査完了日時")
    rejection_reason: str | None = Field(None, description="却下理由(却下時のみ)")
    resulting_policy_id: str | None = Field(None, description="契約化された場合の契約ID")


class Application(ApplicationBase):
    application_id: str = Field(..., description="申込ID(APP-NNNNNN)", examples=["APP-000001"])
    created_at: str
    updated_at: str


class ApplicationList(BaseModel):
    total: int
    items: list[Application]


@app.get("/health", tags=["health"], summary="ヘルスチェック")
def health():
    return {"status": "ok", "service": "application"}


@app.get("/applications", response_model=ApplicationList, tags=["applications"], summary="申込一覧の取得")
def list_applications(
    customer_id: str | None = Query(None, description="顧客IDで絞り込み"),
    product_id: str | None = Query(None, description="商品IDで絞り込み"),
    status_: str | None = Query(None, alias="status", description="ステータスで絞り込み"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    filters = {"customer_id": customer_id, "product_id": product_id, "status": status_}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/applications/{application_id}", response_model=Application, tags=["applications"], summary="申込の取得")
def get_application(application_id: str):
    record = store.get(application_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"申込が見つかりません: {application_id}")
    return record


@app.post("/applications", response_model=Application, status_code=status.HTTP_201_CREATED, tags=["applications"], summary="申込の新規登録")
def create_application(payload: ApplicationBase):
    now = now_jst()
    return store.create({**payload.model_dump(), "created_at": now, "updated_at": now})


@app.put("/applications/{application_id}", response_model=Application, tags=["applications"], summary="申込の更新")
def update_application(application_id: str, payload: ApplicationBase):
    record = store.update(application_id, {**payload.model_dump(), "updated_at": now_jst()})
    if record is None:
        raise HTTPException(status_code=404, detail=f"申込が見つかりません: {application_id}")
    return record


@app.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["applications"], summary="申込の削除")
def delete_application(application_id: str):
    if not store.delete(application_id):
        raise HTTPException(status_code=404, detail=f"申込が見つかりません: {application_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
