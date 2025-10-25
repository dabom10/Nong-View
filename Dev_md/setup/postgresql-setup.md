# 🐘 Render.com PostgreSQL 설정 가이드

## 📋 무료 플랜 제한사항

### **Free Tier 제한**
- **데이터베이스 개수**: 최대 2개
- **저장 용량**: 1GB per database
- **연결 수**: 최대 20개 동시 연결
- **지역**: Oregon (US West)만 가능
- **백업**: 없음 (자동 백업 미지원)
- **유지 기간**: 90일간 비활성 시 삭제

### **권장 사용법**
```
Database 1: 개발/테스트용
Database 2: 프로덕션용 (중요!)
```

---

## 🚀 PostgreSQL 데이터베이스 생성

### **1단계: 새 데이터베이스 생성**

1. **Render.com Dashboard 접속**
   ```
   https://dashboard.render.com/
   ```

2. **New 버튼 클릭**
   - 상단 "New +" 버튼 선택
   - "PostgreSQL" 옵션 선택

3. **기본 정보 입력**
   ```yaml
   Name: nong-view-db
   Database Name: nongview
   User: nongview_user
   Region: Oregon (US West)
   Plan: Free
   ```

4. **고급 설정**
   ```yaml
   PostgreSQL Version: 15 (최신 버전)
   Datadog API Key: (비워둠)
   ```

### **2단계: PostGIS 확장 설치**

데이터베이스 생성 후 **Connect 탭**에서:

1. **External Connection 정보 확인**
   ```bash
   Host: dpg-xxxxxxxxx-a.oregon-postgres.render.com
   Port: 5432
   Database: nongview
   Username: nongview_user
   Password: [자동생성된 패스워드]
   ```

2. **psql로 연결**
   ```bash
   psql postgresql://nongview_user:[password]@dpg-xxxxxxxxx-a.oregon-postgres.render.com/nongview
   ```

3. **PostGIS 확장 설치**
   ```sql
   -- PostGIS 확장 (지리정보 처리용)
   CREATE EXTENSION IF NOT EXISTS postgis;
   
   -- UUID 확장 (고유 ID 생성용)
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   
   -- 설치 확인
   SELECT name, default_version, installed_version 
   FROM pg_available_extensions 
   WHERE name IN ('postgis', 'uuid-ossp');
   ```

### **3단계: 웹 서비스 연결**

#### **render.yaml 방식**
```yaml
services:
  - type: web
    name: nong-view-api
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: nong-view-db
          property: connectionString

  - type: pgsql
    name: nong-view-db
    plan: free
    databaseName: nongview
    user: nongview_user
    postInitSQL: |
      CREATE EXTENSION IF NOT EXISTS postgis;
      CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

#### **수동 연결 방식**
웹 서비스 Environment Variables에 추가:
```bash
DATABASE_URL=postgresql://nongview_user:[password]@dpg-xxxxxxxxx-a.oregon-postgres.render.com/nongview
```

---

## 🔧 데이터베이스 스키마 설정

### **기본 테이블 생성**

```sql
-- 1. 이미지 메타데이터 테이블
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    width INTEGER,
    height INTEGER,
    crs VARCHAR(50),
    bounds GEOMETRY(POLYGON, 4326),
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 분석 작업 테이블
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    image_id UUID REFERENCES images(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    config JSONB,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 크롭 결과 테이블
CREATE TABLE crop_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
    geometry GEOMETRY(POLYGON, 4326),
    crop_path VARCHAR(500),
    area_sqm DECIMAL(12, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. GPKG 내보내기 테이블
CREATE TABLE exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
    export_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### **인덱스 생성**
```sql
-- 성능 최적화를 위한 인덱스
CREATE INDEX idx_images_upload_time ON images(upload_time);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_image_id ON analyses(image_id);
CREATE INDEX idx_crop_results_analysis_id ON crop_results(analysis_id);
CREATE INDEX idx_exports_status ON exports(status);

-- 공간 인덱스 (PostGIS)
CREATE INDEX idx_images_bounds ON images USING GIST(bounds);
CREATE INDEX idx_crop_results_geometry ON crop_results USING GIST(geometry);
```

---

## 🔍 연결 테스트

### **Python 코드로 연결 확인**
```python
import psycopg2
import os

# 연결 문자열
DATABASE_URL = os.getenv('DATABASE_URL')

try:
    # 데이터베이스 연결
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # PostGIS 설치 확인
    cur.execute("SELECT PostGIS_Version();")
    version = cur.fetchone()
    print(f"PostGIS Version: {version[0]}")
    
    # 테이블 목록 확인
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    tables = cur.fetchall()
    print(f"Tables: {[table[0] for table in tables]}")
    
    conn.close()
    print("✅ Database connection successful!")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

### **SQLAlchemy 설정**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv('DATABASE_URL')

# SSL 모드 추가 (Render.com 필수)
if DATABASE_URL and not DATABASE_URL.endswith('?sslmode=require'):
    DATABASE_URL += '?sslmode=require'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 🚨 주의사항 및 팁

### **보안**
```bash
# 1. 연결 문자열 노출 금지
- .env 파일 사용
- 환경변수로만 관리
- GitHub에 업로드 금지

# 2. SSL 연결 필수
DATABASE_URL에 ?sslmode=require 추가
```

### **성능 최적화**
```bash
# 1. 연결 풀링
max_connections = 10 (free tier 제한)

# 2. 쿼리 최적화
- 인덱스 활용
- LIMIT 사용
- 불필요한 SELECT * 피하기

# 3. 트랜잭션 관리
- 짧은 트랜잭션 유지
- 자동 커밋 비활성화
```

### **데이터 백업**
```bash
# 무료 플랜은 자동 백업 없음!
# 정기적 수동 백업 필요

pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### **모니터링**
```bash
# 1. 연결 수 확인
SELECT count(*) FROM pg_stat_activity;

# 2. 데이터베이스 크기 확인
SELECT pg_database_size('nongview') / 1024 / 1024 AS size_mb;

# 3. 테이블별 크기
SELECT 
    tablename,
    pg_size_pretty(pg_relation_size(tablename::regclass)) AS size
FROM pg_tables 
WHERE schemaname = 'public';
```

---

## 🔄 마이그레이션 관리

### **Alembic 설정**
```python
# alembic.ini
[alembic]
sqlalchemy.url = driver://user:pass@localhost/dbname

# env.py
import os
from sqlalchemy import engine_from_config

def get_url():
    return os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://")

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    # ... 나머지 설정
```

### **초기 마이그레이션**
```bash
# 1. 마이그레이션 환경 초기화
alembic init alembic

# 2. 첫 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration"

# 3. 마이그레이션 적용
alembic upgrade head
```

---

## 📊 리소스 모니터링

### **용량 관리**
```sql
-- 데이터베이스 사용량 확인
SELECT 
    pg_database_size('nongview') as size_bytes,
    pg_size_pretty(pg_database_size('nongview')) as size_human,
    (pg_database_size('nongview') * 100.0 / (1024*1024*1024)) as percent_of_1gb;
```

### **성능 모니터링**
```sql
-- 느린 쿼리 확인
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
```

---

*Last Updated: 2025-10-26*  
*Author: Claude Sonnet*  
*Free Tier Limit: 2 databases maximum*