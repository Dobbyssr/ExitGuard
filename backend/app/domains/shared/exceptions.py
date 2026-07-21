"""도메인 공통 예외. service가 던지고 router가 HTTPException으로 변환한다(backend/CLAUDE.md §7)."""

from typing import Any


class DomainError(Exception):
    """모든 도메인 예외의 기반 클래스.

    fields: api-spec §1-3 에러 envelope의 `fields`에 실릴 구조화 상세(예: approve 409의
    risk_count·submitted_count). router가 HTTPException(detail={...})으로 그대로 옮긴다.
    """

    def __init__(self, message: str, fields: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.fields = fields


class NotFoundError(DomainError):
    """요청한 리소스가 존재하지 않음 → 404."""


class DuplicateError(DomainError):
    """유일성 제약을 위반하는 생성 시도 → 409."""


class InvalidStateError(DomainError):
    """상태머신·비즈니스 규칙이 허용하지 않는 전이 시도 → 409/422."""


class CompareFailedError(DomainError):
    """대조 엔진 처리 실패 → 422(api-spec §1-3 `COMPARE_FAILED`).

    LLM 실패·유효신호 0건은 여기 해당하지 않는다(§6-4 Fallback으로 흡수돼 결정론만으로
    성립) — 이 예외는 파이프라인 자체가 처리 불가한 경우(예: MVP 미지원 레일)에만 던진다.
    """
