# 🌐 Render.com 전체 서비스 설정 가이드

## 📊 Free Tier 제한사항 정리

### **전체 계정 제한**
```yaml
Web Services: 무제한 (단, 각각 월 750시간)
Static Sites: 무제한
PostgreSQL: 최대 2개 ⚠️
Redis: 무제한 (각각 25MB)
Cron Jobs: 무제한
Background Workers: 무제한 (월 750시간)
```

### **리소스 제한**
```yaml
# Web Service
CPU: 0.1 CPU units
RAM: 512MB
Storage: Ephemeral (재시작 시 삭제)
Bandwidth: 100GB/월
Runtime: 750시간/월 (31일 기준 24시간 운영 가능)

# PostgreSQL
Storage: 1GB per database
Connections: 20 동시 연결
Backup: 없음
Regions: Oregon (US West)만

# Redis
Memory: 25MB per instance
Connections: 30 동시 연결
Persistence: 없음 (재시작 시 데이터 삭제)
```

---

## 🗄️ Redis 설정 가이드

### **1단계: Redis 인스턴스 생성**

1. **Dashboard에서 New 선택**
   ```
   New + → Redis 선택
   ```

2. **기본 설정**
   ```yaml
   Name: nong-view-redis
   Plan: Free (25MB)
   Region: Oregon (US West)
   Redis Version: 7.x (최신)
   ```

3. **고급 설정**
   ```yaml
   Max Memory Policy: allkeys-lru (권장)
   # LRU = Least Recently Used (가장 오래된 키 삭제)
   
   # 다른 옵션들:
   # - volatile-lru: TTL 설정된 키만 LRU
   # - allkeys-random: 랜덤 삭제
   # - volatile-random: TTL 키만 랜덤 삭제
   # - volatile-ttl: TTL 짧은 키부터 삭제
   # - noeviction: 삭제 안함 (메모리 부족 시 오류)
   ```

### **2단계: 웹 서비스와 연결**

#### **render.yaml 방식**
```yaml
services:
  - type: web
    name: nong-view-api
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: nong-view-redis
          property: connectionString

  - type: redis
    name: nong-view-redis
    plan: free
    maxmemoryPolicy: allkeys-lru
```

#### **환경변수 수동 설정**
```bash
REDIS_URL=redis://red-xxxxxxxxx:6379
```

### **3단계: Python 연결 테스트**
```python
import redis
import os

# Redis 연결
REDIS_URL = os.getenv('REDIS_URL')
r = redis.from_url(REDIS_URL, decode_responses=True)

try:
    # 연결 테스트
    r.ping()
    print("✅ Redis connection successful!")
    
    # 기본 작업 테스트
    r.set('test_key', 'test_value', ex=60)  # 60초 TTL
    value = r.get('test_key')
    print(f"Test value: {value}")
    
    # 메모리 사용량 확인
    info = r.info('memory')
    used_memory = info['used_memory_human']
    print(f"Used memory: {used_memory}")
    
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
```

---

## 🏗️ 전체 서비스 배포 순서

### **1단계: GitHub 리포지토리 준비**
```bash
# 1. 코드 푸시 확인
git status
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. 배포 파일 확인
ls -la build.sh start.sh render.yaml requirements.txt
```

### **2단계: 데이터베이스 서비스 생성 (우선)**
```yaml
순서: PostgreSQL → Redis → Web Service

이유: 
- 웹 서비스가 DB 연결 정보 필요
- 환경변수 자동 연결을 위해
```

### **3단계: Blueprint 배포 (권장)**

1. **render.yaml 사용**
   ```bash
   # Dashboard → New → Blueprint
   # GitHub 리포지토리 선택
   # render.yaml 자동 감지됨
   ```

2. **서비스 순서 자동 처리**
   ```yaml
   # Render가 자동으로 의존성 순서 처리:
   # 1. PostgreSQL 생성
   # 2. Redis 생성  
   # 3. Web Service 생성 (DB 연결 포함)
   ```

### **4단계: 개별 서비스 생성 (대안)**

#### **PostgreSQL 먼저**
```yaml
Name: nong-view-db
Type: PostgreSQL
Plan: Free
Database: nongview
User: nongview_user
```

#### **Redis 두 번째**
```yaml
Name: nong-view-redis
Type: Redis
Plan: Free
Policy: allkeys-lru
```

#### **Web Service 마지막**
```yaml
Name: nong-view-api
Type: Web Service
Build: chmod +x build.sh && ./build.sh
Start: chmod +x start.sh && ./start.sh
Environment Variables:
  - DATABASE_URL: [PostgreSQL에서 자동]
  - REDIS_URL: [Redis에서 자동]
  - 기타 환경변수들...
```

---

## 🔧 환경변수 관리

### **필수 환경변수 체크리스트**
```bash
# ✅ 자동 설정 (Render가 제공)
PORT=10000                    # Render 자동 할당
RENDER=true                   # Render 환경 표시
DATABASE_URL=postgresql://... # DB 서비스 연결 시
REDIS_URL=redis://...        # Redis 서비스 연결 시

# ✅ 수동 설정 필요
ENVIRONMENT=production
SECRET_KEY=[Generate Value 사용]
PYTHON_VERSION=3.10.12

# ✅ 애플리케이션별 설정
API_V1_STR=/api/v1
PROJECT_NAME=Nong-View API
UPLOAD_PATH=/tmp/uploads
CROP_PATH=/tmp/crops
EXPORT_PATH=/tmp/exports

# ✅ CORS 설정
ALLOWED_HOSTS=*
CORS_ORIGINS=https://your-domain.com,http://localhost:3000

# ✅ 지리정보 설정
GDAL_CONFIG=/usr/bin/gdal-config
GDAL_DATA=/usr/share/gdal
PROJ_LIB=/usr/share/proj
```

### **환경변수 설정 방법**

#### **Web Service Dashboard에서**
```bash
Service → Environment → Add Environment Variable

Key: ENVIRONMENT
Value: production

Key: SECRET_KEY  
Value: [Generate Value 버튼 사용]
```

#### **render.yaml에서**
```yaml
envVars:
  - key: ENVIRONMENT
    value: production
  - key: SECRET_KEY
    generateValue: true
  - key: DATABASE_URL
    fromDatabase:
      name: nong-view-db
      property: connectionString
```

---

## 🚀 배포 확인 및 디버깅

### **배포 상태 확인**
```bash
# 1. 빌드 로그 확인
Dashboard → Service → Logs → Build Logs

# 2. 런타임 로그 확인  
Dashboard → Service → Logs → Deploy Logs

# 3. 서비스 상태 확인
Dashboard → Service → Overview
```

### **일반적인 오류 및 해결**

#### **빌드 실패**
```bash
# 문제: 의존성 설치 실패
해결: requirements.txt 확인, fallback 시스템 활용

# 문제: GDAL 설치 실패
해결: build.sh에서 apt-get 명령 확인

# 문제: 메모리 부족
해결: Free tier → Starter tier 업그레이드
```

#### **실행 시 오류**
```bash
# 문제: 데이터베이스 연결 실패
해결: DATABASE_URL 환경변수 확인, SSL 모드 추가

# 문제: Redis 연결 실패
해결: REDIS_URL 환경변수 확인

# 문제: PORT 바인딩 실패
해결: 0.0.0.0:$PORT 사용 확인
```

### **헬스 체크 엔드포인트**
```bash
# 서비스 상태 확인
curl https://nong-view.onrender.com/health

# 예상 응답
{
  "status": "healthy",
  "timestamp": 1698307200.123,
  "version": "1.0.0",
  "environment": "production"
}
```

---

## 💰 비용 최적화 팁

### **Free Tier 최대 활용**
```bash
# 1. 서비스 일시 정지
- 개발 중이 아닐 때 서비스 정지
- Dashboard → Service → Settings → Suspend

# 2. 리소스 모니터링
- 월별 사용 시간 확인
- 750시간 제한 관리

# 3. 데이터베이스 최적화
- 1GB 제한 내 사용
- 정기적 데이터 정리
```

### **업그레이드 고려사항**
```bash
# Starter 플랜 ($7/월)
- Web Service: 더 많은 메모리/CPU
- PostgreSQL: 더 많은 저장소
- 24/7 운영 가능

# 언제 업그레이드?
- 메모리 부족으로 인한 빌드 실패
- 데이터베이스 용량 부족
- 연중무휴 서비스 필요
```

---

## 🔄 CI/CD 자동화

### **GitHub Actions 연동**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      # Render는 GitHub push 시 자동 배포
      # 별도 action 불필요 (Render가 webhook 처리)
```

### **자동 배포 설정**
```bash
# Render Service Settings
Auto-Deploy: Yes
Branch: main

# 매 GitHub push마다 자동 배포
git push origin main → 자동 빌드 & 배포
```

---

*Last Updated: 2025-10-26*  
*Author: Claude Sonnet*  
*PostgreSQL Free Limit: 2 databases per account*