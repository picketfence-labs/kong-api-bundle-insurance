"""customer(顧客)サービス。

個人顧客(100件)のマスタを提供するREST API。application/policy/claim
から参照される中心的なマスタ。マイナンバー等の日本フォーマット項目を含む。
"""
from fastapi import FastAPI, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("customer"), id_field="customer_id", id_prefix="CUS", id_width=6)

app = FastAPI(
    title="Property Insurance Customer API",
    description=(
        "Manage property insurance customer (customers) and policyholder records. "
        "Find personal details, Japanese addresses, contact information, My Number, "
        "and bank accounts used by insurance applications, policies, and claims."
        "\n\n**My Number:** The current API returns the full `my_number` value. "
        "A future version may return a raw or masked value based on the caller's role."
    ),
    version="1.0.0",
    openapi_tags=[{"name": "customers", "description": "Read and manage property insurance customer (customers) and policyholders."}],
)


class BankAccount(BaseModel):
    bank_name: str = Field(..., description="Name of the customer's bank.", examples=["みずほ銀行"])
    branch_name: str = Field(..., description="Name of the bank branch.", examples=["渋谷支店"])
    account_type: str = Field(..., description="Type of bank deposit account.", examples=["普通"])
    account_number: str = Field(..., description="Seven-digit bank account number.", examples=["1234567"])


class CustomerBase(BaseModel):
    last_name: str = Field(..., description="Customer's family name.", examples=["山田"])
    first_name: str = Field(..., description="Customer's given name.", examples=["太郎"])
    last_name_kana: str = Field(..., description="Family name in full-width katakana.", examples=["ヤマダ"])
    first_name_kana: str = Field(..., description="Given name in full-width katakana.", examples=["タロウ"])
    birth_date: str = Field(..., description="Customer's date of birth (YYYY-MM-DD).", examples=["1985-04-12"])
    gender: str = Field(..., description="Customer's gender. Values remain in Japanese.", examples=["男性"])
    my_number: str = Field(..., description="Twelve-digit Japanese My Number; sample values are fictitious.", examples=["123456789018"])
    postal_code: str = Field(..., description="Japanese postal code (NNN-NNNN).", examples=["150-0002"])
    prefecture: str = Field(..., description="Japanese prefecture in the customer's address; also filters customers by location.", examples=["東京都"])
    city: str = Field(..., description="City, ward, or municipality in the customer's Japanese address.", examples=["渋谷区"])
    address_line: str = Field(..., description="Street address and building name.", examples=["1-2-3 パークタワー"])
    phone_number: str | None = Field(None, description="Customer's landline phone number.")
    mobile_number: str = Field(..., description="Customer's mobile phone number.", examples=["090-1234-5678"])
    email: str = Field(..., description="Customer's email address.", examples=["taro@example.com"])
    occupation: str | None = Field(None, description="Customer's occupation.")
    annual_income: int | None = Field(None, description="Customer's annual income in Japanese yen.")
    bank_account: BankAccount | None = Field(None, description="Customer's bank account information.")
    customer_since: str = Field(..., description="Date the insurance customer was registered (YYYY-MM-DD).")


class Customer(CustomerBase):
    customer_id: str = Field(..., description="Insurance customer ID (CUS-NNNNNN).", examples=["CUS-000001"])
    created_at: str
    updated_at: str


class CustomerList(BaseModel):
    total: int
    items: list[Customer]


@app.get("/health", tags=["health"], summary="Check service health")
def health():
    return {"status": "ok", "service": "customer"}


@app.get("/customers", response_model=CustomerList, tags=["customers"], summary="List insurance customers", description="List property insurance customer (customers) and policyholders, optionally filtered by Japanese prefecture or gender.")
def list_customers(
    prefecture: str | None = Query(None, description="Filter insurance customers by Japanese prefecture of residence. Values remain in Japanese."),
    gender: str | None = Query(None, description="Filter insurance customers by gender. Values remain in Japanese."),
    skip: int = Query(0, ge=0, description="Number of insurance customers to skip for pagination."),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of insurance customers to return (1 to 100)."),
):
    filters = {"prefecture": prefecture, "gender": gender}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"], summary="Get an insurance customer", description="Get one property insurance customer or policyholder by customer ID.")
def get_customer(customer_id: str = Path(..., description="ID of the insurance customer to retrieve (CUS-NNNNNN).")):
    record = store.get(customer_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"顧客が見つかりません: {customer_id}")
    return record


@app.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED, tags=["customers"], summary="Create an insurance customer", description="Register a property insurance customer with personal, contact, address, and bank account details.")
def create_customer(payload: CustomerBase):
    now = now_jst()
    return store.create({**payload.model_dump(), "created_at": now, "updated_at": now})


@app.put("/customers/{customer_id}", response_model=Customer, tags=["customers"], summary="Update an insurance customer", description="Replace a property insurance customer record by customer ID.")
def update_customer(payload: CustomerBase, customer_id: str = Path(..., description="ID of the insurance customer to update (CUS-NNNNNN).")):
    record = store.update(customer_id, {**payload.model_dump(), "updated_at": now_jst()})
    if record is None:
        raise HTTPException(status_code=404, detail=f"顧客が見つかりません: {customer_id}")
    return record


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["customers"], summary="Delete an insurance customer", description="Delete a property insurance customer record by customer ID.")
def delete_customer(customer_id: str = Path(..., description="ID of the insurance customer to delete (CUS-NNNNNN).")):
    if not store.delete(customer_id):
        raise HTTPException(status_code=404, detail=f"顧客が見つかりません: {customer_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
