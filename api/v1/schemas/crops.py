"""
크로핑 API 스키마
"""

from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from ...src.pod2_cropping.schemas import CropConfig, ROIBounds, GeometryData


class CropJobStatus(str, Enum):
    """크로핑 작업 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CropJobRequest(BaseModel):
    """크로핑 작업 요청"""
    image_id: str = Field(..., description="대상 이미지 ID")
    geometries: List[GeometryData] = Field(..., description="크로핑할 지오메트리 리스트")
    config: CropConfig = Field(default_factory=CropConfig, description="크로핑 설정")
    job_name: Optional[str] = Field(None, description="작업 이름")
    description: Optional[str] = Field(None, description="작업 설명")
    
    @validator('geometries')
    def validate_geometries(cls, v):
        if len(v) == 0:
            raise ValueError("최소 하나의 지오메트리가 필요합니다")
        if len(v) > 100:
            raise ValueError("한 번에 최대 100개의 지오메트리까지 처리 가능합니다")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "geometries": [
                    {
                        "coordinates": [[[127.1, 35.8], [127.2, 35.8], [127.2, 35.9], [127.1, 35.9], [127.1, 35.8]]],
                        "geometry_type": "Polygon",
                        "crs": "EPSG:4326",
                        "properties": {
                            "pnu": "4513010100100010000",
                            "land_type": "농지",
                            "owner": "농업인"
                        }
                    }
                ],
                "config": {
                    "buffer_distance": 10.0,
                    "use_convex_hull": True,
                    "min_area_threshold": 100.0
                },
                "job_name": "남원시 필지별 크로핑",
                "description": "스마트빌리지 사업 대상 필지 크로핑 작업"
            }
        }


class CropJobResponse(BaseModel):
    """크로핑 작업 생성 응답"""
    job_id: str = Field(..., description="작업 ID")
    image_id: str = Field(..., description="대상 이미지 ID")
    status: CropJobStatus = Field(..., description="작업 상태")
    geometry_count: int = Field(..., description="처리할 지오메트리 개수")
    estimated_duration: int = Field(..., description="예상 소요 시간 (초)")
    created_at: datetime = Field(default_factory=datetime.now, description="작업 생성 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "crop_550e8400-e29b-41d4-a716-446655440001",
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "geometry_count": 15,
                "estimated_duration": 45,
                "created_at": "2025-10-26T10:30:00Z"
            }
        }


class CropResultSummary(BaseModel):
    """크롭 결과 요약"""
    crop_id: str = Field(..., description="크롭 ID")
    geometry_index: int = Field(..., description="지오메트리 인덱스")
    roi_bounds: ROIBounds = Field(..., description="ROI 경계")
    output_filename: str = Field(..., description="출력 파일명")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    cropped_size: Tuple[int, int] = Field(..., description="크롭된 이미지 크기 (width, height)")
    processing_time: float = Field(..., description="처리 시간 (초)")
    
    class Config:
        schema_extra = {
            "example": {
                "crop_id": "crop_550e8400-e29b-41d4-a716-446655440002",
                "geometry_index": 0,
                "roi_bounds": {
                    "minx": 200000.0,
                    "miny": 400000.0,
                    "maxx": 201000.0,
                    "maxy": 401000.0,
                    "crs": "EPSG:5186"
                },
                "output_filename": "namwon_20250115_4513010100100010000_crop.tif",
                "file_size": 25600000,
                "cropped_size": [4000, 4000],
                "processing_time": 1.25
            }
        }


class CropJobStatusResponse(BaseModel):
    """크로핑 작업 상태 응답"""
    job_id: str = Field(..., description="작업 ID")
    image_id: str = Field(..., description="대상 이미지 ID")
    status: CropJobStatus = Field(..., description="작업 상태")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="진행률 (0.0-1.0)")
    message: str = Field("", description="상태 메시지")
    
    # 시간 정보
    created_at: datetime = Field(..., description="작업 생성 시간")
    started_at: Optional[datetime] = Field(None, description="작업 시작 시간")
    completed_at: Optional[datetime] = Field(None, description="작업 완료 시간")
    
    # 처리 통계
    total_geometries: int = Field(..., description="전체 지오메트리 수")
    processed_geometries: int = Field(0, description="처리 완료된 지오메트리 수")
    successful_crops: int = Field(0, description="성공한 크롭 수")
    failed_crops: int = Field(0, description="실패한 크롭 수")
    
    # 결과 정보 (완료 시에만)
    results: Optional[List[CropResultSummary]] = Field(None, description="크롭 결과 목록")
    total_processing_time: Optional[float] = Field(None, description="총 처리 시간 (초)")
    
    # 에러 정보 (실패 시에만)
    error_message: Optional[str] = Field(None, description="에러 메시지")
    error_details: Optional[List[str]] = Field(None, description="상세 에러 목록")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "crop_550e8400-e29b-41d4-a716-446655440001",
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": 0.6,
                "message": "지오메트리 9/15 처리 중...",
                "created_at": "2025-10-26T10:30:00Z",
                "started_at": "2025-10-26T10:30:15Z",
                "total_geometries": 15,
                "processed_geometries": 9,
                "successful_crops": 8,
                "failed_crops": 1
            }
        }


class CropJobListRequest(BaseModel):
    """크로핑 작업 목록 조회 요청"""
    status: Optional[CropJobStatus] = Field(None, description="상태 필터")
    image_id: Optional[str] = Field(None, description="이미지 ID 필터")
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")
    user_id: Optional[str] = Field(None, description="사용자 ID 필터")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "date_from": "2025-10-01T00:00:00Z",
                "date_to": "2025-10-31T23:59:59Z"
            }
        }


class CropJobSummary(BaseModel):
    """크로핑 작업 요약"""
    job_id: str = Field(..., description="작업 ID")
    job_name: Optional[str] = Field(None, description="작업 이름")
    image_id: str = Field(..., description="대상 이미지 ID")
    image_filename: str = Field(..., description="이미지 파일명")
    status: CropJobStatus = Field(..., description="작업 상태")
    progress: float = Field(..., description="진행률")
    geometry_count: int = Field(..., description="지오메트리 수")
    successful_crops: int = Field(..., description="성공한 크롭 수")
    created_at: datetime = Field(..., description="생성 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    created_by: Optional[str] = Field(None, description="생성한 사용자")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "crop_550e8400-e29b-41d4-a716-446655440001",
                "job_name": "남원시 필지별 크로핑",
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "image_filename": "namwon_20250115_ortho.tif",
                "status": "completed",
                "progress": 1.0,
                "geometry_count": 15,
                "successful_crops": 14,
                "created_at": "2025-10-26T10:30:00Z",
                "completed_at": "2025-10-26T10:35:30Z",
                "created_by": "admin"
            }
        }


class CropJobListResponse(BaseModel):
    """크로핑 작업 목록 응답"""
    jobs: List[CropJobSummary] = Field(..., description="작업 목록")
    
    class Config:
        schema_extra = {
            "example": {
                "jobs": [
                    {
                        "job_id": "crop_550e8400-e29b-41d4-a716-446655440001",
                        "job_name": "남원시 필지별 크로핑",
                        "image_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "completed",
                        "progress": 1.0,
                        "geometry_count": 15,
                        "successful_crops": 14,
                        "created_at": "2025-10-26T10:30:00Z"
                    }
                ]
            }
        }


class CropDownloadRequest(BaseModel):
    """크롭 결과 다운로드 요청"""
    crop_ids: Optional[List[str]] = Field(None, description="다운로드할 크롭 ID 목록")
    format: str = Field("zip", description="다운로드 포맷 (zip, tar)")
    include_metadata: bool = Field(True, description="메타데이터 포함 여부")
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['zip', 'tar']:
            raise ValueError("지원되는 포맷: zip, tar")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "crop_ids": [
                    "crop_550e8400-e29b-41d4-a716-446655440002",
                    "crop_550e8400-e29b-41d4-a716-446655440003"
                ],
                "format": "zip",
                "include_metadata": True
            }
        }


class CropDownloadResponse(BaseModel):
    """크롭 결과 다운로드 응답"""
    download_id: str = Field(..., description="다운로드 ID")
    download_url: str = Field(..., description="다운로드 URL")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    expires_at: datetime = Field(..., description="만료 시간")
    crop_count: int = Field(..., description="포함된 크롭 수")
    
    class Config:
        schema_extra = {
            "example": {
                "download_id": "dl_550e8400-e29b-41d4-a716-446655440004",
                "download_url": "/api/v1/crops/download/dl_550e8400-e29b-41d4-a716-446655440004",
                "file_size": 127834560,
                "expires_at": "2025-10-26T22:30:00Z",
                "crop_count": 2
            }
        }


class CropValidationRequest(BaseModel):
    """크로핑 검증 요청"""
    image_id: str = Field(..., description="대상 이미지 ID")
    geometries: List[GeometryData] = Field(..., description="검증할 지오메트리 리스트")
    
    class Config:
        schema_extra = {
            "example": {
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "geometries": [
                    {
                        "coordinates": [[[127.1, 35.8], [127.2, 35.8], [127.2, 35.9], [127.1, 35.9], [127.1, 35.8]]],
                        "geometry_type": "Polygon",
                        "crs": "EPSG:4326",
                        "properties": {"pnu": "4513010100100010000"}
                    }
                ]
            }
        }


class GeometryValidationResult(BaseModel):
    """지오메트리 검증 결과"""
    index: int = Field(..., description="지오메트리 인덱스")
    is_valid: bool = Field(..., description="유효성 여부")
    errors: List[str] = Field(default_factory=list, description="검증 에러 목록")
    warnings: List[str] = Field(default_factory=list, description="경고 메시지 목록")
    estimated_crop_size: Optional[Tuple[int, int]] = Field(None, description="예상 크롭 크기")
    estimated_file_size: Optional[int] = Field(None, description="예상 파일 크기 (바이트)")
    
    class Config:
        schema_extra = {
            "example": {
                "index": 0,
                "is_valid": True,
                "errors": [],
                "warnings": ["면적이 임계값에 가깝습니다"],
                "estimated_crop_size": [4000, 4000],
                "estimated_file_size": 25600000
            }
        }


class CropValidationResponse(BaseModel):
    """크로핑 검증 응답"""
    image_id: str = Field(..., description="대상 이미지 ID")
    total_geometries: int = Field(..., description="전체 지오메트리 수")
    valid_geometries: int = Field(..., description="유효한 지오메트리 수")
    invalid_geometries: int = Field(..., description="무효한 지오메트리 수")
    validation_results: List[GeometryValidationResult] = Field(..., description="검증 결과 목록")
    estimated_total_processing_time: int = Field(..., description="예상 총 처리 시간 (초)")
    estimated_total_file_size: int = Field(..., description="예상 총 파일 크기 (바이트)")
    
    class Config:
        schema_extra = {
            "example": {
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "total_geometries": 1,
                "valid_geometries": 1,
                "invalid_geometries": 0,
                "validation_results": [
                    {
                        "index": 0,
                        "is_valid": True,
                        "errors": [],
                        "warnings": [],
                        "estimated_crop_size": [4000, 4000],
                        "estimated_file_size": 25600000
                    }
                ],
                "estimated_total_processing_time": 5,
                "estimated_total_file_size": 25600000
            }
        }