"""LLM seam(규칙기반 스텁) 신호추출 테스트 — data-model §6-4 ①. DB 불필요, 순수함수."""

import pytest

from app.domains.compare.signal_extractor import extract_signals
from app.domains.labor.models import LaborRequiredElement

_ALLOWED = (LaborRequiredElement.written_notice.value,)


def test_extract_signals_when_verbal_notice_pattern_present_returns_written_notice_signal() -> (
    None
):
    reason_text = "권고사직 처리하며, 통화가 어려워 문자로 통보함."

    extraction = extract_signals(reason_text, _ALLOWED)

    assert len(extraction.signals) == 1
    signal = extraction.signals[0]
    assert signal.label == "written_notice"
    assert (
        signal.evidence_span in reason_text
    )  # 원문 부분문자열(환각 차단 전제, §6-4 검증)
    assert "문자" in signal.evidence_span


def test_extract_signals_when_no_pattern_returns_empty() -> None:
    extraction = extract_signals("정상적으로 서면 통지를 완료했습니다.", _ALLOWED)

    assert extraction.signals == []
    assert extraction.quoted_snippets == []


def test_extract_signals_when_reason_text_empty_returns_empty() -> None:
    assert extract_signals("", _ALLOWED).signals == []


def test_extract_signals_when_label_not_allowed_skips_scan() -> None:
    """허용 라벨 목록이 비어 있으면(다른 레일 호출 등) 스캔 자체를 하지 않는다."""
    extraction = extract_signals("전화로 통보함", allowed_labels=())

    assert extraction.signals == []


@pytest.mark.parametrize("keyword", ["구두", "문자", "전화", "카톡", "말로"])
def test_extract_signals_detects_each_non_written_notice_pattern(keyword: str) -> None:
    reason_text = f"해고 사유를 {keyword}로 전달함."

    extraction = extract_signals(reason_text, _ALLOWED)

    assert len(extraction.signals) == 1
    assert keyword in extraction.signals[0].evidence_span
