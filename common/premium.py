"""保険料算出ロジック(簡易版)。

generate_test_data.py(既存契約の保険料) と simulation サービス(見積り計算) の
両方から共有し、同一商品・同一条件であれば一貫した保険料になるようにする。
実在の保険料率ではなく、デモ用に現実的なオーダー感を再現した簡易モデル。
"""

# カテゴリ別の年間保険料率(保険金額に対する割合)とベース額
_CATEGORY_RATE = {
    "火災保険": {"rate": 0.0007, "base": 0},
    "自動車保険": {"rate": 0.0, "base": 55_000},
    "傷害保険": {"rate": 0.0006, "base": 2_000},
    "医療保険": {"rate": 0.012, "base": 3_000},
    "ペット保険": {"rate": 0.07, "base": 5_000},
}


def _age_factor(category: str, age: int) -> float:
    if category == "自動車保険":
        if age < 26:
            return 1.6
        if age < 35:
            return 1.15
        if age < 60:
            return 1.0
        return 1.1
    if category in ("傷害保険", "医療保険"):
        if age < 20:
            return 0.8
        if age < 40:
            return 1.0
        if age < 60:
            return 1.3
        return 1.8
    if category == "ペット保険":
        if age < 3:
            return 0.9
        if age < 7:
            return 1.0
        return 1.6
    return 1.0


def get_rate_config(category: str) -> dict:
    conf = _CATEGORY_RATE.get(category, {"rate": 0.001, "base": 3_000})
    return dict(conf)


def calculate_premium(category: str, age: int, sum_insured: int, smoker: bool = False) -> dict:
    """年齢・保険金額から月額/年額保険料を算出する。

    Returns: {"monthly_premium": int, "annual_premium": int, "breakdown": {...}}
    """
    conf = _CATEGORY_RATE.get(category, {"rate": 0.001, "base": 3_000})
    factor = _age_factor(category, age)
    base_annual = conf["base"] * factor
    variable_annual = sum_insured * conf["rate"] * factor
    smoker_surcharge = 0.0
    if smoker and category in ("傷害保険", "医療保険"):
        smoker_surcharge = (base_annual + variable_annual) * 0.15

    annual_premium = int(round(base_annual + variable_annual + smoker_surcharge, -1))
    monthly_premium = int(round(annual_premium / 12, -1))

    return {
        "monthly_premium": monthly_premium,
        "annual_premium": annual_premium,
        "breakdown": {
            "base_annual": int(round(base_annual, -1)),
            "variable_annual": int(round(variable_annual, -1)),
            "smoker_surcharge": int(round(smoker_surcharge, -1)),
            "age_factor": factor,
        },
    }
