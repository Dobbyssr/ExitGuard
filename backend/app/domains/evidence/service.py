"""evidence 도메인 서비스 — 수동 보충 봉인(CM-12)·증적 아카이브 조회(CM-14).

자동 봉인(item_submitted 등 4종)은 case 도메인의 mutation과 한 트랜잭션에서 일어나야
하므로 CaseService가 EvidenceRepository를 직접 주입받아 호출한다(§1 도메인 경계 —
service→service 금지). 여기 EvidenceService는 evidence 자체가 주체인 두 엔드포인트만 다룬다.
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.case.models import CaseStatus
from app.domains.case.repository import CaseRepository
from app.domains.evidence.models import Evidence, EvidenceOrigin
from app.domains.evidence.repository import EvidenceRepository
from app.domains.evidence.schemas import EvidenceCreate
from app.domains.shared.exceptions import NotFoundError


class ArchiveMeta:
    """증적 아카이브 조회 meta — router가 core.Meta로 옮겨 담는다(경량 값 객체)."""

    def __init__(
        self,
        *,
        seal_status: str,
        total_count: int,
        last_sealed_at: datetime | None,
        head_hash: str | None,
    ) -> None:
        self.seal_status = seal_status
        self.total_count = total_count
        self.last_sealed_at = last_sealed_at
        self.head_hash = head_hash


class EvidenceService:
    """증적 수동 봉인·아카이브 조회 비즈니스 로직."""

    def __init__(
        self, evidence_repo: EvidenceRepository, case_repo: CaseRepository
    ) -> None:
        self.evidence_repo = evidence_repo
        self.case_repo = case_repo

    async def manual_seal(
        self, db: AsyncSession, case_id: int, payload: EvidenceCreate
    ) -> Evidence:
        """수동 보충 봉인 — 자동 봉인 트리거로 안 잡히는 처리를 관리자가 직접 기록."""
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            raise NotFoundError(f"케이스를 찾을 수 없습니다(id={case_id})")
        return await self.evidence_repo.append(
            db,
            case_id=case_id,
            event_type=payload.event_type,
            origin=EvidenceOrigin.manual,
            actor=payload.actor,
            action=payload.action,
            payload=payload.payload,
            document_ref=payload.document_ref,
        )

    async def get_archive(
        self, db: AsyncSession, case_id: int
    ) -> tuple[list[Evidence], ArchiveMeta]:
        """증적 아카이브 목록 + 봉인 상태 요약(CM-14)."""
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            raise NotFoundError(f"케이스를 찾을 수 없습니다(id={case_id})")
        entries = await self.evidence_repo.list_by_case(db, case_id)
        # sealed = 케이스가 승인 완료(completed)돼 증적 체인이 확정됨 / accruing = 아직 진행 중 축적.
        seal_status = "sealed" if case.status == CaseStatus.completed else "accruing"
        meta = ArchiveMeta(
            seal_status=seal_status,
            total_count=len(entries),
            last_sealed_at=entries[-1].sealed_at if entries else None,
            head_hash=entries[-1].integrity_hash if entries else None,
        )
        return entries, meta
