"""증적 봉인 동시성(data-model §3-4-1) — 실제 exitguard_test DB로 FOR UPDATE 직렬화를 검증.

Mock으로는 진짜 동시성(두 트랜잭션이 같은 Case 행을 두고 경합)을 재현할 수 없어 여기만
실 DB 통합 테스트로 둔다(unit 테스트가 아니라 integration에 배치한 이유).
"""

import asyncio
from datetime import date

from app.domains.case.models import Case
from app.domains.evidence.models import EvidenceEventType, EvidenceOrigin
from app.domains.evidence.repository import EvidenceRepository
from tests.conftest import TestSessionLocal


async def test_concurrent_append_serializes_seq_via_row_lock(seeded: dict) -> None:
    """같은 case에 동시 append 2건 → FOR UPDATE로 직렬화돼 seq 1·2, 체인이 갈라지지 않는다."""
    async with TestSessionLocal() as setup_session:
        case = Case(
            subject_name="동시성 테스트",
            subject_job="x",
            subject_rank="x",
            exit_reason="voluntary",
            exit_date=date(2026, 1, 1),
            intake_route="groupware",
            created_by=seeded["admin_id"],
        )
        setup_session.add(case)
        await setup_session.commit()
        case_id = case.id

    repo = EvidenceRepository()

    async def _append(tag: str) -> None:
        async with TestSessionLocal() as session:
            await repo.append(
                session,
                case_id=case_id,
                event_type=EvidenceEventType.item_submitted,
                origin=EvidenceOrigin.auto,
                actor="테스트",
                action=f"동시 append {tag}",
                payload={"tag": tag},
            )
            await session.commit()

    await asyncio.gather(_append("a"), _append("b"))

    async with TestSessionLocal() as verify_session:
        entries = await repo.list_by_case(verify_session, case_id)

    assert [e.seq for e in entries] == [1, 2]
    assert entries[0].prev_hash is None
    assert entries[1].prev_hash == entries[0].integrity_hash


async def test_sequential_append_is_monotonic(seeded: dict) -> None:
    """최소 보장 — 순차 append 3건이 seq 1·2·3으로 단조증가(§3-4-1)."""
    async with TestSessionLocal() as setup_session:
        case = Case(
            subject_name="순차 테스트",
            subject_job="x",
            subject_rank="x",
            exit_reason="voluntary",
            exit_date=date(2026, 1, 1),
            intake_route="groupware",
            created_by=seeded["admin_id"],
        )
        setup_session.add(case)
        await setup_session.commit()
        case_id = case.id

    repo = EvidenceRepository()
    for tag in ("1", "2", "3"):
        async with TestSessionLocal() as session:
            await repo.append(
                session,
                case_id=case_id,
                event_type=EvidenceEventType.item_submitted,
                origin=EvidenceOrigin.auto,
                actor="테스트",
                action=f"순차 append {tag}",
                payload={"tag": tag},
            )
            await session.commit()

    async with TestSessionLocal() as verify_session:
        entries = await repo.list_by_case(verify_session, case_id)

    assert [e.seq for e in entries] == [1, 2, 3]
    assert entries[1].prev_hash == entries[0].integrity_hash
    assert entries[2].prev_hash == entries[1].integrity_hash
