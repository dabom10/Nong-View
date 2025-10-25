"""
GPKG Export API 스키마
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from ...src.pod6_gpkg_export.schemas import ExportConfig, LayerConfig, PrivacyConfig


class ExportJobStatus(str, Enum):
    """내보내기 작업 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(str, Enum):
    """내보내기 포맷"""
    GPKG = "gpkg"
    SHAPEFILE = "shapefile"
    GEOJSON = "geojson"


class ExportJobRequest(BaseModel):
    """GPKG 내보내기 요청"""
    analysis_ids: List[str] = Field(..., description="포함할 분석 결과 ID 리스트")
    region_name: str = Field(..., description="지역명")
    export_purpose: str = Field(default="행정보고", description="내보내기 목적")
    format: ExportFormat = Field(default=ExportFormat.GPKG, description="내보내기 포맷")
    config: ExportConfig = Field(default_factory=ExportConfig, description="내보내기 설정")
    job_name: Optional[str] = Field(None, description="작업 이름")
    description: Optional[str] = Field(None, description="작업 설명")
    
    @validator('analysis_ids')
    def validate_analysis_ids(cls, v):
        if len(v) == 0:
            raise ValueError("최소 하나의 분석 결과 ID가 필요합니다")
        if len(v) > 50:
            raise ValueError("한 번에 최대 50개의 분석 결과까지 처리 가능합니다")
        return v
    
    @validator('region_name')
    def validate_region_name(cls, v):
        if len(v.strip()) == 0:
            raise ValueError("지역명은 필수입니다")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_ids": [
                    "analysis_550e8400-e29b-41d4-a716-446655440001",
                    "analysis_550e8400-e29b-41d4-a716-446655440002"
                ],
                "region_name": "남원시",
                "export_purpose": "스마트빌리지 사업 현황 보고",
                "format": "gpkg",
                "config": {
                    "output_crs": "EPSG:5186",
                    "include_statistics": True,
                    "include_metadata": True,
                    "privacy_config": {
                        "mask_owner_names": True,
                        "mask_phone_numbers": True
                    }
                },
                "job_name": "남원시 2025년 1월 현황 보고서",
                "description": "스마트빌리지 사업 관련 농지 현황 분석 결과"
            }
        }


class ExportJobResponse(BaseModel):
    """내보내기 작업 생성 응답"""
    job_id: str = Field(..., description="작업 ID")
    region_name: str = Field(..., description="지역명")
    format: ExportFormat = Field(..., description="내보내기 포맷")
    status: ExportJobStatus = Field(..., description="작업 상태")
    analysis_count: int = Field(..., description="포함된 분석 결과 개수")
    estimated_duration: int = Field(..., description="예상 소요 시간 (초)")
    created_at: datetime = Field(default_factory=datetime.now, description="작업 생성 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "export_550e8400-e29b-41d4-a716-446655440003",
                "region_name": "남원시",
                "format": "gpkg",
                "status": "pending",
                "analysis_count": 2,
                "estimated_duration": 30,
                "created_at": "2025-10-26T14:30:00Z"
            }
        }


class LayerStatisticsSummary(BaseModel):
    """레이어 통계 요약"""
    layer_name: str = Field(..., description="레이어 이름")
    feature_count: int = Field(..., description="피처 개수")
    total_area_sqm: float = Field(default=0.0, description="총 면적 (제곱미터)")
    area_by_type: Dict[str, float] = Field(default_factory=dict, description="타입별 면적")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="품질 점수 (0.0-1.0)")
    
    class Config:
        schema_extra = {
            "example": {
                "layer_name": "crop_detection",
                "feature_count": 1520,
                "total_area_sqm": 245000.0,
                "area_by_type": {
                    "조사료": 125000.0,
                    "사료작물": 87000.0,
                    "기타": 33000.0
                },
                "quality_score": 0.92
            }
        }


class ExportJobStatusResponse(BaseModel):
    """내보내기 작업 상태 응답"""
    job_id: str = Field(..., description="작업 ID")
    region_name: str = Field(..., description="지역명")
    format: ExportFormat = Field(..., description="내보내기 포맷")
    status: ExportJobStatus = Field(..., description="작업 상태")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="진행률 (0.0-1.0)")
    message: str = Field("", description="상태 메시지")
    
    # 시간 정보
    created_at: datetime = Field(..., description="작업 생성 시간")
    started_at: Optional[datetime] = Field(None, description="작업 시작 시간")
    completed_at: Optional[datetime] = Field(None, description="작업 완료 시간")
    
    # 처리 통계
    total_analyses: int = Field(..., description="전체 분석 결과 수")
    processed_analyses: int = Field(0, description="처리 완료된 분석 결과 수")
    current_step: str = Field("", description="현재 처리 단계")
    total_steps: int = Field(1, description="전체 처리 단계 수")
    
    # 결과 정보 (완료 시에만)
    output_filename: Optional[str] = Field(None, description="출력 파일명")
    file_size: Optional[int] = Field(None, description="파일 크기 (바이트)")
    layer_statistics: Optional[List[LayerStatisticsSummary]] = Field(None, description="레이어별 통계")
    
    # 품질 정보
    data_quality_score: Optional[float] = Field(None, description="데이터 품질 점수")
    privacy_compliance: Optional[bool] = Field(None, description="개인정보 보호 준수 여부")
    
    # 에러 정보 (실패 시에만)
    error_message: Optional[str] = Field(None, description="에러 메시지")
    error_details: Optional[List[str]] = Field(None, description="상세 에러 목록")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "export_550e8400-e29b-41d4-a716-446655440003",
                "region_name": "남원시",
                "format": "gpkg",
                "status": "processing",
                "progress": 0.75,
                "message": "메타데이터 생성 중...",
                "created_at": "2025-10-26T14:30:00Z",
                "started_at": "2025-10-26T14:30:05Z",
                "total_analyses": 2,
                "processed_analyses": 2,
                "current_step": "메타데이터 생성",
                "total_steps": 4,
                "data_quality_score": 0.92,
                "privacy_compliance": True
            }
        }


class ExportJobSummary(BaseModel):
    """내보내기 작업 요약"""
    job_id: str = Field(..., description="작업 ID")
    job_name: Optional[str] = Field(None, description="작업 이름")
    region_name: str = Field(..., description="지역명")
    format: ExportFormat = Field(..., description="내보내기 포맷")
    status: ExportJobStatus = Field(..., description="작업 상태")
    progress: float = Field(..., description="진행률")
    analysis_count: int = Field(..., description="분석 결과 수")
    file_size: Optional[int] = Field(None, description="파일 크기 (바이트)")
    created_at: datetime = Field(..., description="생성 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    created_by: Optional[str] = Field(None, description="생성한 사용자")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "export_550e8400-e29b-41d4-a716-446655440003",
                "job_name": "남원시 2025년 1월 현황 보고서",
                "region_name": "남원시",
                "format": "gpkg",
                "status": "completed",
                "progress": 1.0,
                "analysis_count": 2,
                "file_size": 15728640,
                "created_at": "2025-10-26T14:30:00Z",
                "completed_at": "2025-10-26T14:32:15Z",
                "created_by": "admin"
            }
        }


class ExportJobListResponse(BaseModel):
    """내보내기 작업 목록 응답"""
    jobs: List[ExportJobSummary] = Field(..., description="작업 목록")
    
    class Config:
        schema_extra = {
            "example": {
                "jobs": [
                    {
                        "job_id": "export_550e8400-e29b-41d4-a716-446655440003",
                        "job_name": "남원시 2025년 1월 현황 보고서",
                        "region_name": "남원시",
                        "format": "gpkg",
                        "status": "completed",
                        "progress": 1.0,
                        "analysis_count": 2,
                        "file_size": 15728640,
                        "created_at": "2025-10-26T14:30:00Z"
                    }
                ]
            }
        }


class ExportDownloadResponse(BaseModel):
    """내보내기 결과 다운로드 응답"""
    download_id: str = Field(..., description="다운로드 ID")
    download_url: str = Field(..., description="다운로드 URL")
    filename: str = Field(..., description="파일명")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    format: ExportFormat = Field(..., description="파일 포맷")
    expires_at: datetime = Field(..., description="만료 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "download_id": "dl_export_550e8400-e29b-41d4-a716-446655440004",
                "download_url": "/api/v1/exports/download/dl_export_550e8400-e29b-41d4-a716-446655440004",
                "filename": "namwon_20251026_report.gpkg",
                "file_size": 15728640,
                "format": "gpkg",
                "expires_at": "2025-10-27T14:30:00Z"
            }
        }


class ExportValidationRequest(BaseModel):
    """내보내기 사전 검증 요청"""
    analysis_ids: List[str] = Field(..., description="검증할 분석 결과 ID 리스트")
    region_name: str = Field(..., description="지역명")
    config: ExportConfig = Field(default_factory=ExportConfig, description="내보내기 설정")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_ids": [
                    "analysis_550e8400-e29b-41d4-a716-446655440001",
                    "analysis_550e8400-e29b-41d4-a716-446655440002"
                ],
                "region_name": "남원시",
                "config": {
                    "output_crs": "EPSG:5186",
                    "include_statistics": True
                }
            }
        }


class AnalysisValidationResult(BaseModel):
    """분석 결과 검증 결과"""
    analysis_id: str = Field(..., description="분석 결과 ID")
    is_valid: bool = Field(..., description="유효성 여부")
    errors: List[str] = Field(default_factory=list, description="검증 에러 목록")
    warnings: List[str] = Field(default_factory=list, description="경고 메시지 목록")
    feature_count: int = Field(0, description="피처 개수")
    estimated_file_size: int = Field(0, description="예상 파일 크기 기여분 (바이트)")
    data_quality_score: float = Field(0.0, description="데이터 품질 점수")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "analysis_550e8400-e29b-41d4-a716-446655440001",
                "is_valid": True,
                "errors": [],
                "warnings": ["일부 필지에서 신뢰도가 낮은 탐지 결과가 있습니다"],
                "feature_count": 1520,
                "estimated_file_size": 7864320,
                "data_quality_score": 0.92
            }
        }


class ExportValidationResponse(BaseModel):
    """내보내기 사전 검증 응답"""
    region_name: str = Field(..., description="지역명")
    total_analyses: int = Field(..., description="전체 분석 결과 수")
    valid_analyses: int = Field(..., description="유효한 분석 결과 수")
    invalid_analyses: int = Field(..., description="무효한 분석 결과 수")
    validation_results: List[AnalysisValidationResult] = Field(..., description="검증 결과 목록")
    
    # 전체 통계
    total_features: int = Field(0, description="총 피처 개수")
    estimated_file_size: int = Field(0, description="예상 파일 크기 (바이트)")
    estimated_processing_time: int = Field(0, description="예상 처리 시간 (초)")
    overall_quality_score: float = Field(0.0, description="전체 품질 점수")
    
    # 개인정보 보호 분석
    privacy_issues: List[str] = Field(default_factory=list, description="개인정보 보호 이슈")
    sensitive_field_count: int = Field(0, description="민감 정보 필드 수")
    
    class Config:
        schema_extra = {
            "example": {
                "region_name": "남원시",
                "total_analyses": 2,
                "valid_analyses": 2,
                "invalid_analyses": 0,
                "validation_results": [
                    {
                        "analysis_id": "analysis_550e8400-e29b-41d4-a716-446655440001",
                        "is_valid": True,
                        "errors": [],
                        "warnings": [],
                        "feature_count": 1520,
                        "estimated_file_size": 7864320,
                        "data_quality_score": 0.92
                    }
                ],
                "total_features": 3040,
                "estimated_file_size": 15728640,
                "estimated_processing_time": 30,
                "overall_quality_score": 0.91,
                "privacy_issues": ["소유자명 정보가 포함되어 있습니다"],
                "sensitive_field_count": 2
            }
        }


class ExportTemplateRequest(BaseModel):
    """내보내기 템플릿 요청"""
    template_name: str = Field(..., description="템플릿 이름")
    region_type: str = Field(..., description="지역 타입 (시군구, 읍면동 등)")
    purpose: str = Field(..., description="사용 목적")
    
    class Config:
        schema_extra = {
            "example": {
                "template_name": "스마트빌리지_현황보고",
                "region_type": "시군구",
                "purpose": "행정보고"
            }
        }


class ExportTemplateResponse(BaseModel):
    """내보내기 템플릿 응답"""
    template_id: str = Field(..., description="템플릿 ID")
    template_name: str = Field(..., description="템플릿 이름")
    description: str = Field(..., description="템플릿 설명")
    config: ExportConfig = Field(..., description="권장 설정")
    required_layers: List[str] = Field(..., description="필수 레이어 목록")
    optional_layers: List[str] = Field(..., description="선택적 레이어 목록")
    
    class Config:
        schema_extra = {
            "example": {
                "template_id": "tmpl_smart_village_report",
                "template_name": "스마트빌리지 현황보고",
                "description": "스마트빌리지 사업 관련 농지 현황 분석 결과 표준 보고서",
                "config": {
                    "output_crs": "EPSG:5186",
                    "include_statistics": True,
                    "include_metadata": True,
                    "privacy_config": {
                        "mask_owner_names": True,
                        "mask_phone_numbers": True
                    }
                },
                "required_layers": ["parcels", "crop_detections"],
                "optional_layers": ["facilities", "statistics"]
            }
        }