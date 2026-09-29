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
    title="Property Insurance Premium Simulation API",
    description=(
        "Calculate a property insurance premium simulation (simulations) for an insurance product "
        "using customer age, sum insured, and smoking status. The API does not store simulations "
        "and uses the same premium calculation as insurance policies."
    ),
    version="1.0.0",
    openapi_tags=[{"name": "simulation", "description": "Calculate property insurance premium simulation (simulations) and quotes."}],
)


class SimulationRequest(BaseModel):
    product_id: str = Field(..., description="Insurance product ID to quote or simulate (PRD-NNN).", examples=["PRD-004"])
    birth_date: str = Field(..., description="Customer's date of birth (YYYY-MM-DD), used to calculate age for the insurance premium.", examples=["1985-04-12"])
    gender: str = Field("回答しない", description="Customer's gender, retained in the simulation request. Values remain in Japanese.", examples=["男性"])
    sum_insured: int = Field(..., description="Requested insurance coverage amount or sum insured in Japanese yen.", examples=[3000000])
    payment_period: str | None = Field(None, description="Requested insurance premium payment period; retained in the simulation request.", examples=["1年（自動更新）"])
    smoker_flag: bool = Field(False, description="Whether the customer smokes; increases premiums for medical and accident insurance.")


class Breakdown(BaseModel):
    base_annual: int = Field(..., description="Base annual insurance premium in Japanese yen.")
    variable_annual: int = Field(..., description="Annual insurance premium component proportional to the sum insured, in Japanese yen.")
    smoker_surcharge: int = Field(..., description="Annual smoker surcharge for medical or accident insurance, in Japanese yen.")
    age_factor: float = Field(..., description="Age factor used in the insurance premium calculation.")


class SimulationResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    age: int = Field(..., description="Customer's age on the simulation date.")
    sum_insured: int
    monthly_premium: int = Field(..., description="Estimated monthly insurance premium in Japanese yen.")
    annual_premium: int = Field(..., description="Estimated annual insurance premium in Japanese yen.")
    breakdown: Breakdown


def _calc_age(birth: date, as_of: date) -> int:
    years = as_of.year - birth.year
    if (as_of.month, as_of.day) < (birth.month, birth.day):
        years -= 1
    return years


@app.get("/health", tags=["health"], summary="Check service health")
def health():
    return {"status": "ok", "service": "simulation"}


@app.post("/simulations", response_model=SimulationResponse, tags=["simulation"], summary="Calculate an insurance premium", description="Create a property insurance premium simulation (simulations) or quote for a product and requested sum insured. Returns monthly and annual premium estimates without storing the result.")
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
