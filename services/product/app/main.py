"""product(商品)サービス。

損害保険商品のマスタ(5件固定)を提供するREST API。他サービス
(simulation/application/policy)から商品情報を参照される。
"""
from fastapi import FastAPI, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("product"), id_field="product_id", id_prefix="PRD", id_width=3)

app = FastAPI(
    title="Property Insurance Product API",
    description=(
        "Manage property insurance product (products) and coverage offerings. "
        "Find fire, auto, accident, medical, and pet insurance products, including "
        "coverage, eligibility, insured amounts, premium rates, riders, and sales status."
    ),
    version="1.0.0",
    openapi_tags=[{"name": "products", "description": "Read and manage property insurance product (products)."}],
)


class PremiumRateTable(BaseModel):
    annual_rate_on_sum_insured: float = Field(..., description="Annual premium rate applied to the sum insured.")
    annual_base_premium: int = Field(..., description="Base annual insurance premium in Japanese yen.")
    note: str | None = Field(None, description="Additional notes about the insurance premium rate.")


class ProductBase(BaseModel):
    product_code: str = Field(..., description="Internal code for the insurance product.", examples=["FIRE-STD"])
    product_name: str = Field(..., description="Insurance product name, including its marketing name.", examples=["火災保険「住まいの安心」"])
    category: str = Field(..., description="Insurance product category, such as fire, auto, accident, medical, or pet insurance.", examples=["火災保険"])
    description: str = Field(..., description="Description of the insurance product and its purpose.")
    coverage_summary: str = Field(..., description="Summary of coverage under the main insurance policy.")
    min_age: int = Field(..., description="Minimum eligible age for this insurance product.", examples=[18])
    max_age: int = Field(..., description="Maximum eligible age for this insurance product.", examples=[99])
    policy_term: str = Field(..., description="Coverage period or term of the insurance policy.", examples=["1〜5年"])
    min_sum_insured: int = Field(..., description="Minimum sum insured in Japanese yen.")
    max_sum_insured: int = Field(..., description="Maximum sum insured in Japanese yen.")
    premium_rate_table: PremiumRateTable = Field(..., description="Rates and factors used to calculate insurance premiums.")
    riders: list[str] = Field(default_factory=list, description="Optional riders available for this insurance product.")
    status: str = Field(..., description="Sales status of the insurance product.", examples=["販売中"])


class Product(ProductBase):
    product_id: str = Field(..., description="Insurance product ID (PRD-NNN).", examples=["PRD-001"])
    created_at: str
    updated_at: str


class ProductList(BaseModel):
    total: int
    items: list[Product]


@app.get("/health", tags=["health"], summary="Check service health")
def health():
    return {"status": "ok", "service": "product"}


@app.get("/products", response_model=ProductList, tags=["products"], summary="List insurance products", description="List property insurance product (products), optionally filtered by insurance category or sales status.")
def list_products(
    category: str | None = Query(None, description="Filter insurance products by product category, such as fire, auto, accident, medical, or pet insurance. Values remain in Japanese."),
    status_: str | None = Query(None, alias="status", description="Filter insurance products by sales status. Values remain in Japanese."),
    skip: int = Query(0, ge=0, description="Number of insurance products to skip for pagination."),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of insurance products to return (1 to 100)."),
):
    filters = {"category": category, "status": status_}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/products/{product_id}", response_model=Product, tags=["products"], summary="Get an insurance product", description="Get one property insurance product by its product ID, including coverage and premium details.")
def get_product(product_id: str = Path(..., description="ID of the insurance product to retrieve (PRD-NNN).")):
    record = store.get(product_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"商品が見つかりません: {product_id}")
    return record


@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED, tags=["products"], summary="Create an insurance product", description="Create a property insurance product with coverage, eligibility, and premium rate details.")
def create_product(payload: ProductBase):
    now = now_jst()
    record = store.create({**payload.model_dump(), "created_at": now, "updated_at": now})
    return record


@app.put("/products/{product_id}", response_model=Product, tags=["products"], summary="Update an insurance product", description="Replace a property insurance product by its product ID.")
def update_product(payload: ProductBase, product_id: str = Path(..., description="ID of the insurance product to update (PRD-NNN).")):
    now = now_jst()
    record = store.update(product_id, {**payload.model_dump(), "updated_at": now})
    if record is None:
        raise HTTPException(status_code=404, detail=f"商品が見つかりません: {product_id}")
    return record


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["products"], summary="Delete an insurance product", description="Delete a property insurance product by its product ID.")
def delete_product(product_id: str = Path(..., description="ID of the insurance product to delete (PRD-NNN).")):
    if not store.delete(product_id):
        raise HTTPException(status_code=404, detail=f"商品が見つかりません: {product_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
