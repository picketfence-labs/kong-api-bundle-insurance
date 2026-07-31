"""customer(顧客)サービス。

個人顧客(100件)のマスタを提供するREST API。application/policy/claim
から参照される中心的なマスタ。マイナンバー等の日本フォーマット項目を含む。
"""
from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from common.store import JsonStore, now_jst, resolve_seed_path

store = JsonStore(resolve_seed_path("customer"), id_field="customer_id", id_prefix="CUS", id_width=6)

app = FastAPI(
    title="顧客サービス (Customer Service)",
    description=(
        "個人顧客マスタを提供するAPI。氏名・住所・連絡先・マイナンバー・口座情報を管理します。"
        "\n\n**マイナンバーの扱い:** 現バージョンでは`my_number`をフル桁でそのまま返却します。"
        "将来的に利用者の権限(ロール)に応じてraw/maskedを切り替える予定です。"
    ),
    version="1.0.0",
    openapi_tags=[{"name": "customers", "description": "顧客マスタの参照・管理"}],
)


class BankAccount(BaseModel):
    bank_name: str = Field(..., description="銀行名", examples=["みずほ銀行"])
    branch_name: str = Field(..., description="支店名", examples=["渋谷支店"])
    account_type: str = Field(..., description="預金種別", examples=["普通"])
    account_number: str = Field(..., description="口座番号(7桁)", examples=["1234567"])


class CustomerBase(BaseModel):
    last_name: str = Field(..., description="姓", examples=["山田"])
    first_name: str = Field(..., description="名", examples=["太郎"])
    last_name_kana: str = Field(..., description="姓(全角カナ)", examples=["ヤマダ"])
    first_name_kana: str = Field(..., description="名(全角カナ)", examples=["タロウ"])
    birth_date: str = Field(..., description="生年月日(YYYY-MM-DD)", examples=["1985-04-12"])
    gender: str = Field(..., description="性別", examples=["男性"])
    my_number: str = Field(..., description="マイナンバー(12桁・ダミー)", examples=["123456789018"])
    postal_code: str = Field(..., description="郵便番号(NNN-NNNN)", examples=["150-0002"])
    prefecture: str = Field(..., description="都道府県", examples=["東京都"])
    city: str = Field(..., description="市区町村", examples=["渋谷区"])
    address_line: str = Field(..., description="番地・建物名", examples=["1-2-3 パークタワー"])
    phone_number: str | None = Field(None, description="固定電話番号")
    mobile_number: str = Field(..., description="携帯電話番号", examples=["090-1234-5678"])
    email: str = Field(..., description="メールアドレス", examples=["taro@example.com"])
    occupation: str | None = Field(None, description="職業")
    annual_income: int | None = Field(None, description="年収(円)")
    bank_account: BankAccount | None = Field(None, description="口座情報")
    customer_since: str = Field(..., description="顧客登録日(YYYY-MM-DD)")


class Customer(CustomerBase):
    customer_id: str = Field(..., description="顧客ID(CUS-NNNNNN)", examples=["CUS-000001"])
    created_at: str
    updated_at: str


class CustomerList(BaseModel):
    total: int
    items: list[Customer]


@app.get("/health", tags=["health"], summary="ヘルスチェック")
def health():
    return {"status": "ok", "service": "customer"}


@app.get("/customers", response_model=CustomerList, tags=["customers"], summary="顧客一覧の取得")
def list_customers(
    prefecture: str | None = Query(None, description="都道府県で絞り込み"),
    gender: str | None = Query(None, description="性別で絞り込み"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    filters = {"prefecture": prefecture, "gender": gender}
    total, items = store.list(filters=filters, skip=skip, limit=limit)
    return {"total": total, "items": items}


@app.get("/customers/{customer_id}", response_model=Customer, tags=["customers"], summary="顧客の取得")
def get_customer(customer_id: str):
    record = store.get(customer_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"顧客が見つかりません: {customer_id}")
    return record


@app.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED, tags=["customers"], summary="顧客の新規登録")
def create_customer(payload: CustomerBase):
    now = now_jst()
    return store.create({**payload.model_dump(), "created_at": now, "updated_at": now})


@app.put("/customers/{customer_id}", response_model=Customer, tags=["customers"], summary="顧客の更新")
def update_customer(customer_id: str, payload: CustomerBase):
    record = store.update(customer_id, {**payload.model_dump(), "updated_at": now_jst()})
    if record is None:
        raise HTTPException(status_code=404, detail=f"顧客が見つかりません: {customer_id}")
    return record


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["customers"], summary="顧客の削除")
def delete_customer(customer_id: str):
    if not store.delete(customer_id):
        raise HTTPException(status_code=404, detail=f"顧客が見つかりません: {customer_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
