# Phase 1 계약 교차검증 — TC 요약

세로절단 시나리오(김민준 퇴사 → 3레일 → 방어가능 리포트) 기준 핵심 대조만. 상세 실행결과는 `qa/verification/2026-07-20-phase1-contract-crosscheck.md`.

## Happy Path
- TC-01 뼈대 재정의 검사: 공통/노무/영업비밀/보안 4세트 문서에서 코어 엔티티·enum·상태머신·compare shape 재정의 여부 → PASS(0건)
- TC-02 CP 커버 검사: CM13/LB5/TS3/SEC2 = 23개 전부 목적·플로우·AC·문구경계 존재 → PASS
- TC-03 이음새 절번호 인용 검증: §3-1-1/§3-4-1/§6-4/§10 실재 여부 → PASS

## Edge Case / 정합 대조
- TC-04 직역법 금지어 실사용 스캔(본문 서술, 금지어 목록 제외): "위법입니다"/"부당해고입니다"/"패소합니다"/"진단" → PASS(0건 실사용)
- TC-05 boundary_notice 원문 일치(compare 응답 예시, 글자 단위) → PASS(LB-04·TS-05), Minor(프로즈 인용 3곳 축약/변형)
- TC-06 레일 간 완료율/리스크 수치 정합
  - 노무 rail_completion: 유비쿼터스 §10(65%) vs 노무 data-model §3-3 자체계산(40%) → **FAIL(불일치, Major)**
  - 보안 rail_completion: 보안 api-spec 예시(88%) vs 항목 상태 기반 재계산(67%) → **FAIL(불일치, Major)**
  - 케이스 전체 risk_count: 유비쿼터스 §10(2) vs 노무 레일 자체 blocking-unmet 합(3) → **FAIL(불일치, Major)**
- TC-07 항목코드/레일코드 표기 흔들림(L-/S-/C-, trade_secret vs secret) → PASS
- TC-08 데모 수치(자산 13건·이상반출 4.2GB·게이트 시드) 표집 대조 → PASS(TC-06 제외 나머지 일치)

## 결과
Blocker 0 · Major 3 · Minor 3. 상세는 검증 리포트 참조.
