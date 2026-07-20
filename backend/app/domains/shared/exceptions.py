"""도메인 공통 예외. service가 던지고 router가 HTTPException으로 변환한다(backend/CLAUDE.md §7).

지금은 모델 단계라 실제로 raise하는 곳은 없다 — 다음 단계(service) 구현이 이 클래스들을 쓴다.
"""


class DomainError(Exception):
    """모든 도메인 예외의 기반 클래스."""


class NotFoundError(DomainError):
    """요청한 리소스가 존재하지 않음 → 404."""


class DuplicateError(DomainError):
    """유일성 제약을 위반하는 생성 시도 → 409."""


class InvalidStateError(DomainError):
    """상태머신·비즈니스 규칙이 허용하지 않는 전이 시도 → 409/422."""
