"""AI 판례·판정례 대조 엔진 (핵심 해자 자리).

★ 여기가 ExitGuard의 유일한 기술 해자다. L1 법령 / L2 판례·판정례 / L3 정부가이드의
공개 기준과 회사 내부 상태를 "대조"해 미충족 항목·법정기한(D-day)·근거 출처링크를
산출한다. 판단·창작이 아니라 대조·인용·출처링크로만 동작해야 한다(PRODUCT §3-2, §4).

API 계약(docs/spec/api-spec.md, data-model.md)이 아직 없어 지금은 배선만 해둔다.
실제 구현은 계약 확정 후 착수 — 여기서 절대 대충 짜지 않는다(ponytail 예외 대상).
"""


def compare(case: dict) -> dict:
    raise NotImplementedError("AI 판례·판정례 대조 엔진 — API 계약 확정 후 구현")
