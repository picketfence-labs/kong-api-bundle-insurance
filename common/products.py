"""商品(product)マスタの静的定義。

generate_test_data.py・product サービス・simulation サービスで共有する
単一の情報源(single source of truth)。docs/DATA.md の商品テーブルと対応する。
"""

PRODUCTS = [
    {
        "product_id": "PRD-001",
        "product_code": "FIRE-STD",
        "product_name": "火災保険「住まいの安心」",
        "category": "火災保険",
        "description": "戸建て・マンションを対象に、火災・落雷・風災・水災などの損害を補償する住まいの保険です。",
        "coverage_summary": "火災・落雷・風災・水災",
        "min_age": 18,
        "max_age": 99,
        "policy_term": "1〜5年",
        "policy_term_years_options": [1, 2, 3, 5],
        "min_sum_insured": 10_000_000,
        "max_sum_insured": 50_000_000,
        "riders": ["地震保険特約", "個人賠償責任特約"],
        "status": "販売中",
    },
    {
        "product_id": "PRD-002",
        "product_code": "AUTO-STD",
        "product_name": "自動車保険「ドライブセーフ」",
        "category": "自動車保険",
        "description": "対人・対物・車両損害を補償する任意自動車保険です。等級・年齢条件に応じて保険料が変動します。",
        "coverage_summary": "対人・対物・車両保険",
        "min_age": 18,
        "max_age": 99,
        "policy_term": "1年（自動更新）",
        "policy_term_years_options": [1],
        "min_sum_insured": 1_000_000,
        "max_sum_insured": 5_000_000,
        "riders": ["弁護士費用特約", "ロードサービス特約"],
        "status": "販売中",
    },
    {
        "product_id": "PRD-003",
        "product_code": "PA-STD",
        "product_name": "傷害保険「ケガの安心サポート」",
        "category": "傷害保険",
        "description": "急激かつ偶然な事故によるケガの入院・通院・後遺障害・死亡を補償します。",
        "coverage_summary": "入院・通院・後遺障害・死亡保障（急激・偶然な事故）",
        "min_age": 0,
        "max_age": 80,
        "policy_term": "1年（自動更新）",
        "policy_term_years_options": [1],
        "min_sum_insured": 1_000_000,
        "max_sum_insured": 10_000_000,
        "riders": ["個人賠償責任特約"],
        "status": "販売中",
    },
    {
        "product_id": "PRD-004",
        "product_code": "MED-STD",
        "product_name": "医療保険「メディカルサポート」",
        "category": "医療保険",
        "description": "病気・ケガによる入院・手術を保障する医療保険（第三分野）です。",
        "coverage_summary": "入院・手術給付金",
        "min_age": 0,
        "max_age": 75,
        "policy_term": "1年（自動更新）",
        "policy_term_years_options": [1],
        "min_sum_insured": 1_000_000,
        "max_sum_insured": 5_000_000,
        "riders": ["先進医療特約", "がん診断給付特約"],
        "status": "販売中",
    },
    {
        "product_id": "PRD-005",
        "product_code": "PET-STD",
        "product_name": "ペット保険「わんにゃんメディカル」",
        "category": "ペット保険",
        "description": "動物病院での診療費（入院・手術・通院）を補償するペット保険です。",
        "coverage_summary": "動物病院での診療費（入院・手術・通院）",
        "min_age": 0,
        "max_age": 12,
        "policy_term": "1年（自動更新）",
        "policy_term_years_options": [1],
        "min_sum_insured": 300_000,
        "max_sum_insured": 1_000_000,
        "riders": [],
        "status": "販売中",
    },
]

PRODUCTS_BY_ID = {p["product_id"]: p for p in PRODUCTS}

PET_SPECIES = [
    ("犬", ["トイプードル", "柴犬", "チワワ", "ミニチュアダックスフンド", "フレンチブルドッグ"]),
    ("猫", ["雑種（ミックス）", "スコティッシュフォールド", "アメリカンショートヘア", "マンチカン"]),
]

CLAIM_TYPES_BY_CATEGORY = {
    "火災保険": ["火災"],
    "自動車保険": ["自動車事故"],
    "傷害保険": ["入院", "通院", "手術", "死亡（傷害）"],
    "医療保険": ["入院", "通院", "手術"],
    "ペット保険": ["ペット診療"],
}
