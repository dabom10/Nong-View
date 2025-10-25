# Nong-View 개발 문서 인덱스

## 📁 문서 구조 개요

이 디렉토리는 Nong-View AI 영상분석 파이프라인 프로젝트의 개발 문서를 체계적으로 정리한 공간입니다.

```
Dev_md/
├── 01_prompts/              # 초기 요구사항 및 프롬프트
├── 02_rules/                # 개발 규칙 및 가이드라인
├── 03_guides/               # 구현 가이드 및 매뉴얼
├── 04_development_logs/     # 일일 개발 로그
├── 05_reports/              # 진행 보고서 및 기술 문서
├── 06_architecture/         # 시스템 아키텍처 문서
└── README.md               # 이 파일
```

## 📋 문서 카테고리별 안내

### 🎯 01_prompts (초기 요구사항)
프로젝트 시작 시 정의된 요구사항과 초기 프롬프트를 보관합니다.

- `initial_requirements.md` - 프로젝트 초기 요구사항 정의

### 📏 02_rules (개발 규칙)
프로젝트 전체 및 담당자별 개발 규칙을 정의합니다.

- `coding_standards.md` - 전체 프로젝트 코딩 표준
- `development_rules.md` - 일반적인 개발 규칙 및 가이드라인  
- `sonnet_development_rules.md` - **Sonnet 전용 개발 규칙** ⭐

### 📖 03_guides (구현 가이드)
단계별 구현 방법과 기술적 가이드를 제공합니다.

- `api_design_guide.md` - API 설계 가이드
- `pod_development_guide.md` - POD별 개발 가이드
- `sonnet_implementation_guide.md` - **Sonnet 구현 가이드** ⭐

### 📝 04_development_logs (개발 로그)
일일 개발 진행 상황과 기술적 의사결정을 기록합니다.

- `2025-10-26_dev_log.md` - 일반 개발 로그
- `2025-10-26_initial_setup.md` - 초기 설정 로그
- `2025-10-26_opus_implementation.md` - Opus 구현 로그
- `2025-10-26_sonnet_implementation.md` - **Sonnet 구현 로그** ⭐

### 📊 05_reports (보고서)
진행 상황 보고서와 기술 문서를 정리합니다.

- `progress_report_2025-10-26.md` - 전체 진행 보고서
- `sonnet_progress_report_2025-10-26.md` - **Sonnet 진행 보고서** ⭐
- `technical_architecture_report.md` - **기술 아키텍처 보고서** ⭐

### 🏗️ 06_architecture (아키텍처)
시스템 아키텍처와 설계 문서를 보관합니다.

- `system_architecture.md` - 전체 시스템 아키텍처

## 🎯 Sonnet 담당자 핵심 문서

Claude Sonnet이 담당하는 주요 문서들을 우선순위별로 정리했습니다.

### 📌 필수 참조 문서
1. **`02_rules/sonnet_development_rules.md`** - Sonnet 전용 개발 규칙
2. **`03_guides/sonnet_implementation_guide.md`** - 단계별 구현 가이드
3. **`04_development_logs/2025-10-26_sonnet_implementation.md`** - 최신 개발 로그

### 📈 진행 상황 추적
1. **`05_reports/sonnet_progress_report_2025-10-26.md`** - 상세 진행 보고서
2. **`05_reports/technical_architecture_report.md`** - 기술 아키텍처 문서

## 🚀 Sonnet 담당 영역 요약

### 핵심 책임 영역
- **POD2**: 크로핑 (ROI 추출) - ✅ 완료
- **POD6**: GPKG Export - ✅ 완료  
- **API**: FastAPI 서버 구축 - 🔄 진행 중
- **통합**: 전체 파이프라인 오케스트레이션 - 🔄 계획

### 구현 완료 현황 (2025-10-26 기준)
```
POD2 크로핑:        ████████████████████ 100% ✅
POD6 GPKG Export:   ████████████████████ 100% ✅
API 서버 기본 구조:  ████████████████████ 100% ✅
API 엔드포인트:     ░░░░░░░░░░░░░░░░░░░░ 0%  🔄
UI 대시보드:        ░░░░░░░░░░░░░░░░░░░░ 0%  🔄

전체 Sonnet 진행률: ████████████░░░░░░░░ 60%
```

## 📅 다음 단계 계획

### 우선순위 1 (2025-10-27)
- [ ] API 엔드포인트 구현
  - [ ] `endpoints/images.py` - 이미지 관리 API
  - [ ] `endpoints/crops.py` - 크로핑 API
  - [ ] `endpoints/exports.py` - 내보내기 API

### 우선순위 2 (2025-10-28)
- [ ] 데이터베이스 모델 구현
- [ ] 테스트 코드 작성
- [ ] 통합 테스트

### 우선순위 3 (2025-10-29)
- [ ] UI 대시보드 기본 구조
- [ ] 성능 최적화
- [ ] 문서 업데이트

## 🔍 문서 검색 가이드

### 빠른 참조 방법
1. **개발 규칙 확인**: `02_rules/sonnet_development_rules.md`
2. **구현 방법 확인**: `03_guides/sonnet_implementation_guide.md`  
3. **진행 상황 확인**: `05_reports/sonnet_progress_report_2025-10-26.md`
4. **일일 작업 확인**: `04_development_logs/2025-10-26_sonnet_implementation.md`

### 키워드별 문서 위치
- **POD2 크로핑**: `sonnet_implementation_guide.md` § 2
- **POD6 GPKG**: `sonnet_implementation_guide.md` § 3  
- **FastAPI**: `sonnet_implementation_guide.md` § 4
- **개인정보 보호**: `sonnet_development_rules.md` § 8
- **성능 최적화**: `sonnet_development_rules.md` § 7
- **테스트 전략**: `sonnet_development_rules.md` § 6

## 📞 문서 관리 정책

### 업데이트 주기
- **개발 로그**: 매일 업데이트
- **진행 보고서**: 주간 업데이트  
- **규칙/가이드**: 필요시 업데이트
- **아키텍처**: 주요 변경 시 업데이트

### 문서 버전 관리
- 모든 문서는 Git으로 버전 관리
- 주요 변경 시 changelog 기록
- 문서 하단에 작성자/일시 명시

### 품질 관리
- 문서 리뷰 필수
- 정확성 및 최신성 유지
- 독자 관점에서 가독성 검토

## 🏷️ 태그 시스템

문서 내 태그를 활용해 빠른 검색이 가능합니다.

- `⭐` : Sonnet 핵심 문서
- `✅` : 완료된 작업
- `🔄` : 진행 중 작업  
- `📌` : 중요 참조 사항
- `🚨` : 주의 사항
- `💡` : 팁 및 아이디어

## 📞 연락처 및 지원

### 문서 관련 문의
- **작성자**: Claude Sonnet
- **검토자**: 개발팀
- **승인자**: 프로젝트 매니저

### 문서 개선 제안
- 개선 사항은 Git 이슈로 등록
- 긴급한 수정은 직접 수정 후 리뷰 요청
- 새로운 문서 추가는 팀 논의 후 진행

---

## 📈 프로젝트 전체 현황 (간략)

```
Nong-View 프로젝트 진행률: ████████████░░░░░░░░ 60%

✅ 완료 (Opus + Sonnet)
- POD1: 데이터 관리 (Opus)
- POD2: 크로핑 (Sonnet)  
- POD3: 타일링 (Opus)
- POD4: AI 추론 (Opus)
- POD5: 병합 (Opus)
- POD6: GPKG Export (Sonnet)

🔄 진행 중 (Sonnet)
- API 서버 구축
- UI 대시보드 개발

📅 계획 (공통)
- 테스트 코드 작성
- 배포 환경 구축
- 성능 최적화
```

---

*문서 인덱스 최종 업데이트: 2025-10-26 17:45*  
*관리자: Claude Sonnet*  
*다음 업데이트: 2025-10-27*