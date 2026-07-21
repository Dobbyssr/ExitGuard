"""compare 화이트리스트 검증(§6-4 ②) — 환각 차단 로직. DB 불필요, 순수함수."""

from app.domains.compare.schemas import Signal
from app.domains.compare.service import validate_signals


def test_validate_signals_drops_label_outside_whitelist() -> None:
    """폐집합 밖 라벨(예: just_cause — MVP 미허용, §5-1)은 드롭한다."""
    reason_text = "정당한 이유 없이 해고함"
    signals = [Signal(label="just_cause", evidence_span="정당한 이유", confidence=0.9)]

    assert validate_signals(signals, reason_text) == []


def test_validate_signals_drops_when_evidence_span_not_substring() -> None:
    """LLM이 원문에 없는 구간을 evidence_span으로 냈다면(환각) 드롭한다."""
    reason_text = "문자로 통보함"
    signals = [
        Signal(label="written_notice", evidence_span="구두로 통보함", confidence=0.9)
    ]

    assert validate_signals(signals, reason_text) == []


def test_validate_signals_keeps_valid_signal() -> None:
    reason_text = "문자로 통보함"
    signals = [
        Signal(label="written_notice", evidence_span="문자로 통보함", confidence=0.9)
    ]

    assert validate_signals(signals, reason_text) == signals


def test_validate_signals_drops_empty_evidence_span() -> None:
    reason_text = "문자로 통보함"
    signals = [Signal(label="written_notice", evidence_span="", confidence=0.9)]

    assert validate_signals(signals, reason_text) == []
