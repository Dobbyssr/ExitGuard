"""evidence 도메인 리포지토리 — 증적 append 전체 절차(잠금→채번→해시조립→insert)를 캡슐화.

`append()`는 원래 "SQLAlchemy 쿼리만" 규칙보다 한 단계 더 하지만(backend/CLAUDE.md §4),
이는 의도된 예외다 — 도비 브리프의 도메인 경계 지시(CaseService→EvidenceRepository OK /
CaseService→EvidenceService 금지)에 따라 CaseService가 증적을 봉인하려면 이 리포지토리를
직접 호출해야 한다. 해시 알고리즘 자체는 순수함수(hashing.py)로 분리해뒀으니 여기서는
"그 순수함수를 트랜잭션 안에서 올바른 순서로 호출"하는 조립만 한다.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.case.models import Case
from app.domains.evidence.hashing import build_sealed_evidence
from app.domains.evidence.models import Evidence, EvidenceEventType, EvidenceOrigin


class EvidenceRepository:
    """Evidence 테이블 접근 + 봉인 조립. stateless."""

    async def _lock_case(self, db: AsyncSession, case_id: int) -> None:
        """seq 채번 직렬화 — 해당 Case 행을 FOR UPDATE로 잠근다(§3-4-1 동시성 규약).

        Case당 잠금이라 케이스 간 병렬성은 그대로 유지된다(글로벌 락 아님).
        """
        await db.execute(select(Case.id).where(Case.id == case_id).with_for_update())

    async def _get_last(self, db: AsyncSession, case_id: int) -> Evidence | None:
        """해당 case의 최신(seq 최대) Evidence — 체인 헤드."""
        result = await db.execute(
            select(Evidence)
            .where(Evidence.case_id == case_id)
            .order_by(Evidence.seq.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def append(
        self,
        db: AsyncSession,
        *,
        case_id: int,
        event_type: EvidenceEventType,
        origin: EvidenceOrigin,
        actor: str,
        action: str,
        payload: dict,
        document_ref: str | None = None,
    ) -> Evidence:
        """이벤트 1건을 증적으로 봉인해 append한다.

        해당 mutation과 동일 트랜잭션에서 호출돼야 한다(별도 commit 금지 — get_db가
        요청 단위로 커밋을 책임진다). `UNIQUE(case_id, seq)` + 이 잠금이 함께 동시
        append의 seq 단조증가를 보장한다(§3-4-1 — 스네이프 round1 반영).
        """
        await self._lock_case(db, case_id)
        last = await self._get_last(db, case_id)
        evidence = build_sealed_evidence(
            last=last,
            case_id=case_id,
            event_type=event_type,
            origin=origin,
            actor=actor,
            action=action,
            payload=payload,
            document_ref=document_ref,
        )
        db.add(evidence)
        await db.flush()
        return evidence

    async def list_by_case(self, db: AsyncSession, case_id: int) -> list[Evidence]:
        """봉인 이력을 seq 순으로 반환(증적 아카이브 조회)."""
        result = await db.execute(
            select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.seq)
        )
        return list(result.scalars().all())
