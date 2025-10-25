# Sonnet 전용 개발 규칙 및 가이드라인

## 1. Sonnet 담당 영역

### 1.1 핵심 책임
- **POD2: 크로핑 (ROI 추출)** - ROI 경계 기반 이미지 크로핑
- **POD6: GPKG Export** - 행정보고용 GeoPackage 생성
- **API 개발** - FastAPI 기반 REST API 서버 구축
- **통합 관리** - 전체 파이프라인 통합 및 조율

### 1.2 개발 우선순위
```
Priority 1: POD2 크로핑 + POD6 GPKG Export (핵심 기능)
Priority 2: FastAPI 서버 + 핵심 API 엔드포인트
Priority 3: UI/UX 개발 (관리자 대시보드)
Priority 4: 배포 및 인프라 (Docker, CI/CD)
```

## 2. Sonnet 특화 코딩 규칙

### 2.1 모듈 구조 규칙
```python
# Sonnet 담당 모듈 구조
src/
├── pod2_cropping/
│   ├── __init__.py          # 모듈 초기화
│   ├── engine.py            # 크로핑 엔진 (핵심 로직)
│   ├── schemas.py           # Pydantic 스키마
│   └── tests/               # 단위 테스트
├── pod6_gpkg_export/
│   ├── __init__.py
│   ├── exporter.py          # GPKG 내보내기 엔진
│   ├── report_generator.py  # 리포트 생성기
│   ├── schemas.py
│   └── tests/
└── api/
    ├── main.py              # FastAPI 메인 앱
    ├── v1/
    │   ├── endpoints/       # API 엔드포인트
    │   ├── schemas/         # API 스키마
    │   └── dependencies.py  # 의존성 주입
    └── tests/
```

### 2.2 스키마 설계 원칙
```python
# 1. Pydantic 모델 필수 사용
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SonnetSchema(BaseModel):
    """
    모든 스키마는 다음 요소를 포함:
    1. 명확한 docstring
    2. Field validation
    3. 타입 힌트
    4. Config 클래스 (example 포함)
    """
    id: str = Field(..., description="고유 식별자")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {"example": {"id": "test", "created_at": "2025-10-26T10:30:00Z"}}

# 2. 요청/응답 스키마 분리
class CreateRequest(BaseModel):
    """생성 요청 스키마"""
    pass

class CreateResponse(BaseModel):
    """생성 응답 스키마"""
    pass
```

### 2.3 API 설계 원칙
```python
# FastAPI 라우터 구조
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

router = APIRouter()

@router.post("/", response_model=CreateResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    request: CreateRequest,
    current_user = Depends(require_auth),
    service = Depends(get_service)
) -> CreateResponse:
    """
    리소스 생성 API
    
    - 명확한 docstring
    - 적절한 status code
    - 타입 힌트
    - 의존성 주입 활용
    - 예외 처리
    """
    try:
        result = service.create(request)
        return CreateResponse(**result.dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

## 3. 지리공간 데이터 처리 규칙

### 3.1 좌표계 표준
```python
# 기본 좌표계 규칙
DEFAULT_CRS = "EPSG:5186"  # Korea 2000 / Central Belt 2010
WGS84_CRS = "EPSG:4326"    # WGS84 (위경도)

# 좌표계 변환 시 필수 확인사항
def transform_coordinates(gdf: gpd.GeoDataFrame, target_crs: str):
    """
    1. 소스 CRS 확인
    2. 변환 필요성 검사
    3. 정확도 검증
    4. 에러 처리
    """
    if gdf.crs is None:
        raise ValueError("소스 CRS가 정의되지 않음")
    
    if str(gdf.crs) == target_crs:
        return gdf  # 변환 불필요
    
    return gdf.to_crs(target_crs)
```

### 3.2 GPKG 구조 표준
```python
# 레이어 명명 규칙
LAYER_NAMES = {
    "parcels": "필지",           # 농지 경계
    "crop_detections": "작물탐지", # AI 탐지 결과  
    "facilities": "시설물",       # 농업 시설
    "statistics": "통계",        # 집계 통계
    "metadata": "메타데이터"     # 분석 정보
}

# 필수 필드 규칙
REQUIRED_FIELDS = {
    "parcels": ["pnu", "area_sqm", "land_type"],
    "crop_detections": ["detection_id", "crop_type", "confidence"],
    "facilities": ["facility_id", "facility_type", "condition"]
}
```

## 4. 비동기 처리 규칙

### 4.1 백그라운드 작업 패턴
```python
# Celery 또는 FastAPI BackgroundTasks 사용
from fastapi import BackgroundTasks
from celery import Celery

# 장시간 작업은 비동기 처리
@router.post("/process")
async def start_processing(
    request: ProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    1. 즉시 작업 ID 반환
    2. 백그라운드에서 실제 처리
    3. 상태 조회 API 제공
    4. 완료 시 결과 저장
    """
    job_id = str(uuid.uuid4())
    background_tasks.add_task(process_data, job_id, request)
    
    return {"job_id": job_id, "status": "started"}

async def process_data(job_id: str, request: ProcessRequest):
    """실제 처리 로직"""
    try:
        # 상태 업데이트: processing
        # 처리 수행
        # 상태 업데이트: completed
        pass
    except Exception as e:
        # 상태 업데이트: failed
        pass
```

## 5. 에러 처리 및 로깅

### 5.1 에러 처리 체계
```python
# 커스텀 예외 클래스
class NongViewException(Exception):
    """기본 예외 클래스"""
    pass

class CroppingError(NongViewException):
    """크로핑 관련 오류"""
    pass

class ExportError(NongViewException):
    """내보내기 관련 오류"""
    pass

# 예외 처리 패턴
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"특정 오류 발생: {e}")
    # 복구 시도 또는 사용자 친화적 오류 반환
except Exception as e:
    logger.error(f"예상치 못한 오류: {e}", exc_info=True)
    # 일반적인 오류 응답
```

### 5.2 로깅 표준
```python
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# 로그 레벨별 사용 기준
logger.debug(f"상세 디버그 정보: {details}")          # 개발 시에만
logger.info(f"주요 처리 과정: {process_name}")        # 정상 흐름
logger.warning(f"주의 필요: {warning_message}")       # 경고
logger.error(f"오류 발생: {error_message}")           # 복구 가능한 오류
logger.critical(f"심각한 오류: {critical_error}")     # 시스템 중단 수준

# 구조화된 로깅
logger.info(
    "크로핑 완료",
    extra={
        "crop_id": crop_id,
        "processing_time": processing_time,
        "output_size": output_size
    }
)
```

## 6. 테스트 전략

### 6.1 테스트 구조
```python
# 단위 테스트 (pytest)
def test_cropping_engine():
    """크로핑 엔진 단위 테스트"""
    engine = CroppingEngine()
    # Given: 테스트 데이터 준비
    # When: 기능 실행
    # Then: 결과 검증

# 통합 테스트
@pytest.mark.asyncio
async def test_api_integration():
    """API 통합 테스트"""
    # FastAPI TestClient 사용
    response = client.post("/api/v1/crops", json=test_data)
    assert response.status_code == 201

# 성능 테스트
def test_performance_benchmark():
    """성능 벤치마크 테스트"""
    # 처리 시간 측정
    # 메모리 사용량 모니터링
```

### 6.2 테스트 데이터 관리
```python
# 픽스처 활용
@pytest.fixture
def sample_image():
    """테스트용 샘플 이미지"""
    return create_test_image()

@pytest.fixture
def sample_geometries():
    """테스트용 지오메트리"""
    return create_test_geometries()
```

## 7. 성능 최적화 규칙

### 7.1 메모리 관리
```python
# 대용량 파일 스트리밍 처리
def process_large_image(image_path: Path):
    """대용량 이미지 청크 단위 처리"""
    with rasterio.open(image_path) as src:
        # 청크 단위로 읽기
        for block_index, window in src.block_windows():
            block = src.read(window=window)
            # 처리
            yield process_block(block)

# 메모리 정리
def cleanup_resources():
    """리소스 정리"""
    import gc
    gc.collect()
```

### 7.2 병렬 처리
```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# I/O 바운드 작업: ThreadPoolExecutor
def process_io_bound_tasks(tasks):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(task) for task in tasks]
        return [future.result() for future in futures]

# CPU 바운드 작업: ProcessPoolExecutor  
def process_cpu_bound_tasks(tasks):
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(task) for task in tasks]
        return [future.result() for future in futures]
```

## 8. 보안 규칙

### 8.1 개인정보 보호
```python
# 개인정보 마스킹 함수
def mask_personal_info(data: dict) -> dict:
    """개인정보 마스킹"""
    sensitive_fields = ['owner_name', 'phone', 'address']
    
    masked = data.copy()
    for field in sensitive_fields:
        if field in masked:
            masked[field] = mask_field(masked[field], field)
    
    return masked

def mask_field(value: str, field_type: str) -> str:
    """필드별 마스킹 규칙"""
    if field_type == 'owner_name':
        return value[0] + '*' * (len(value) - 1)
    elif field_type == 'phone':
        return value[:3] + '****' + value[-4:]
    return '****'
```

### 8.2 입력 검증
```python
# Pydantic 검증 활용
from pydantic import validator

class SecureSchema(BaseModel):
    filename: str
    
    @validator('filename')
    def validate_filename(cls, v):
        # 파일명 검증 (경로 삽입 공격 방지)
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid filename")
        return v
```

## 9. 문서화 규칙

### 9.1 API 문서
```python
# Swagger/OpenAPI 자동 문서화
@router.post(
    "/crop",
    response_model=CropResponse,
    summary="이미지 크로핑",
    description="지정된 ROI 영역으로 이미지를 크롭합니다.",
    responses={
        201: {"description": "크로핑 성공"},
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"}
    }
)
async def crop_image(request: CropRequest):
    """
    이미지 크로핑 API
    
    ROI 경계를 기반으로 이미지를 크롭하고 결과를 반환합니다.
    
    **처리 과정:**
    1. ROI 검증
    2. 좌표계 변환
    3. 이미지 크로핑
    4. 결과 저장
    """
    pass
```

### 9.2 코드 문서화
```python
class SonnetClass:
    """
    Sonnet 담당 클래스
    
    이 클래스는 다음과 같은 기능을 제공합니다:
    - 기능 1: 설명
    - 기능 2: 설명
    
    Attributes:
        attr1: 속성 설명
        attr2: 속성 설명
    
    Example:
        >>> instance = SonnetClass()
        >>> result = instance.method()
        >>> print(result)
    """
    
    def __init__(self, param1: str, param2: int = 0):
        """
        초기화
        
        Args:
            param1: 매개변수 1 설명
            param2: 매개변수 2 설명 (기본값: 0)
        """
        pass
    
    def method(self, input_data: Any) -> Any:
        """
        메서드 설명
        
        Args:
            input_data: 입력 데이터 설명
            
        Returns:
            반환값 설명
            
        Raises:
            ValueError: 발생 조건 설명
            
        Example:
            >>> result = instance.method(data)
            >>> assert result is not None
        """
        pass
```

## 10. 협업 규칙

### 10.1 Opus와 협업
```python
# Opus 구현 모듈 활용
from ..pod1_data_ingestion import DataRegistry
from ..pod3_tiling import TilingEngine
from ..pod4_ai_inference import InferenceEngine
from ..pod5_merging import MergeEngine

# Sonnet이 Opus 모듈을 통합하는 패턴
class PipelineOrchestrator:
    """파이프라인 오케스트레이터 (Sonnet 담당)"""
    
    def __init__(self):
        self.data_registry = DataRegistry()      # Opus
        self.tiling_engine = TilingEngine()      # Opus
        self.inference_engine = InferenceEngine() # Opus
        self.merge_engine = MergeEngine()        # Opus
        self.cropping_engine = CroppingEngine()  # Sonnet
        self.gpkg_exporter = GPKGExporter()     # Sonnet
    
    async def process_pipeline(self, request):
        """전체 파이프라인 실행"""
        # 1. 데이터 로드 (Opus)
        # 2. 크로핑 (Sonnet)
        # 3. 타일링 (Opus)
        # 4. AI 추론 (Opus)
        # 5. 병합 (Opus)
        # 6. GPKG 내보내기 (Sonnet)
        pass
```

### 10.2 인터페이스 계약
```python
# 모듈 간 인터페이스 정의
from abc import ABC, abstractmethod

class ProcessorInterface(ABC):
    """처리기 인터페이스"""
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """처리 메서드"""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """입력 검증"""
        pass
```

---

*Version: 1.0.0*
*Created: 2025-10-26*
*Author: Claude Sonnet*
*Next Review: 2025-11-02*