"""Gate.compute 결정론적 계산식(data-model §5) 경계값 테스트. DB 불필요 — 순수함수."""

from app.domains.case.models import Item, ItemStatus
from app.domains.case.service import compute_gate
from app.domains.shared.enums import ItemKind, Rail


def _item(rail: Rail, status: ItemStatus, blocking: bool) -> Item:
    return Item(
        case_id=1,
        rail=rail,
        code="X",
        name="테스트 항목",
        kind=ItemKind.statutory,
        status=status,
        blocking=blocking,
    )


def test_compute_gate_when_no_items_returns_zero_completion_and_defensible() -> None:
    """applicable(rail)=0인 경계값 — max(1, 0)로 0으로 나누기를 피하고 defensible은 true."""
    gate = compute_gate([])

    assert gate.overall_completion == 0
    assert gate.rail_completion[Rail.labor] == 0
    assert gate.risk_count == 0
    assert gate.defensible is True


def test_compute_gate_when_all_approved_returns_full_completion() -> None:
    items = [
        _item(Rail.labor, ItemStatus.approved, blocking=True),
        _item(Rail.labor, ItemStatus.approved, blocking=False),
    ]

    gate = compute_gate(items)

    assert gate.rail_completion[Rail.labor] == 100
    assert gate.overall_completion == 100
    assert gate.risk_count == 0
    assert gate.defensible is True


def test_compute_gate_when_blocking_item_unresolved_counts_as_risk() -> None:
    """blocking=true인 미충족 항목만 risk_count에 잡힌다(non-blocking은 무시)."""
    items = [
        _item(Rail.labor, ItemStatus.submitted, blocking=True),
        _item(Rail.labor, ItemStatus.pending, blocking=False),
    ]

    gate = compute_gate(items)

    assert gate.risk_count == 1
    assert gate.defensible is False


def test_compute_gate_when_not_applicable_excluded_from_applicable_denominator() -> (
    None
):
    """§4: not_applicable은 applicable(rail) 분모에서 빠진다 — 2/5=40% 재현(시드 산수)."""
    items = [
        _item(Rail.labor, ItemStatus.approved, blocking=True),
        _item(Rail.labor, ItemStatus.approved, blocking=True),
        _item(Rail.labor, ItemStatus.submitted, blocking=True),
        _item(Rail.labor, ItemStatus.pending, blocking=False),
        _item(Rail.labor, ItemStatus.pending, blocking=False),
        _item(Rail.labor, ItemStatus.not_applicable, blocking=True),
    ]

    gate = compute_gate(items)

    assert gate.rail_completion[Rail.labor] == 40
    assert gate.overall_completion == 40
    assert gate.risk_count == 1  # submitted이면서 blocking인 항목 1건
    assert gate.defensible is False


def test_compute_gate_computes_each_rail_independently() -> None:
    """레일별 completion은 서로 독립 — 한 레일이 0이어도 다른 레일에 영향 없음."""
    items = [
        _item(Rail.labor, ItemStatus.approved, blocking=True),
        _item(Rail.trade_secret, ItemStatus.pending, blocking=True),
    ]

    gate = compute_gate(items)

    assert gate.rail_completion[Rail.labor] == 100
    assert gate.rail_completion[Rail.trade_secret] == 0
    assert gate.rail_completion[Rail.security] == 0
    assert gate.overall_completion == 50
