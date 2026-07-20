"""증적 해시체인 순수함수(data-model §3-4-1) 재현성·체인연결 테스트. DB 불필요."""

from app.domains.evidence.hashing import (
    build_sealed_evidence,
    canonical_json,
    compute_integrity_hash,
)
from app.domains.evidence.models import EvidenceEventType, EvidenceOrigin


def test_canonical_json_when_key_order_differs_produces_same_string() -> None:
    """키정렬·공백정규화로 payload 순서가 달라도 동일 문자열(해시 재현성의 전제)."""
    a = canonical_json({"b": 1, "a": 2})
    b = canonical_json({"a": 2, "b": 1})

    assert a == b
    assert a == '{"a":2,"b":1}'


def test_compute_integrity_hash_is_deterministic_for_same_input() -> None:
    """같은 payload+prev_hash → 항상 같은 해시(재현성)."""
    h1 = compute_integrity_hash({"x": 1}, "prev")
    h2 = compute_integrity_hash({"x": 1}, "prev")

    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_compute_integrity_hash_changes_when_prev_hash_differs() -> None:
    """동일 payload라도 prev_hash가 다르면 해시가 달라진다 — 순서 위변조 탐지 근거."""
    h1 = compute_integrity_hash({"x": 1}, "prev-a")
    h2 = compute_integrity_hash({"x": 1}, "prev-b")

    assert h1 != h2


def test_build_sealed_evidence_when_no_prior_starts_chain_at_seq_one() -> None:
    """직전 Evidence 없음(last=None) → seq=1, prev_hash=None(체인 시작)."""
    evidence = build_sealed_evidence(
        last=None,
        case_id=1,
        event_type=EvidenceEventType.item_submitted,
        origin=EvidenceOrigin.auto,
        actor="한지수",
        action="테스트 상신",
        payload={"a": 1},
    )

    assert evidence.seq == 1
    assert evidence.prev_hash is None
    assert evidence.integrity_hash == compute_integrity_hash({"a": 1}, None)


def test_build_sealed_evidence_when_prior_exists_chains_seq_and_prev_hash() -> None:
    """직전 Evidence가 있으면 seq=직전+1, prev_hash=직전 integrity_hash로 체인 연결."""
    first = build_sealed_evidence(
        last=None,
        case_id=1,
        event_type=EvidenceEventType.item_submitted,
        origin=EvidenceOrigin.auto,
        actor="이수현",
        action="상신",
        payload={"step": 1},
    )

    second = build_sealed_evidence(
        last=first,
        case_id=1,
        event_type=EvidenceEventType.item_confirmed,
        origin=EvidenceOrigin.auto,
        actor="한지수",
        action="확인완료",
        payload={"step": 2},
    )

    assert second.seq == 2
    assert second.prev_hash == first.integrity_hash
    assert second.integrity_hash == compute_integrity_hash(
        {"step": 2}, first.integrity_hash
    )
    assert second.integrity_hash != first.integrity_hash
