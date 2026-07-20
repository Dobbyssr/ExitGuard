"""도메인 경계를 넘나드는 공용 열거형.

Rail·ItemKind는 case 도메인(Item)과 catalog 도메인(Standard·RailTemplate·TemplateItem)
양쪽에서 쓰인다. 각 도메인이 따로 선언하면 같은 개념이 서로 다른 파이썬 타입이 되어
비교·직렬화가 어긋난다 — 공용 어휘라 여기 1곳에 둔다(docs/spec/data-model.md §2).
"""

import enum


class Rail(str, enum.Enum):
    """3레일 구분 — 노무/영업비밀/보안(§2-1)."""

    labor = "labor"
    trade_secret = "trade_secret"
    security = "security"


class ItemKind(str, enum.Enum):
    """검사항목 구분(필수성) — 법정/내규/권고(§2-4)."""

    statutory = "statutory"
    internal = "internal"
    recommended = "recommended"
