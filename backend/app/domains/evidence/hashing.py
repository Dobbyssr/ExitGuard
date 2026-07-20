"""증적 해시체인 조립 — 순수함수(DB 접근 없음). data-model.md §3-4-1 freeze 규약 그대로.

CaseService·EvidenceService 양쪽이 이 모듈을 통해 봉인을 조립한다(EvidenceRepository.append
경유). service→service 호출 없이 알고리즘을 한 곳에만 두기 위해 리포지토리도 서비스도 아닌
독립 모듈로 뺐다 — 무결성 핵심 로직이라 DB 유무와 관계없이 단위테스트로 재현성을 검증한다.
"""

import hashlib
import json
from datetime import UTC, datetime

from app.domains.evidence.models import Evidence, EvidenceEventType, EvidenceOrigin


def canonical_json(payload: dict) -> str:
    """해시 재현성을 위한 표준 직렬화 — 키 정렬·공백 정규화(§3-4-1)."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def compute_integrity_hash(payload: dict, prev_hash: str | None) -> str:
    """SHA-256(canonical_json(payload) + prev_hash) — payload와 직전 해시를 함께 해시해
    순서 위변조까지 탐지한다(§3-4-1)."""
    raw = canonical_json(payload) + (prev_hash or "")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_sealed_evidence(
    *,
    last: Evidence | None,
    case_id: int,
    event_type: EvidenceEventType,
    origin: EvidenceOrigin,
    actor: str,
    action: str,
    payload: dict,
    document_ref: str | None = None,
) -> Evidence:
    """직전 Evidence(같은 case, 없으면 None)로부터 다음 Evidence를 조립한다.

    seq=직전+1(없으면 1), prev_hash=직전 integrity_hash(없으면 None=체인 시작).
    호출자가 `last`를 이미 (락 하에) 조회해 넘기므로 이 함수 자체는 DB에 접근하지 않는
    순수함수다 — 해시 재현성·체인 연결을 DB 없이 단위테스트할 수 있다.
    """
    seq = (last.seq + 1) if last is not None else 1
    prev_hash = last.integrity_hash if last is not None else None
    integrity_hash = compute_integrity_hash(payload, prev_hash)
    now = datetime.now(UTC)
    return Evidence(
        case_id=case_id,
        seq=seq,
        occurred_at=now,
        actor=actor,
        action=action,
        event_type=event_type,
        origin=origin,
        document_ref=document_ref,
        payload=payload,
        integrity_hash=integrity_hash,
        prev_hash=prev_hash,
        sealed_at=now,
    )
