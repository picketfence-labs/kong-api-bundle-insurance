"""product(商品)サービス。

損害保険商品のマスタ(5件固定)を提供するREST API。他サービス
(simulation/application/policy)から商品情報を参照される。
"""
from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("product"), id_field="product_id", id_prefix="PRD", id_width=3)

app = FastAPI(
    title="商品サービス (Product Service)",
    description="損害保険商品マスタを提供するAPI。火災・自動車・傷害・医療・ペットの各保険商品を管理します。",
    version="1.0.0",
    openapi_tags=[{"name": "products", "description": "商品マスタの参照・管理"}],
)


class PremiumRateTable(BaseModel):
    annual_rate_on_sum_insured: float = Field(..., description="保険金額に対する年間保険料率")
    annual_base_premium: int = Field(..., description="年間ベース保険料(円)")
    note: str | None = Field(None, description="補足")


class ProductBase(BaseModel):
    product_code: str = Field(..., description="社内商品コード", examples=["FIRE-STD"])
    product_name: str = Field(..., description="商品名(愛称含む)", examples=["火災保険「住まいの安心」"])
    category: str = Field(..., description="商品カテゴリ", examples=["火災保険"])
    description: str = Field(..., description="商品説明文")
    coverage_summary: str = Field(..., description="主契約の保障内容概要")
    min_age: int = Field(..., description="加入可能な最低年齢", examples=[18])
    max_age: int = Field(..., description="加入可能な最高年齢", examples=[99])
    policy_term: str = Field(..., description="保険期間", examples=["1〜5年"])
    min_sum_insured: int = Field(..., description="保険金額の下限(円)")
    max_sum_insured: int = Field(..., description="保険金額の上限(円)")
    premium_rate_table: PremiumRateTable = Field(..., description="保険料算出係数")
    riders: list[str] = Field(default_factory=list, description="付帯可能な特約一覧")
    status: str = Field(..., description="販売状況", examples=["販売中"])


class Product(ProductBase):
    product_id: str = Field(..., description="商品ID(PRD-NNN)", examples=["PRD-001"])
    created_at: str
    updated_at: str


class ProductList(BaseModel):
    total: int
    items: list[Product]


@app.get("/health", tags=["health"], summary="ヘルスチェック")
def health():
    return {"status": "ok", "service": "product"}


@app.get("/products", response_model=ProductList, tags=["products"], summary="商品一覧の取得")
def list_products(
    category: str | None = Query(None, description="商品カテゴリで絞り込み"),
    status_: str | None = Query(None, alias="status", description="販売状況で絞り込み"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    filters = {"category": category, "status": status_}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/products/{product_id}", response_model=Product, tags=["products"], summary="商品の取得")
def get_product(product_id: str):
    record = store.get(product_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"商品が見つかりません: {product_id}")
    return record


@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED, tags=["products"], summary="商品の新規登録")
def create_product(payload: ProductBase):
    now = now_jst()
    record = store.create({**payload.model_dump(), "created_at": now, "updated_at": now})
    return record


@app.put("/products/{product_id}", response_model=Product, tags=["products"], summary="商品の更新")
def update_product(product_id: str, payload: ProductBase):
    now = now_jst()
    record = store.update(product_id, {**payload.model_dump(), "updated_at": now})
    if record is None:
        raise HTTPException(status_code=404, detail=f"商品が見つかりません: {product_id}")
    return record


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["products"], summary="商品の削除")
def delete_product(product_id: str):
    if not store.delete(product_id):
        raise HTTPException(status_code=404, detail=f"商品が見つかりません: {product_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
