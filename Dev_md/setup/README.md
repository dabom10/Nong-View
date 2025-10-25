# 🛠️ Nong-View 설정 가이드 모음

이 폴더는 Nong-View 프로젝트의 모든 설정 및 배포 관련 가이드를 포함합니다.

## 📚 가이드 목록

### 🐘 [PostgreSQL 설정 가이드](./postgresql-setup.md)
- **무료 플랜 제한**: 최대 2개 데이터베이스
- **PostGIS 확장 설치**: 지리정보 처리를 위한 필수 확장
- **스키마 설계**: 이미지, 분석, 크롭, 내보내기 테이블
- **성능 최적화**: 인덱스, 연결 관리, 쿼리 최적화
- **백업 전략**: 무료 플랜 백업 부재에 대한 대응

### 🌐 [Render.com 전체 서비스 설정](./render-services-setup.md)
- **Free Tier 제한사항**: 모든 서비스별 상세 제한
- **Redis 설정**: 캐시 서버 구성 및 메모리 정책
- **배포 순서**: 의존성을 고려한 올바른 서비스 생성 순서
- **환경변수 관리**: 필수 환경변수 체크리스트
- **CI/CD 자동화**: GitHub 연동 자동 배포

---

## 🚀 빠른 시작 가이드

### 1️⃣ 첫 배포 (권장 순서)
```bash
1. GitHub에 코드 푸시
2. PostgreSQL 데이터베이스 생성 (1/2)
3. Redis 인스턴스 생성
4. Web Service 생성 (render.yaml 사용)
5. 환경변수 설정
6. PostGIS 확장 설치
```

### 2️⃣ Blueprint 방식 (자동화)
```bash
1. GitHub 리포지토리 준비
2. Render Dashboard → New → Blueprint
3. render.yaml 자동 감지
4. 모든 서비스 자동 생성
5. PostGIS 수동 설치만 필요
```

---

## ⚠️ 중요 제한사항

### 🔢 **Free Tier 제한**
| 서비스 | 개수 제한 | 용량/시간 제한 |
|--------|-----------|----------------|
| Web Service | 무제한 | 750시간/월 |
| PostgreSQL | **2개만** | 1GB/DB |
| Redis | 무제한 | 25MB/인스턴스 |
| Static Sites | 무제한 | 100GB 대역폭/월 |

### 💡 **최적화 팁**
```bash
# PostgreSQL 2개 제한 관리
Database 1: 개발/테스트용
Database 2: 프로덕션용

# 메모리 최적화
- requirements 최소화
- 이미지 크기 제한
- 캐시 적극 활용

# 비용 절약
- 개발 중이 아닐 때 서비스 일시 정지
- 불필요한 로그 출력 최소화
- 정기적 데이터베이스 정리
```

---

## 🔍 트러블슈팅

### 🚨 **자주 발생하는 문제들**

#### PostgreSQL 관련
```bash
❌ 문제: "Too many databases" 오류
✅ 해결: 기존 DB 삭제 또는 다른 계정 사용

❌ 문제: PostGIS 확장 설치 실패
✅ 해결: 수동으로 psql 연결하여 CREATE EXTENSION

❌ 문제: SSL 연결 오류
✅ 해결: DATABASE_URL에 ?sslmode=require 추가
```

#### 배포 관련
```bash
❌ 문제: 빌드 시 메모리 부족
✅ 해결: Free → Starter 플랜 업그레이드

❌ 문제: pydantic-core Rust 컴파일 오류
✅ 해결: fallback 시스템이 자동 처리

❌ 문제: 환경변수 누락
✅ 해결: 체크리스트 확인 및 수동 설정
```

---

## 📞 지원 및 참고자료

### 🔗 **공식 문서**
- [Render.com 문서](https://render.com/docs)
- [PostgreSQL on Render](https://render.com/docs/databases)
- [Redis on Render](https://render.com/docs/redis)

### 🛠️ **도구 및 유틸리티**
- [PostGIS 문서](https://postgis.net/documentation/)
- [psql 명령어 참조](https://www.postgresql.org/docs/current/app-psql.html)
- [Redis CLI 사용법](https://redis.io/topics/rediscli)

### 💬 **커뮤니티**
- [Render Community Forum](https://community.render.com/)
- [PostgreSQL 커뮤니티](https://www.postgresql.org/community/)

---

## 📝 업데이트 노트

| 날짜 | 변경사항 | 작성자 |
|------|----------|--------|
| 2025-10-26 | 초기 설정 가이드 작성 | Claude Sonnet |
| 2025-10-26 | PostgreSQL 2개 제한 발견 및 문서화 | Claude Sonnet |
| 2025-10-26 | Redis 설정 및 전체 서비스 가이드 추가 | Claude Sonnet |

---

*이 가이드는 Render.com Free Tier 기준으로 작성되었습니다.*  
*유료 플랜 사용 시 일부 제한사항이 달라질 수 있습니다.*

---

**📁 설정 파일 위치:**
- `render.yaml` - Blueprint 설정
- `build.sh` - 빌드 스크립트  
- `start.sh` - 시작 스크립트
- `requirements*.txt` - Python 의존성
- `api/main_*.py` - API 서버 버전들