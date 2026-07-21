"""LB-03 3-상태 롤업 — 코어 `Item.status`를 노무 3-상태(충족/미충족/해당없음)로 파생.

노무 data-model.md §3-1·§3-2. 순수함수(결정론적 count) — 집합(set) 아닌 명시적 개수라
영업비밀 `protection_status` set 오독 버그 전례를 반복하지 않는다(§3-2 주석). 판단이 아니라
Item.status 상태의 기계적 합산이다(경계는 코어 Gate.compute와 동일, §3-1).
"""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domains.case.models import Item, ItemStatus


@dataclass(frozen=True)
class LaborRollup:
    """노무 레일 6항목 롤업 — met+na+unmet == total 불변식(§3-2)."""

    met_count: int
    na_count: int
    unmet_count: int
    total_count: int


def compute_labor_rollup(items: Sequence[Item]) -> LaborRollup:
    """노무 레일 Item 목록(rail=labor로 이미 필터된 것)으로부터 LB-03 요약 카운트를 낸다."""
    met = sum(1 for i in items if i.status == ItemStatus.approved)
    na = sum(1 for i in items if i.status == ItemStatus.not_applicable)
    unmet = sum(
        1
        for i in items
        if i.status in (ItemStatus.pending, ItemStatus.submitted, ItemStatus.rejected)
    )
    return LaborRollup(
        met_count=met, na_count=na, unmet_count=unmet, total_count=len(items)
    )
