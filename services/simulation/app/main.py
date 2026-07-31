"""simulation(保険料試算)サービス。

商品・顧客属性から保険料を試算するステートレスAPI(永続化なし)。
product サービスの商品カテゴリと、共通の保険料算出ロジック(common.premium)を
用いて、他サービスの契約保険料と一貫した試算結果を返す。
"""
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from common import premium
from common.products import PRODUCTS_BY_ID

app = FastAPI(
    title="保険料試算サービス (Simulation Service)",
    description=(
        "保険料を試算するステートレスAPI。データは永続化せず、入力に応じて都度計算します。"
        "契約(policy)サービスの保険料と同一の算出ロジックを用います。"
    ),
    version="1.0.0",
    openapi_tags=[{"name": "simulation", "description": "保険料の試算"}],
)


class SimulationRequest(BaseModel):
    product_id: str = Field(..., description="試算対象商品(商品ID)", examples=["PRD-004"])
    birth_date: str = Field(..., description="生年月日(YYYY-MM-DD)。年齢計算に使用", examples=["1985-04-12"])
    gender: str = Field("回答しない", description="性別", examples=["男性"])
    sum_insured: int = Field(..., description="希望保険金額(円)", examples=[3000000])
    payment_period: str | None = Field(None, description="払込期間", examples=["1年（自動更新）"])
    smoker_flag: bool = Field(False, description="喫煙の有無(医療・傷害保険で保険料に影響)")


class Breakdown(BaseModel):
    base_annual: int = Field(..., description="年間ベース保険料(円)")
    variable_annual: int = Field(..., description="保険金額比例部分の年間保険料(円)")
    smoker_surcharge: int = Field(..., description="喫煙割増(円)")
    age_factor: float = Field(..., description="年齢係数")


class SimulationResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    age: int = Field(..., description="試算基準日時点の年齢")
    sum_insured: int
    monthly_premium: int = Field(..., description="月額保険料(円)")
    annual_premium: int = Field(..., description="年額保険料(円)")
    breakdown: Breakdown


def _calc_age(birth: date, as_of: date) -> int:
    years = as_of.year - birth.year
    if (as_of.month, as_of.day) < (birth.month, birth.day):
        years -= 1
    return years


@app.get("/health", tags=["health"], summary="ヘルスチェック")
def health():
    return {"status": "ok", "service": "simulation"}


@app.post("/simulations", response_model=SimulationResponse, tags=["simulation"], summary="保険料の試算")
def simulate(req: SimulationRequest):
    product = PRODUCTS_BY_ID.get(req.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"商品が見つかりません: {req.product_id}")

    try:
        birth = date.fromisoformat(req.birth_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="birth_dateはYYYY-MM-DD形式で指定してください")

    age = _calc_age(birth, date.today())

    if not (product["min_age"] <= age <= product["max_age"]):
        raise HTTPException(
            status_code=422,
            detail=f"この商品の加入可能年齢は{product['min_age']}〜{product['max_age']}歳です(試算年齢: {age}歳)",
        )
    if not (product["min_sum_insured"] <= req.sum_insured <= product["max_sum_insured"]):
        raise HTTPException(
            status_code=422,
            detail=(
                f"保険金額は{product['min_sum_insured']:,}〜{product['max_sum_insured']:,}円の範囲で"
                f"指定してください(入力値: {req.sum_insured:,}円)"
            ),
        )

    result = premium.calculate_premium(product["category"], age, req.sum_insured, smoker=req.smoker_flag)
    return {
        "product_id": product["product_id"],
        "product_name": product["product_name"],
        "category": product["category"],
        "age": age,
        "sum_insured": req.sum_insured,
        "monthly_premium": result["monthly_premium"],
        "annual_premium": result["annual_premium"],
        "breakdown": result["breakdown"],
    }
