# Apps SDK 체크리스트 & 템플릿

이 문서는 `guide.md`의 내용을 실행 가능한 체크리스트로 압축한 문서입니다.

## 1) P0 유스케이스 정의 체크리스트
- [ ] 한 문장으로 성공 정의(사용자가 얻는 결과)
- [ ] Direct prompts 5개 이상
- [ ] Indirect prompts 5개 이상
- [ ] Negative prompts 5개 이상
- [ ] 각 프롬프트의 기대 행동 라벨링(툴 호출/미호출/대안)
- [ ] 최소 기능(MLF) 범위 고정(P0)

## 2) Tool 설계 체크리스트(모델 선택 관점)
- [ ] Tool name이 행동을 정확히 나타냄(동사/구체)
- [ ] Tool name이 앱 내에서 유일
- [ ] Description이 실제 동작과 일치
- [ ] “Use this when…”으로 시작해 사용/비사용 경계를 명시
- [ ] 입력 스키마가 최소이며 task와 직접 연관
- [ ] enum/제약을 적극 활용
- [ ] 재시도에 안전(멱등)하거나, 중복 부작용 가능성을 명시

## 3) Tool annotations(심사/가드레일) 체크리스트
- [ ] `readOnlyHint`가 정확함(외부 상태 변경 없으면 true)
- [ ] 외부 시스템/공개 콘텐츠/계정 밖 작업이면 `openWorldHint`를 적절히 설정
- [ ] 삭제/덮어쓰기 등 파괴적 동작이면 `destructiveHint`를 정확히 설정
- [ ] 누락/오표기는 심사 거절의 주요 원인임을 인지
## 4) Widget/템플릿 체크리스트
- [ ] 위젯 리소스 `mimeType`이 `text/html+skybridge`
- [ ] `_meta["openai/outputTemplate"]`가 올바른 템플릿 URI를 가리킴
- [ ] `window.openai` 런타임 의존 코드가 템플릿 환경에서만 실행됨
- [ ] `structuredContent`는 모델이 읽기 좋은 “최소 JSON”
- [ ] `_meta`는 위젯 전용(큰 데이터/민감 데이터)
- [ ] widget state에 비밀값/토큰을 절대 저장하지 않음

## 5) Widget CSP(도메인 allowlist) 체크리스트
- [ ] `connect_domains`에 API 도메인 최소만 허용
- [ ] `resource_domains`에 이미지/폰트/CDN 최소만 허용
- [ ] `redirect_domains`는 필요한 경우에만
- [ ] `frame_domains`는 가능한 사용하지 않음(심사 리스크 큼)

## 6) Display mode/UX 체크리스트
- [ ] Inline card primary action ≤ 2
- [ ] 카드 내부 탭/드릴다운/깊은 내비게이션 없음
- [ ] 카드 내부 중첩 스크롤 없음
- [ ] ChatGPT 시스템 기능(입력창 등) 복제 없음
- [ ] Fullscreen에서도 시스템 composer가 항상 존재한다는 전제로 UX 설계

## 7) 배포 체크리스트
- [ ] HTTPS 엔드포인트
- [ ] `/mcp`가 안정적이고 빠름
- [ ] streaming/SSE 특성에 맞는 인프라(또는 설정)
- [ ] secret은 repo 밖(Secret manager + env)
- [ ] tool-call ID/latency/error 로그
- [ ] CPU/mem/request 관측(대시보드)
## 8) 메타데이터 튜닝(Optimize metadata) 운영 루틴
- [ ] 골든 프롬프트 세트를 주기적으로 리플레이(릴리즈 후 포함)
- [ ] 변경은 한 번에 하나(원인 추적 가능)
- [ ] precision(오발동 방지) 우선, 그 다음 recall(미발동 개선)
- [ ] “wrong tool” confirmation 스파이크는 metadata drift 신호로 간주

## 9) 심사(App submission) 체크리스트(요약)
- [ ] 목적/독창성 명확(카피캣/사칭/스팸 금지)
- [ ] 오류 처리/안정성/지연(UX) 기준 만족
- [ ] 이름/설명/스크린샷이 실제 기능과 일치
- [ ] 툴 이름/설명/주석이 과장/유도/조작 없이 정확
- [ ] 입력/응답 최소화(불필요 데이터/텔레메트리/ID 반환 금지)
- [ ] Restricted Data 수집 금지(PCI/PHI/정부식별자/인증 비밀값 등)
- [ ] 인증 앱이면 샘플 데이터 있는 데모 계정 제공(가입/불가 2FA 금지)
- [ ] 프라이버시 정책 공개

## 10) 템플릿: 골든 프롬프트 표(복붙용)

| id | type (direct/indirect/negative) | prompt | expected | notes |
|---|---|---|---|---|
| P1 | direct |  | call_tool: <tool> |  |
| P2 | indirect |  | call_tool: <tool> |  |
| P3 | negative |  | do_not_call |  |

## 참고(원문 링크)
- Optimize metadata: https://developers.openai.com/apps-sdk/guides/optimize-metadata
- App submission guidelines: https://developers.openai.com/apps-sdk/app-submission-guidelines
