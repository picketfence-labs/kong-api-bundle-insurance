#!/usr/bin/env python3
"""全サービス共通のテストデータを一括生成する。

product(5) / customer(100) / application(300, うち200件成立) / policy(200) / claim(50)
を1つのスクリプトで生成することで、サービスをまたいだ参照整合性(外部キー・
商品カテゴリと請求種別の整合など)を担保する。生成結果は data/seed/ 配下に
サービス単位のJSONファイルとして書き出す。乱数シードを固定しているため、
再実行しても同じデータが生成される。

使い方: python3 scripts/generate_test_data.py
"""
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from common import jp_data, premium
from common.products import PRODUCTS, PRODUCTS_BY_ID, PET_SPECIES, CLAIM_TYPES_BY_CATEGORY

SEED = 20260731
REFERENCE_DATE = date(2026, 7, 31)  # データ生成の基準日(「現在」とみなす日付)
OUT_DIR = ROOT / "data" / "seed"

JST = "+09:00"


def to_date_str(d: date) -> str:
    return d.isoformat()


def to_datetime_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + JST


def add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        # 2/29 起点のケース
        return d.replace(month=2, day=28, year=d.year + years)


def random_date(rng: random.Random, start: date, end: date) -> date:
    if end <= start:
        return start
    delta_days = (end - start).days
    return start + timedelta(days=rng.randint(0, delta_days))


def calc_age(birth_date: date, as_of: date) -> int:
    years = as_of.year - birth_date.year
    if (as_of.month, as_of.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def romanize_hint(seq: int) -> str:
    return f"customer{seq:03d}"


# ---------------------------------------------------------------------------
# 1. product
# ---------------------------------------------------------------------------

def build_products():
    products = []
    for p in PRODUCTS:
        rate_conf = premium.get_rate_config(p["category"])
        products.append({
            "product_id": p["product_id"],
            "product_code": p["product_code"],
            "product_name": p["product_name"],
            "category": p["category"],
            "description": p["description"],
            "coverage_summary": p["coverage_summary"],
            "min_age": p["min_age"],
            "max_age": p["max_age"],
            "policy_term": p["policy_term"],
            "min_sum_insured": p["min_sum_insured"],
            "max_sum_insured": p["max_sum_insured"],
            "premium_rate_table": {
                "annual_rate_on_sum_insured": rate_conf["rate"],
                "annual_base_premium": rate_conf["base"],
                "note": "年齢係数はsimulationサービスの共通計算ロジックを参照",
            },
            "riders": p["riders"],
            "status": p["status"],
            "created_at": to_datetime_str(datetime(2024, 4, 1, 9, 0, 0)),
            "updated_at": to_datetime_str(datetime(2024, 4, 1, 9, 0, 0)),
        })
    return products


# ---------------------------------------------------------------------------
# 2. customer
# ---------------------------------------------------------------------------

def build_customers(rng: random.Random, count: int = 100):
    customers = []
    genders = rng.choices(
        ["男性", "女性", "その他", "回答しない"], weights=[47, 47, 3, 3], k=count
    )
    for i in range(1, count + 1):
        customer_id = jp_data.format_id("CUS", i)
        gender = genders[i - 1]
        age = rng.randint(20, 85)
        birth_date = REFERENCE_DATE - timedelta(days=age * 365 + rng.randint(0, 364))
        last_kanji, first_kanji, last_kana, first_kana = jp_data.generate_full_name(rng, gender)
        pref_code, postal_code, prefecture, city, address_line = jp_data.generate_postal_address(rng)
        mobile = jp_data.generate_mobile_number(rng)
        has_landline = rng.random() < 0.4
        landline = jp_data.generate_landline_number(rng, pref_code) if has_landline else None
        occupation = rng.choice(jp_data.OCCUPATIONS)
        annual_income = None
        if occupation not in ("専業主婦・主夫", "無職"):
            annual_income = rng.randint(250, 1200) * 10_000
        customer_since = random_date(
            rng, max(birth_date.replace(year=birth_date.year + 20), date(2015, 1, 1)),
            REFERENCE_DATE - timedelta(days=30),
        )
        handle = romanize_hint(i)
        customers.append({
            "customer_id": customer_id,
            "last_name": last_kanji,
            "first_name": first_kanji,
            "last_name_kana": last_kana,
            "first_name_kana": first_kana,
            "birth_date": to_date_str(birth_date),
            "gender": gender,
            "my_number": jp_data.generate_my_number(rng),
            "postal_code": postal_code,
            "prefecture": prefecture,
            "city": city,
            "address_line": address_line,
            "phone_number": landline,
            "mobile_number": mobile,
            "email": f"{handle}@example.com",
            "occupation": occupation,
            "annual_income": annual_income,
            "bank_account": jp_data.generate_bank_account(rng),
            "customer_since": to_date_str(customer_since),
            "created_at": to_datetime_str(datetime.combine(customer_since, datetime.min.time().replace(hour=10))),
            "updated_at": to_datetime_str(datetime.combine(customer_since, datetime.min.time().replace(hour=10))),
        })
    return customers


# ---------------------------------------------------------------------------
# helpers shared by application / policy generation
# ---------------------------------------------------------------------------

REJECTION_REASONS = [
    "告知内容に基づき引受基準を満たさないため",
    "既往症により引受不可と判断されたため",
    "希望保険金額が引受可能上限を超過しているため",
    "必要書類の不備が是正されなかったため",
]

RELATIONSHIPS = ["配偶者", "子", "父", "母", "兄弟姉妹"]


def eligible_customers_for_product(customers, product, as_of: date):
    if product["category"] == "ペット保険":
        return customers
    result = []
    for c in customers:
        birth_date = date.fromisoformat(c["birth_date"])
        age = calc_age(birth_date, as_of)
        if product["min_age"] <= age <= product["max_age"]:
            result.append(c)
    return result or customers


def round_to(value: int, nearest: int) -> int:
    return max(nearest, int(round(value / nearest)) * nearest)


def build_insured_pet(rng: random.Random):
    species, breeds = rng.choice(PET_SPECIES)
    breed = rng.choice(breeds)
    name = rng.choice(["ポチ", "モモ", "ソラ", "ラム", "マロン", "ココ", "レオ", "ハナ"])
    age = rng.randint(0, 11)
    return {"species": species, "breed": breed, "name": name, "age": age}


def build_health_declaration(rng: random.Random):
    has_condition = rng.random() < 0.15
    return {
        "has_pre_existing_condition": has_condition,
        "notes": "既往症あり(告知済み)" if has_condition else "特記事項なし",
    }


def build_beneficiary(rng: random.Random, customer):
    relationship = rng.choice(RELATIONSHIPS)
    return {"name": f"{customer['last_name']} {rng.choice(['太郎', '花子', '次郎', '由紀'])}", "relationship": relationship}


# ---------------------------------------------------------------------------
# 3. application (+ 4. policy)
# ---------------------------------------------------------------------------

def build_applications_and_policies(rng: random.Random, products, customers, app_count: int = 300, approved_count: int = 200):
    applications = []
    approved_flags = [True] * approved_count + [False] * (app_count - approved_count)
    rng.shuffle(approved_flags)

    non_approved_statuses = rng.choices(
        ["審査中", "却下", "取消"], weights=[55, 30, 15], k=app_count - approved_count
    )
    non_approved_iter = iter(non_approved_statuses)

    products_by_category_weight = products  # 単純に一様分布から選ぶ

    for i in range(1, app_count + 1):
        application_id = jp_data.format_id("APP", i)
        product = rng.choice(products_by_category_weight)
        candidates = eligible_customers_for_product(customers, product, REFERENCE_DATE)
        customer = rng.choice(candidates)
        customer_since = date.fromisoformat(customer["customer_since"])
        application_date = random_date(rng, customer_since, REFERENCE_DATE - timedelta(days=1))

        if product["category"] in ("火災保険",):
            sum_insured = round_to(rng.randint(product["min_sum_insured"], product["max_sum_insured"]), 1_000_000)
        elif product["category"] == "ペット保険":
            sum_insured = round_to(rng.randint(product["min_sum_insured"], product["max_sum_insured"]), 100_000)
        else:
            sum_insured = round_to(rng.randint(product["min_sum_insured"], product["max_sum_insured"]), 500_000)

        payment_method = rng.choices(["口座振替", "クレジットカード", "団体扱い"], weights=[55, 35, 10], k=1)[0]

        entry = {
            "application_id": application_id,
            "customer_id": customer["customer_id"],
            "product_id": product["product_id"],
            "application_date": to_date_str(application_date),
            "desired_sum_insured": sum_insured,
            "desired_payment_period": product["policy_term"],
            "payment_method": payment_method,
            "health_declaration": None,
            "beneficiary": None,
            "insured_pet": None,
            "status": None,
            "reviewed_at": None,
            "rejection_reason": None,
            "resulting_policy_id": None,
            "created_at": to_datetime_str(datetime.combine(application_date, datetime.min.time().replace(hour=9, minute=30))),
            "updated_at": None,
            "_product": product,
            "_customer": customer,
            "_application_date": application_date,
        }

        if product["category"] in ("医療保険", "傷害保険"):
            entry["health_declaration"] = build_health_declaration(rng)
        if product["category"] == "傷害保険":
            entry["beneficiary"] = build_beneficiary(rng, customer)
        if product["category"] == "ペット保険":
            entry["insured_pet"] = build_insured_pet(rng)

        is_approved = approved_flags[i - 1]
        review_lag = timedelta(days=rng.randint(2, 10))
        reviewed_at = datetime.combine(application_date, datetime.min.time().replace(hour=14)) + review_lag

        if is_approved:
            entry["status"] = "承認"
            entry["reviewed_at"] = to_datetime_str(reviewed_at)
        else:
            status = next(non_approved_iter)
            entry["status"] = status
            if status != "審査中":
                entry["reviewed_at"] = to_datetime_str(reviewed_at)
                if status == "却下":
                    entry["rejection_reason"] = rng.choice(REJECTION_REASONS)

        entry["updated_at"] = entry["reviewed_at"] or entry["created_at"]
        applications.append(entry)

    # --- policy generation from approved applications ---
    approved_apps = [a for a in applications if a["status"] == "承認"]
    rng.shuffle(approved_apps)

    category_prefix = {
        "火災保険": "FIRE", "自動車保険": "AUTO", "傷害保険": "PA",
        "医療保険": "MED", "ペット保険": "PET",
    }

    policies = []
    for i, app in enumerate(approved_apps, start=1):
        product = app["_product"]
        customer = app["_customer"]
        policy_id = jp_data.format_id("POL", i)
        contract_date = app["_application_date"] + timedelta(days=rng.randint(3, 14))
        if contract_date > REFERENCE_DATE:
            contract_date = REFERENCE_DATE
        effective_date = contract_date

        if product["category"] == "火災保険":
            term_years = rng.choice(PRODUCTS_BY_ID[product["product_id"]]["policy_term_years_options"])
            expiry_date = add_years(contract_date, term_years)
            auto_renew = False
        else:
            term_years = 1
            expiry_date = add_years(contract_date, term_years)
            auto_renew = True

        status_roll = rng.random()
        if auto_renew:
            # 自動更新商品は基準日まで更新され続けているとみなす
            while expiry_date < REFERENCE_DATE:
                expiry_date = add_years(expiry_date, 1)
            if status_roll < 0.06:
                status = "解約"
            elif status_roll < 0.10:
                status = "失効"
            else:
                status = "有効"
        else:
            if expiry_date < REFERENCE_DATE:
                status = "満期"
            elif status_roll < 0.05:
                status = "解約"
            else:
                status = "有効"

        age_at_contract = calc_age(date.fromisoformat(customer["birth_date"]), contract_date)
        premium_payment_cycle = rng.choices(["月払", "年払", "一括"], weights=[55, 30, 15], k=1)[0]
        calc = premium.calculate_premium(product["category"], age_at_contract, app["desired_sum_insured"])
        premium_amount = calc["monthly_premium"] if premium_payment_cycle == "月払" else calc["annual_premium"]

        riders = []
        for r in product["riders"]:
            if rng.random() < 0.3:
                riders.append(r)

        policy_number = f"{contract_date.year}-{category_prefix[product['category']]}-{i:06d}"

        policy = {
            "policy_id": policy_id,
            "policy_number": policy_number,
            "application_id": app["application_id"],
            "customer_id": customer["customer_id"],
            "product_id": product["product_id"],
            "contract_date": to_date_str(contract_date),
            "effective_date": to_date_str(effective_date),
            "expiry_date": to_date_str(expiry_date),
            "sum_insured": app["desired_sum_insured"],
            "premium_amount": premium_amount,
            "premium_payment_cycle": premium_payment_cycle,
            "payment_method": app["payment_method"],
            "status": status,
            "beneficiary": app["beneficiary"],
            "insured_pet": app["insured_pet"],
            "riders": riders,
            "created_at": to_datetime_str(datetime.combine(contract_date, datetime.min.time().replace(hour=10))),
            "updated_at": to_datetime_str(datetime.combine(contract_date, datetime.min.time().replace(hour=10))),
            "_category": product["category"],
            "_effective_date": effective_date,
            "_expiry_date": expiry_date,
        }
        policies.append(policy)
        app["resulting_policy_id"] = policy_id
        app["updated_at"] = policy["created_at"]

    return applications, policies


# ---------------------------------------------------------------------------
# 5. claim
# ---------------------------------------------------------------------------

CLAIM_AMOUNT_RANGE = {
    "火災": (0.1, 0.6),
    "自動車事故": (0.05, 0.5),
    "入院": (0.02, 0.15),
    "通院": (0.005, 0.03),
    "手術": (0.03, 0.2),
    "死亡（傷害）": (0.9, 1.0),
    "ペット診療": (0.02, 0.3),
}

CLAIM_CATEGORY_WEIGHT = {
    "火災保険": 0.6, "自動車保険": 1.6, "傷害保険": 1.2, "医療保険": 1.4, "ペット保険": 1.0,
}


def build_claims(rng: random.Random, policies, count: int = 50):
    weights = [CLAIM_CATEGORY_WEIGHT[p["_category"]] for p in policies]
    chosen = rng.choices(policies, weights=weights, k=count)

    claims = []
    for i, policy in enumerate(chosen, start=1):
        claim_id = jp_data.format_id("CLM", i)
        category = policy["_category"]
        claim_type = rng.choice(CLAIM_TYPES_BY_CATEGORY[category])

        window_end = min(policy["_expiry_date"], REFERENCE_DATE)
        incident_date = random_date(rng, policy["_effective_date"], window_end)
        claim_date = min(incident_date + timedelta(days=rng.randint(0, 30)), REFERENCE_DATE)

        low, high = CLAIM_AMOUNT_RANGE[claim_type]
        claim_amount_requested = round_to(int(policy["sum_insured"] * rng.uniform(low, high)), 1_000)

        status = rng.choices(["審査中", "承認", "支払済", "却下"], weights=[20, 20, 50, 10], k=1)[0]
        claim_amount_paid = None
        processed_at = None
        if status in ("承認", "支払済"):
            claim_amount_paid = int(claim_amount_requested * rng.uniform(0.9, 1.0))
            processed_at = to_datetime_str(
                datetime.combine(claim_date, datetime.min.time().replace(hour=15)) + timedelta(days=rng.randint(3, 20))
            )
        elif status == "却下":
            processed_at = to_datetime_str(
                datetime.combine(claim_date, datetime.min.time().replace(hour=15)) + timedelta(days=rng.randint(3, 20))
            )

        claims.append({
            "claim_id": claim_id,
            "policy_id": policy["policy_id"],
            "customer_id": policy["customer_id"],
            "claim_type": claim_type,
            "incident_date": to_date_str(incident_date),
            "claim_date": to_date_str(claim_date),
            "claim_amount_requested": claim_amount_requested,
            "claim_amount_paid": claim_amount_paid,
            "status": status,
            "description": f"{PRODUCTS_BY_ID[policy['product_id']]['product_name']}にかかる{claim_type}の請求",
            "processed_at": processed_at,
            "created_at": to_datetime_str(datetime.combine(claim_date, datetime.min.time().replace(hour=9))),
            "updated_at": processed_at or to_datetime_str(datetime.combine(claim_date, datetime.min.time().replace(hour=9))),
        })
    return claims


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------

def strip_private_fields(records):
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in records]


def main():
    rng = random.Random(SEED)

    products = build_products()
    customers = build_customers(rng, count=100)
    applications, policies = build_applications_and_policies(rng, products, customers, app_count=300, approved_count=200)
    claims = build_claims(rng, policies, count=50)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    datasets = {
        "product": products,
        "customer": customers,
        "application": strip_private_fields(applications),
        "policy": strip_private_fields(policies),
        "claim": claims,
    }
    for name, records in datasets.items():
        path = OUT_DIR / f"{name}.json"
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {len(records):>4} records -> {path.relative_to(ROOT)}")

    approved = sum(1 for a in applications if a["status"] == "承認")
    print("\n--- summary ---")
    print(f"product: {len(products)}")
    print(f"customer: {len(customers)}")
    print(f"application: {len(applications)} (承認 {approved} / 未成立 {len(applications) - approved})")
    print(f"policy: {len(policies)}")
    print(f"claim: {len(claims)}")


if __name__ == "__main__":
    main()
