"""LLM seam — 비정형 `reason_text` → 구조화 신호(data-model §6-4 ① LLM 단계).

★ 교체 지점(다음 단계에서 실 Claude API로 갈아끼울 곳): 지금은 **규칙기반(정규식) 스텁**으로
동작한다. 실 LLM으로 바꿔도 시그니처·반환 계약은 그대로다 —
    extract_signals(reason_text: str, allowed_labels: Sequence[str]) -> SignalExtraction
호출부(compare/service.py)는 이 함수 하나만 갈아끼우면 되고 한 글자도 안 바뀐다. 실제 교체 시:
- 프롬프트에 `reason_text` + `allowed_labels`(폐집합)를 주입해 Claude에 신호추출만 시킨다.
- 응답을 그대로 `SignalExtraction`(JSON)으로 파싱해 반환한다.
- LLM은 라벨을 창작할 수 있고 `evidence_span`이 원문에 없을 수도 있다 — 그 검증은 이 함수의
  책임이 아니다(호출자 compare/service.py의 화이트리스트 검증이 전담, §6-4 "LLM은 판단하지
  않는다"). 이 스텁도 검증 없이 raw 신호만 낸다 — 동일 경계를 지킨다.
"""

import re
from collections.abc import Sequence

from app.domains.compare.schemas import Signal, SignalExtraction
from app.domains.labor.models import LaborRequiredElement

# 비서면(구두·약식) 통보 신호 패턴(노무 §5-2). 매칭된 절(節) 전체를 evidence_span으로 낸다
# (원문 문장 경계 '.'까지 포함 — 단일 키워드보다 근거로서 맥락이 있다. 여전히 reason_text의
# 실제 부분문자열이라 화이트리스트 검증(§6-4 evidence_span substring 체크)을 통과한다).
_NON_WRITTEN_NOTICE_PATTERN = re.compile(r"[^.]*(?:구두|문자|전화|카톡|말로)[^.]*")


def extract_signals(
    reason_text: str, allowed_labels: Sequence[str]
) -> SignalExtraction:
    """reason_text에서 허용 라벨(폐집합)만 스캔한다. 유효 신호 없으면 빈 SignalExtraction.

    MVP는 `written_notice`(서면통지 결여) 단일 요소만 스캔한다(노무 §5-1 MVP 범위).
    """
    if (
        not reason_text
        or LaborRequiredElement.written_notice.value not in allowed_labels
    ):
        return SignalExtraction(signals=[], quoted_snippets=[])

    match = _NON_WRITTEN_NOTICE_PATTERN.search(reason_text)
    if match is None:
        return SignalExtraction(signals=[], quoted_snippets=[])

    return SignalExtraction(
        signals=[
            Signal(
                label=LaborRequiredElement.written_notice.value,
                evidence_span=match.group(0).strip(),
                confidence=0.9,
            )
        ],
        quoted_snippets=[],
    )
