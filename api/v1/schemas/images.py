"""
이미지 관리 API 스키마
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ImageFormat(str, Enum):
    """지원되는 이미지 포맷"""
    GEOTIFF = "geotiff"
    TIFF = "tiff"
    COG = "cog"
    JP2 = "jp2"


class ImageStatus(str, Enum):
    """이미지 상태"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class ImageMetadata(BaseModel):
    """이미지 메타데이터"""
    width: int = Field(..., description="이미지 너비 (픽셀)")
    height: int = Field(..., description="이미지 높이 (픽셀)")
    bands: int = Field(..., description="밴드 수")
    dtype: str = Field(..., description="데이터 타입")
    crs: str = Field(..., description="좌표계")
    transform: List[float] = Field(..., description="변환 행렬")
    bounds: Dict[str, float] = Field(..., description="경계 좌표")
    resolution: float = Field(..., description="해상도 (미터/픽셀)")
    
    class Config:
        schema_extra = {
            "example": {
                "width": 10000,
                "height": 8000,
                "bands": 3,
                "dtype": "uint8",
                "crs": "EPSG:5186",
                "transform": [0.25, 0.0, 200000.0, 0.0, -0.25, 500000.0],
                "bounds": {
                    "minx": 200000.0,
                    "miny": 498000.0, 
                    "maxx": 202500.0,
                    "maxy": 500000.0
                },
                "resolution": 0.25
            }
        }


class ImageUploadRequest(BaseModel):
    """이미지 업로드 요청"""
    filename: str = Field(..., description="파일명")
    description: Optional[str] = Field(None, description="이미지 설명")
    region_name: Optional[str] = Field(None, description="지역명")
    capture_date: Optional[datetime] = Field(None, description="촬영 일시")
    drone_model: Optional[str] = Field(None, description="드론 모델")
    camera_model: Optional[str] = Field(None, description="카메라 모델")
    altitude: Optional[float] = Field(None, description="촬영 고도 (미터)")
    overlap: Optional[float] = Field(None, description="겹침률")
    tags: Optional[List[str]] = Field(default_factory=list, description="태그")
    
    @validator('filename')
    def validate_filename(cls, v):
        allowed_extensions = ['.tif', '.tiff', '.jp2']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f"지원되지 않는 파일 형식입니다. 허용된 형식: {', '.join(allowed_extensions)}")
        return v
    
    @validator('altitude')
    def validate_altitude(cls, v):
        if v is not None and (v < 0 or v > 1000):
            raise ValueError("고도는 0-1000m 범위여야 합니다")
        return v
    
    @validator('overlap')
    def validate_overlap(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError("겹침률은 0-1 범위여야 합니다")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "namwon_20250115_ortho.tif",
                "description": "남원시 스마트빌리지 사업 지역 정사영상",
                "region_name": "남원시",
                "capture_date": "2025-01-15T10:30:00Z",
                "drone_model": "DJI Matrice 300",
                "camera_model": "Zenmuse P1",
                "altitude": 150.0,
                "overlap": 0.8,
                "tags": ["남원시", "스마트빌리지", "정사영상"]
            }
        }


class ImageUploadResponse(BaseModel):
    """이미지 업로드 응답"""
    id: str = Field(..., description="이미지 ID")
    filename: str = Field(..., description="파일명")
    file_path: str = Field(..., description="저장된 파일 경로")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    format: ImageFormat = Field(..., description="이미지 포맷")
    status: ImageStatus = Field(..., description="이미지 상태")
    upload_progress: float = Field(1.0, description="업로드 진행률")
    metadata: Optional[ImageMetadata] = Field(None, description="이미지 메타데이터")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="업로드 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "namwon_20250115_ortho.tif",
                "file_path": "/data/uploads/550e8400_namwon_20250115_ortho.tif",
                "file_size": 157286400,
                "format": "geotiff",
                "status": "ready",
                "upload_progress": 1.0,
                "uploaded_at": "2025-10-26T10:30:00Z"
            }
        }


class ImageListRequest(BaseModel):
    """이미지 목록 조회 요청"""
    status: Optional[ImageStatus] = Field(None, description="상태 필터")
    region_name: Optional[str] = Field(None, description="지역명 필터")
    format: Optional[ImageFormat] = Field(None, description="포맷 필터")
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")
    tags: Optional[List[str]] = Field(None, description="태그 필터")
    search: Optional[str] = Field(None, description="검색어")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "ready",
                "region_name": "남원시",
                "format": "geotiff",
                "date_from": "2025-01-01T00:00:00Z",
                "date_to": "2025-12-31T23:59:59Z",
                "tags": ["스마트빌리지"],
                "search": "정사영상"
            }
        }


class ImageSummary(BaseModel):
    """이미지 요약 정보"""
    id: str = Field(..., description="이미지 ID")
    filename: str = Field(..., description="파일명")
    description: Optional[str] = Field(None, description="설명")
    region_name: Optional[str] = Field(None, description="지역명")
    format: ImageFormat = Field(..., description="이미지 포맷")
    status: ImageStatus = Field(..., description="이미지 상태")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    resolution: Optional[float] = Field(None, description="해상도 (미터/픽셀)")
    area_sqm: Optional[float] = Field(None, description="커버 면적 (제곱미터)")
    capture_date: Optional[datetime] = Field(None, description="촬영 일시")
    uploaded_at: datetime = Field(..., description="업로드 시간")
    tags: List[str] = Field(default_factory=list, description="태그")
    analysis_count: int = Field(0, description="분석 횟수")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "namwon_20250115_ortho.tif",
                "description": "남원시 스마트빌리지 사업 지역 정사영상",
                "region_name": "남원시",
                "format": "geotiff",
                "status": "ready",
                "file_size": 157286400,
                "resolution": 0.25,
                "area_sqm": 6250000.0,
                "capture_date": "2025-01-15T10:30:00Z",
                "uploaded_at": "2025-01-16T09:15:00Z",
                "tags": ["남원시", "스마트빌리지"],
                "analysis_count": 3
            }
        }


class ImageListResponse(BaseModel):
    """이미지 목록 응답"""
    images: List[ImageSummary] = Field(..., description="이미지 목록")
    
    class Config:
        schema_extra = {
            "example": {
                "images": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "filename": "namwon_20250115_ortho.tif",
                        "region_name": "남원시",
                        "format": "geotiff",
                        "status": "ready",
                        "file_size": 157286400,
                        "uploaded_at": "2025-01-16T09:15:00Z"
                    }
                ]
            }
        }


class ImageDetailResponse(BaseModel):
    """이미지 상세 정보 응답"""
    id: str = Field(..., description="이미지 ID")
    filename: str = Field(..., description="파일명")
    description: Optional[str] = Field(None, description="설명")
    region_name: Optional[str] = Field(None, description="지역명")
    format: ImageFormat = Field(..., description="이미지 포맷")
    status: ImageStatus = Field(..., description="이미지 상태")
    file_path: str = Field(..., description="파일 경로")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    metadata: Optional[ImageMetadata] = Field(None, description="이미지 메타데이터")
    
    # 촬영 정보
    capture_date: Optional[datetime] = Field(None, description="촬영 일시")
    drone_model: Optional[str] = Field(None, description="드론 모델")
    camera_model: Optional[str] = Field(None, description="카메라 모델")
    altitude: Optional[float] = Field(None, description="촬영 고도")
    overlap: Optional[float] = Field(None, description="겹침률")
    
    # 메타 정보
    tags: List[str] = Field(default_factory=list, description="태그")
    uploaded_at: datetime = Field(..., description="업로드 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    uploaded_by: Optional[str] = Field(None, description="업로드한 사용자")
    
    # 분석 정보
    analysis_count: int = Field(0, description="분석 횟수")
    last_analysis_at: Optional[datetime] = Field(None, description="마지막 분석 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "namwon_20250115_ortho.tif",
                "description": "남원시 스마트빌리지 사업 지역 정사영상",
                "region_name": "남원시",
                "format": "geotiff",
                "status": "ready",
                "file_path": "/data/uploads/550e8400_namwon_20250115_ortho.tif",
                "file_size": 157286400,
                "capture_date": "2025-01-15T10:30:00Z",
                "drone_model": "DJI Matrice 300",
                "camera_model": "Zenmuse P1",
                "altitude": 150.0,
                "overlap": 0.8,
                "tags": ["남원시", "스마트빌리지"],
                "uploaded_at": "2025-01-16T09:15:00Z",
                "updated_at": "2025-01-16T09:15:00Z",
                "analysis_count": 3,
                "last_analysis_at": "2025-01-20T14:30:00Z"
            }
        }


class ImageUpdateRequest(BaseModel):
    """이미지 정보 수정 요청"""
    description: Optional[str] = Field(None, description="설명")
    region_name: Optional[str] = Field(None, description="지역명")
    tags: Optional[List[str]] = Field(None, description="태그")
    
    class Config:
        schema_extra = {
            "example": {
                "description": "남원시 스마트빌리지 사업 지역 정사영상 (수정됨)",
                "region_name": "남원시",
                "tags": ["남원시", "스마트빌리지", "2025년"]
            }
        }


class ImageDeleteResponse(BaseModel):
    """이미지 삭제 응답"""
    deleted_id: str = Field(..., description="삭제된 이미지 ID")
    message: str = Field(..., description="삭제 결과 메시지")
    
    class Config:
        schema_extra = {
            "example": {
                "deleted_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "이미지가 성공적으로 삭제되었습니다"
            }
        }