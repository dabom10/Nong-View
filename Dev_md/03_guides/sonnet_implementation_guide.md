# Sonnet 구현 가이드

## 1. 개발 환경 설정

### 1.1 필수 패키지 설치
```bash
# 기본 패키지
pip install fastapi uvicorn python-multipart
pip install pydantic sqlalchemy alembic
pip install geopandas rasterio shapely fiona

# 지리공간 라이브러리
pip install gdal pyproj cartopy
pip install geopy folium

# 데이터베이스
pip install psycopg2-binary redis

# 백그라운드 작업
pip install celery

# 테스트
pip install pytest pytest-asyncio httpx

# 개발 도구
pip install black isort flake8 mypy
```

### 1.2 IDE 설정
```json
// VS Code settings.json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true
}
```

## 2. POD2 크로핑 구현 가이드

### 2.1 크로핑 엔진 설계
```python
# 핵심 아키텍처
class CroppingEngine:
    """
    설계 원칙:
    1. 단일 책임: ROI 기반 크로핑만 담당
    2. 의존성 역전: 인터페이스에 의존
    3. 확장성: 다양한 크로핑 전략 지원
    """
    
    def __init__(self, strategy: CroppingStrategy = None):
        self.strategy = strategy or DefaultCroppingStrategy()
    
    def crop_image(self, image_path, geometries, config) -> List[CropResult]:
        """메인 크로핑 메서드"""
        return self.strategy.execute(image_path, geometries, config)
```

### 2.2 구현 단계별 가이드

#### 단계 1: 스키마 정의
```python
# schemas.py 구현 순서
1. ROIBounds 클래스 (경계 정보)
2. CropConfig 클래스 (설정 정보)
3. GeometryData 클래스 (지오메트리 데이터)
4. CropRequest/CropResult 클래스 (요청/응답)
5. CropStatus 클래스 (상태 관리)

# 검증 포인트
- 모든 필드에 적절한 validation
- 타입 힌트 완전성
- 문서화 완성도
- 예제 데이터 포함
```

#### 단계 2: 엔진 구현
```python
# engine.py 구현 순서
1. 기본 구조 및 초기화
2. 지오메트리 변환 로직
3. ROI 경계 계산
4. 실제 크로핑 수행
5. 결과 생성 및 검증
6. 에러 처리 및 로깅

# 구현 팁
def _perform_cropping(self, image_path, polygon, output_path, config):
    """
    크로핑 구현 시 고려사항:
    1. 메모리 효율성 (큰 이미지 처리)
    2. 좌표계 일치성 확인
    3. 출력 품질 보장
    4. 에러 복구 전략
    """
    with rasterio.open(image_path) as src:
        # 메타데이터 검증
        if src.crs != polygon_crs:
            polygon = transform_geometry(polygon, polygon_crs, src.crs)
        
        # 메모리 사용량 체크
        estimated_memory = calculate_memory_usage(src, polygon)
        if estimated_memory > MAX_MEMORY:
            return self._crop_in_chunks(src, polygon, output_path, config)
        
        # 일반 크로핑
        return self._crop_normal(src, polygon, output_path, config)
```

#### 단계 3: 테스트 구현
```python
# test_cropping.py 구조
class TestCroppingEngine:
    @pytest.fixture
    def sample_image(self):
        """테스트용 샘플 이미지 생성"""
        return create_test_raster()
    
    @pytest.fixture 
    def sample_geometry(self):
        """테스트용 지오메트리 생성"""
        return create_test_polygon()
    
    def test_basic_cropping(self, sample_image, sample_geometry):
        """기본 크로핑 테스트"""
        # Given
        engine = CroppingEngine()
        config = CropConfig()
        
        # When
        results = engine.crop_image(sample_image, [sample_geometry], config)
        
        # Then
        assert len(results) == 1
        assert results[0].cropped_size[0] > 0
        assert Path(results[0].output_path).exists()
    
    def test_coordinate_transformation(self):
        """좌표계 변환 테스트"""
        pass
    
    def test_error_handling(self):
        """에러 처리 테스트"""
        pass
```

## 3. POD6 GPKG Export 구현 가이드

### 3.1 Export 엔진 설계
```python
# 아키텍처 패턴: Builder + Strategy
class GPKGExporter:
    """
    설계 원칙:
    1. 레이어별 독립 처리
    2. 스트리밍 방식 메모리 관리
    3. 개인정보 보호 필터링
    4. 품질 검증 자동화
    """
    
    def export(self, request: ExportRequest) -> ExportResult:
        builder = GPKGBuilder(request.config)
        
        # 레이어별 처리
        for layer_config in request.config.layers:
            data = self._prepare_layer_data(layer_config, request.analysis_ids)
            builder.add_layer(layer_config.name, data)
        
        # 메타데이터 추가
        builder.add_metadata(self._create_metadata(request))
        
        # 빌드 및 검증
        return builder.build_and_validate()
```

### 3.2 구현 단계별 가이드

#### 단계 1: 데이터 수집 전략
```python
def _collect_analysis_data(self, analysis_ids: List[str]) -> Dict[str, Any]:
    """
    데이터 수집 전략:
    1. 분석 ID별 결과 로드
    2. 지오메트리 데이터 통합
    3. 속성 데이터 정규화
    4. 품질 검증
    """
    
    # 병렬 로딩으로 성능 향상
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(self._load_analysis_result, aid): aid 
            for aid in analysis_ids
        }
        
        results = {}
        for future in as_completed(futures):
            aid = futures[future]
            try:
                results[aid] = future.result()
            except Exception as e:
                logger.error(f"분석 결과 로드 실패: {aid} - {e}")
    
    return self._merge_analysis_results(results)
```

#### 단계 2: 개인정보 보호 구현
```python
def _apply_privacy_protection(self, gdf, privacy_config):
    """
    개인정보 보호 전략:
    1. 필드별 마스킹 규칙
    2. 지오메트리 좌표 일반화
    3. 식별 가능한 패턴 제거
    4. 감사 로그 생성
    """
    
    protected_gdf = gdf.copy()
    
    # 규칙 기반 마스킹
    masking_rules = {
        'owner_name': self._mask_name,
        'phone': self._mask_phone,
        'address': self._mask_address
    }
    
    for field, masking_func in masking_rules.items():
        if field in protected_gdf.columns and privacy_config.should_mask(field):
            protected_gdf[field] = protected_gdf[field].apply(masking_func)
    
    # 지오메트리 일반화 (선택적)
    if privacy_config.anonymize_locations:
        protected_gdf.geometry = protected_gdf.geometry.apply(
            lambda geom: geom.buffer(5).centroid  # 5m 버퍼 후 중심점
        )
    
    return protected_gdf
```

#### 단계 3: 품질 검증 시스템
```python
class GPKGValidator:
    """GPKG 품질 검증기"""
    
    def validate(self, gpkg_path: Path) -> ValidationResult:
        """
        검증 항목:
        1. 파일 구조 검증
        2. 레이어 완성도 검증
        3. 데이터 일관성 검증
        4. 메타데이터 검증
        """
        
        issues = []
        
        # GPKG 파일 구조 검증
        issues.extend(self._validate_structure(gpkg_path))
        
        # 레이어별 검증
        with sqlite3.connect(gpkg_path) as conn:
            layers = self._get_layer_list(conn)
            for layer in layers:
                issues.extend(self._validate_layer(conn, layer))
        
        # 데이터 일관성 검증
        issues.extend(self._validate_consistency(gpkg_path))
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now()
        )
```

## 4. FastAPI 서버 구현 가이드

### 4.1 프로젝트 구조
```
api/
├── main.py                 # 메인 앱
├── config.py              # 설정 관리
├── v1/
│   ├── __init__.py
│   ├── dependencies.py    # 의존성 주입
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── images.py      # 이미지 관리 API
│   │   ├── analyses.py    # 분석 API
│   │   ├── crops.py       # 크로핑 API
│   │   ├── exports.py     # 내보내기 API
│   │   └── statistics.py  # 통계 API
│   └── schemas/
│       ├── __init__.py
│       ├── common.py      # 공통 스키마
│       ├── images.py      # 이미지 스키마
│       └── ...
└── tests/
    ├── conftest.py        # 테스트 설정
    ├── test_images.py
    └── ...
```

### 4.2 API 엔드포인트 구현 패턴

#### 이미지 관리 API
```python
# endpoints/images.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List

router = APIRouter()

@router.post("/", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    metadata: Optional[str] = None,
    current_user = Depends(require_auth),
    upload_path: Path = Depends(get_upload_path)
) -> ImageUploadResponse:
    """
    이미지 업로드 API
    
    구현 포인트:
    1. 파일 타입 검증 (TIFF, GeoTIFF만 허용)
    2. 파일 크기 제한
    3. 메타데이터 추출 및 저장
    4. 썸네일 생성
    5. 중복 검사
    """
    
    # 파일 검증
    if not file.filename.lower().endswith(('.tif', '.tiff')):
        raise HTTPException(400, "TIFF 파일만 지원됩니다")
    
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(400, f"파일 크기가 너무 큽니다: {file.size}")
    
    # 파일 저장
    file_path = upload_path / f"{uuid.uuid4()}_{file.filename}"
    
    async with aopen(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # 메타데이터 추출
    try:
        image_metadata = extract_raster_metadata(file_path)
    except Exception as e:
        file_path.unlink()  # 실패 시 파일 삭제
        raise HTTPException(400, f"메타데이터 추출 실패: {e}")
    
    # 데이터베이스 저장
    # TODO: 구현
    
    return ImageUploadResponse(
        id=str(uuid.uuid4()),
        filename=file.filename,
        file_path=str(file_path),
        metadata=image_metadata,
        uploaded_at=datetime.now()
    )
```

#### 크로핑 API
```python
# endpoints/crops.py
@router.post("/", response_model=CropResponse)
async def create_crop_job(
    request: CropRequest,
    background_tasks: BackgroundTasks,
    cropping_engine = Depends(get_cropping_engine)
) -> CropResponse:
    """
    크로핑 작업 생성 API
    
    비동기 처리 패턴:
    1. 즉시 작업 ID 반환
    2. 백그라운드에서 실제 처리
    3. 상태 조회 API로 진행상황 확인
    """
    
    job_id = str(uuid.uuid4())
    
    # 입력 검증
    validation_errors = cropping_engine.validate_geometries(request.geometries)
    if validation_errors:
        raise HTTPException(400, f"지오메트리 검증 실패: {validation_errors}")
    
    # 백그라운드 작업 시작
    background_tasks.add_task(
        process_cropping_job,
        job_id,
        request,
        cropping_engine
    )
    
    return CropResponse(
        job_id=job_id,
        status="started",
        message="크로핑 작업이 시작되었습니다"
    )

async def process_cropping_job(
    job_id: str,
    request: CropRequest,
    engine: CroppingEngine
):
    """백그라운드 크로핑 작업"""
    try:
        # 상태 업데이트: processing
        await update_job_status(job_id, "processing", 0.0)
        
        # 실제 크로핑 수행
        results = engine.crop_image(
            image_path=Path(request.image_path),
            geometries=request.geometries,
            config=request.config,
            output_dir=get_crop_path()
        )
        
        # 상태 업데이트: completed
        await update_job_status(job_id, "completed", 1.0, results)
        
    except Exception as e:
        logger.error(f"크로핑 작업 실패: {job_id} - {e}")
        await update_job_status(job_id, "failed", 0.0, error=str(e))
```

### 4.3 의존성 주입 설계
```python
# dependencies.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 의존성"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_cropping_engine() -> CroppingEngine:
    """크로핑 엔진 싱글톤"""
    if not hasattr(get_cropping_engine, 'instance'):
        get_cropping_engine.instance = CroppingEngine()
    return get_cropping_engine.instance

async def require_auth(
    authorization: Optional[str] = Header(None)
) -> User:
    """인증 필수 의존성"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, "인증 토큰이 필요합니다")
    
    token = authorization.split(' ')[1]
    user = await verify_token(token)
    
    if not user:
        raise HTTPException(401, "유효하지 않은 토큰입니다")
    
    return user
```

## 5. 통합 테스트 가이드

### 5.1 테스트 환경 설정
```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """인증 헤더"""
    token = create_test_token()
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_tiff():
    """테스트용 TIFF 파일"""
    return create_test_geotiff()
```

### 5.2 API 테스트 패턴
```python
def test_full_pipeline(client, auth_headers, sample_tiff):
    """전체 파이프라인 통합 테스트"""
    
    # 1. 이미지 업로드
    upload_response = client.post(
        "/api/v1/images/",
        files={"file": ("test.tif", sample_tiff, "image/tiff")},
        headers=auth_headers
    )
    assert upload_response.status_code == 201
    image_id = upload_response.json()["id"]
    
    # 2. 크로핑 작업 생성
    crop_request = {
        "image_id": image_id,
        "geometries": [create_test_geometry()],
        "config": {"buffer_distance": 10.0}
    }
    
    crop_response = client.post(
        "/api/v1/crops/",
        json=crop_request,
        headers=auth_headers
    )
    assert crop_response.status_code == 201
    job_id = crop_response.json()["job_id"]
    
    # 3. 작업 완료 대기
    wait_for_job_completion(client, job_id, auth_headers)
    
    # 4. GPKG 내보내기
    export_request = {
        "analysis_ids": [job_id],
        "region_name": "테스트지역"
    }
    
    export_response = client.post(
        "/api/v1/exports/gpkg",
        json=export_request,
        headers=auth_headers
    )
    assert export_response.status_code == 201
```

## 6. 배포 및 운영 가이드

### 6.1 Docker 설정
```dockerfile
# Dockerfile
FROM python:3.10-slim

# GDAL 설치
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV GDAL_VERSION=3.4.1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 환경 설정
```python
# config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Nong-View API"
    VERSION: str = "1.0.0"
    
    # 데이터베이스
    DATABASE_URL: str = "postgresql://user:pass@localhost/nongview"
    
    # 파일 경로
    UPLOAD_PATH: str = "/data/uploads"
    CROP_PATH: str = "/data/crops"
    EXPORT_PATH: str = "/data/exports"
    
    # 보안
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 외부 서비스
    REDIS_URL: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 6.3 모니터링 설정
```python
# 로깅 설정
import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    """구조화된 로깅 설정"""
    
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger

# 메트릭 수집
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response
```

---

*Version: 1.0.0*
*Created: 2025-10-26*
*Author: Claude Sonnet*
*Review Date: 2025-11-02*