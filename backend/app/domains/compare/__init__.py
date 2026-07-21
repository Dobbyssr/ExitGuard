"""compare 도메인 — AI 판례·판정례 대조 엔진(핵심 해자).

data-model.md §6(CompareInput/CompareResult shape)·§6-4(LLM/결정론 분리 파이프라인) 구현.
LLM 단계(signal_extractor.py, 지금은 규칙기반 스텁)와 결정론 단계(service.py)를 분리해
"판단·문구생성은 결정론이 소유"(GPT 래퍼 아님)를 코드로 증명한다.
"""
