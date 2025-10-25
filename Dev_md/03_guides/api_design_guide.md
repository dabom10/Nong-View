# API 설계 가이드

## 1. API 아키텍처

### 1.1 RESTful 원칙
- **리소스 중심**: URL은 리소스를 나타냄
- **HTTP 메서드**: 적절한 메서드 사용
- **상태 비저장**: 각 요청은 독립적
- **계층적 구조**: 리소스 간 관계 표현

### 1.2 URL 설계

#### 기본 규칙
```
# 복수형 명사 사용
GET /api/v1/images         # ✅ Good
GET /api/v1/image          # ❌ Bad

# 계층적 구조
GET /api/v1/images/{id}/tiles
GET /api/v1/parcels/{pnu}/statistics

# 동사 대신 명사 사용
POST /api/v1/analyses      # ✅ Good (분석 생성)
POST /api/v1/analyze       # ❌ Bad
```

#### URL 패턴
```
# Collection
GET    /api/v1/images              # 목록 조회
POST   /api/v1/images              # 새 리소스 생성

# Item
GET    /api/v1/images/{id}         # 단일 조회
PUT    /api/v1/images/{id}         # 전체 수정
PATCH  /api/v1/images/{id}         # 부분 수정
DELETE /api/v1/images/{id}         # 삭제

# Sub-resource
GET    /api/v1/images/{id}/tiles   # 하위 리소스 조회
POST   /api/v1/images/{id}/analyze # 액션 실행
```

## 2. API 엔드포인트 설계

### 2.1 이미지 관리 API

```python
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List, Optional

app = FastAPI()

# 이미지 업로드
@app.post("/api/v1/images", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    metadata: Optional[ImageMetadata] = None
):
    """
    Upload ortho-image (TIF/ECW)
    
    Returns:
        ImageResponse with image_id and metadata
    """
    pass

# 이미지 목록 조회
@app.get("/api/v1/images", response_model=List[ImageSummary])
async def list_images(
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """
    List images with pagination and filtering
    """
    pass

# 이미지 상세 조회
@app.get("/api/v1/images/{image_id}", response_model=ImageDetail)
async def get_image(image_id: UUID):
    """
    Get image details including metadata
    """
    pass
```

### 2.2 분석 API

```python
# 분석 시작
@app.post("/api/v1/analyses", response_model=AnalysisJob)
async def start_analysis(request: AnalysisRequest):
    """
    Start analysis job
    
    Request body:
    {
        "image_id": "uuid",
        "roi": {
            "type": "bbox",
            "coordinates": [minx, miny, maxx, maxy]
        },
        "models": ["crop", "facility", "landuse"],
        "options": {
            "confidence_threshold": 0.5,
            "tile_size": 640
        }
    }
    """
    pass

# 분석 상태 조회
@app.get("/api/v1/analyses/{job_id}", response_model=AnalysisStatus)
async def get_analysis_status(job_id: UUID):
    """
    Get analysis job status
    
    Response:
    {
        "job_id": "uuid",
        "status": "processing",
        "progress": 0.75,
        "eta_seconds": 120
    }
    """
    pass

# 분석 결과 조회
@app.get("/api/v1/analyses/{job_id}/results", response_model=AnalysisResults)
async def get_analysis_results(
    job_id: UUID,
    format: str = "json"
):
    """
    Get analysis results
    
    Formats: json, geojson, csv
    """
    pass
```

### 2.3 타일 API

```python
# 타일 생성
@app.post("/api/v1/images/{image_id}/tiles", response_model=TilingJob)
async def create_tiles(
    image_id: UUID,
    config: TilingConfig
):
    """
    Generate tiles from image
    """
    pass

# 타일 목록
@app.get("/api/v1/images/{image_id}/tiles", response_model=List[TileInfo])
async def list_tiles(
    image_id: UUID,
    bounds: Optional[str] = None  # "minx,miny,maxx,maxy"
):
    """
    List tiles for an image
    """
    pass

# 타일 이미지 조회
@app.get("/api/v1/tiles/{tile_id}/image")
async def get_tile_image(tile_id: UUID):
    """
    Get tile image file
    """
    return FileResponse(tile_path, media_type="image/tiff")
```

### 2.4 필지 통계 API

```python
# 필지별 통계
@app.get("/api/v1/parcels/{pnu}/statistics", response_model=ParcelStats)
async def get_parcel_statistics(
    pnu: str,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """
    Get statistics for a parcel
    """
    pass

# 지역 통계
@app.get("/api/v1/statistics/regional", response_model=RegionalStats)
async def get_regional_statistics(
    region_code: str,
    aggregation: str = "daily"  # daily, weekly, monthly
):
    """
    Get regional statistics
    """
    pass
```

### 2.5 Export API

```python
# GPKG Export
@app.post("/api/v1/export/gpkg", response_model=ExportJob)
async def export_gpkg(request: ExportRequest):
    """
    Export results as GeoPackage
    """
    pass

# Export 상태
@app.get("/api/v1/export/{export_id}")
async def get_export_status(export_id: UUID):
    """
    Get export job status
    """
    pass

# Download
@app.get("/api/v1/export/{export_id}/download")
async def download_export(export_id: UUID):
    """
    Download exported file
    """
    return FileResponse(
        file_path,
        media_type="application/geopackage+sqlite3",
        filename=f"nongview_{export_id}.gpkg"
    )
```

## 3. 요청/응답 스키마

### 3.1 공통 응답 포맷

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class ResponseBase(BaseModel, Generic[T]):
    """Base response wrapper"""
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    meta: Optional[MetaInfo] = None

class ErrorDetail(BaseModel):
    """Error information"""
    code: str
    message: str
    details: Optional[List[str]] = None

class MetaInfo(BaseModel):
    """Metadata for response"""
    timestamp: datetime
    version: str = "1.0.0"
    request_id: Optional[str] = None
```

### 3.2 페이지네이션

```python
class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response"""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool
```

### 3.3 필터링 및 정렬

```python
class FilterParams(BaseModel):
    """Common filter parameters"""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class SortParams(BaseModel):
    """Sort parameters"""
    sort_by: str = "created_at"
    order: str = Field("desc", regex="^(asc|desc)$")
```

## 4. 에러 처리

### 4.1 HTTP 상태 코드

```python
from fastapi import HTTPException, status

# 성공
200 OK                  # 조회 성공
201 Created            # 생성 성공
204 No Content         # 삭제 성공

# 클라이언트 에러
400 Bad Request        # 잘못된 요청
401 Unauthorized       # 인증 필요
403 Forbidden          # 권한 없음
404 Not Found          # 리소스 없음
409 Conflict           # 충돌 (중복 등)
422 Unprocessable Entity # 검증 실패

# 서버 에러
500 Internal Server Error # 서버 오류
503 Service Unavailable  # 서비스 불가
```

### 4.2 에러 응답 예시

```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": exc.errors()
            }
        }
    )

@app.get("/api/v1/images/{image_id}")
async def get_image(image_id: UUID):
    image = db.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "IMAGE_NOT_FOUND",
                "message": f"Image {image_id} not found"
            }
        )
    return image
```

## 5. 인증 및 권한

### 5.1 JWT 인증

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )

@app.get("/api/v1/protected")
async def protected_route(user=Depends(verify_token)):
    return {"user": user}
```

### 5.2 API Key 인증

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return x_api_key

@app.get("/api/v1/data")
async def get_data(api_key=Depends(verify_api_key)):
    return {"data": "sensitive"}
```

## 6. 비동기 처리

### 6.1 백그라운드 작업

```python
from fastapi import BackgroundTasks

@app.post("/api/v1/analyses")
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    job_id = create_job()
    background_tasks.add_task(
        run_analysis,
        job_id,
        request
    )
    return {
        "job_id": job_id,
        "status": "queued"
    }
```

### 6.2 WebSocket

```python
@app.websocket("/ws/analysis/{job_id}")
async def analysis_progress(
    websocket: WebSocket,
    job_id: UUID
):
    await websocket.accept()
    
    while True:
        progress = get_job_progress(job_id)
        await websocket.send_json({
            "progress": progress,
            "status": get_job_status(job_id)
        })
        
        if progress >= 1.0:
            break
            
        await asyncio.sleep(1)
    
    await websocket.close()
```

## 7. API 문서화

### 7.1 OpenAPI 설정

```python
from fastapi import FastAPI

app = FastAPI(
    title="Nong-View API",
    description="Agricultural Image Analysis Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
```

### 7.2 엔드포인트 문서화

```python
@app.post(
    "/api/v1/images",
    response_model=ImageResponse,
    summary="Upload image",
    description="Upload ortho-image for analysis",
    response_description="Uploaded image information",
    tags=["Images"]
)
async def upload_image(
    file: UploadFile = File(
        ...,
        description="Image file (TIF or ECW format)"
    ),
    metadata: ImageMetadata = Body(
        None,
        description="Optional image metadata"
    )
):
    """
    Upload an ortho-image for analysis.
    
    - **file**: Image file in TIF or ECW format
    - **metadata**: Optional metadata including capture date and drone info
    
    Returns image ID and processing status.
    """
    pass
```

## 8. 성능 최적화

### 8.1 캐싱

```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@app.get("/api/v1/statistics/regional")
@cache(expire=300)  # Cache for 5 minutes
async def get_regional_statistics(region_code: str):
    return compute_statistics(region_code)
```

### 8.2 Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/images")
@limiter.limit("10/minute")
async def list_images(request: Request):
    pass
```

---

*Version: 1.0.0*
*Last Updated: 2025-10-26*