// 백엔드 enum 값 → 한글 라벨. UI 문구는 여기 한 곳에서만 관리한다.
// ⚖️ 직역법 경계(PRODUCT §4): "진단"/"위법입니다"/"패소" 등 금지어를 이 파일에도 쓰지 않는다.
import type { CaseStatus, EvidenceEventType, ExitReason, IntakeRoute, ItemKind, ItemStatus, Rail } from "./api";

export const railLabel: Record<Rail, string> = {
  labor: "노무",
  trade_secret: "영업비밀",
  security: "보안",
};

export const exitReasonLabel: Record<ExitReason, string> = {
  voluntary: "자발적 퇴사",
  recommended_resignation: "권고사직",
  dismissal: "해고",
  contract_expiry: "계약만료",
};

export const intakeRouteLabel: Record<IntakeRoute, string> = {
  groupware: "그룹웨어 연동",
  dismissal: "해고 처리",
  resignation: "사직 처리",
};

export const itemKindLabel: Record<ItemKind, string> = {
  statutory: "법정",
  internal: "내규",
  recommended: "권고",
};

// pending -> "확인 대기"(§4: '진단' 등 판단 단정 어휘 회피, 상태 서술만)
export const itemStatusLabel: Record<ItemStatus, string> = {
  pending: "대기",
  submitted: "검토 대기(상신됨)",
  approved: "확인 완료",
  rejected: "반려",
  not_applicable: "해당없음",
};

export const caseStatusLabel: Record<CaseStatus, string> = {
  in_progress: "진행중",
  review_waiting: "검토 대기",
  completed: "승인 완료",
};

export const caseStatusFilterLabel: Record<"all" | CaseStatus, string> = {
  all: "전체",
  in_progress: "진행중",
  review_waiting: "검토 대기",
  completed: "승인 완료",
};

export const evidenceEventTypeLabel: Record<EvidenceEventType, string> = {
  item_submitted: "항목 상신",
  item_confirmed: "항목 확인완료",
  item_rejected: "항목 반려",
  compare_recorded: "기준 대조 기록",
  recovery_confirmed: "회수 확인",
  case_approved: "케이스 승인",
};
