"""
POD6 GPKG Export 관련 스키마 정의
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class LayerConfig(BaseModel):
    """레이어 설정"""
    name: str = Field(..., description="레이어 이름")
    geometry_type: Literal["Point", "LineString", "Polygon"] = Field(..., description="지오메트리 타입")
    fields: Dict[str, str] = Field(default_factory=dict, description="필드 정의 (이름: 타입)")
    include_features: bool = Field(default=True, description="피처 포함 여부")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "parcels",
                "geometry_type": "Polygon",
                "fields": {
                    "pnu": "str",
                    "land_type": "str",
                    "area_sqm": "float",
                    "crop_type": "str",
                    "detection_confidence": "float"
                },
                "include_features": True
            }
        }


class PrivacyConfig(BaseModel):
    """개인정보 보호 설정"""
    mask_owner_names: bool = Field(default=True, description="소유자명 마스킹")
    mask_phone_numbers: bool = Field(default=True, description="전화번호 마스킹")
    remove_personal_fields: List[str] = Field(default_factory=list, description="제거할 개인정보 필드")
    anonymize_locations: bool = Field(default=False, description="위치 정보 익명화")
    
    class Config:
        schema_extra = {
            "example": {
                "mask_owner_names": True,
                "mask_phone_numbers": True,
                "remove_personal_fields": ["resident_number", "detailed_address"],
                "anonymize_locations": False
            }
        }


class ExportConfig(BaseModel):
    """GPKG 내보내기 설정"""
    output_crs: str = Field(default="EPSG:5186", description="출력 좌표계")
    include_statistics: bool = Field(default=True, description="통계 정보 포함")
    include_metadata: bool = Field(default=True, description="메타데이터 포함")
    privacy_config: PrivacyConfig = Field(default_factory=PrivacyConfig, description="개인정보 보호 설정")
    
    # 레이어 설정
    layers: List[LayerConfig] = Field(default_factory=list, description="포함할 레이어 설정")
    
    # 품질 설정
    max_file_size_mb: float = Field(default=100.0, description="최대 파일 크기 (MB)")
    compression_level: int = Field(default=6, description="압축 레벨 (0-9)")
    
    class Config:
        schema_extra = {
            "example": {
                "output_crs": "EPSG:5186",
                "include_statistics": True,
                "include_metadata": True,
                "privacy_config": {
                    "mask_owner_names": True,
                    "mask_phone_numbers": True
                },
                "layers": [
                    {
                        "name": "parcels",
                        "geometry_type": "Polygon",
                        "fields": {"pnu": "str", "area_sqm": "float"}
                    }
                ],
                "max_file_size_mb": 100.0,
                "compression_level": 6
            }
        }


class ExportRequest(BaseModel):
    """GPKG 내보내기 요청"""
    analysis_ids: List[str] = Field(..., description="포함할 분석 결과 ID 리스트")
    region_name: str = Field(..., description="지역명")
    export_purpose: str = Field(default="행정보고", description="내보내기 목적")
    config: ExportConfig = Field(default_factory=ExportConfig, description="내보내기 설정")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "550e8400-e29b-41d4-a716-446655440001"
                ],
                "region_name": "남원시",
                "export_purpose": "스마트빌리지 사업 현황 보고",
                "config": {
                    "output_crs": "EPSG:5186",
                    "include_statistics": True
                }
            }
        }


class LayerStatistics(BaseModel):
    """레이어 통계"""
    layer_name: str = Field(..., description="레이어 이름")
    feature_count: int = Field(..., description="피처 개수")
    total_area_sqm: float = Field(default=0.0, description="총 면적 (제곱미터)")
    area_by_type: Dict[str, float] = Field(default_factory=dict, description="타입별 면적")
    
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
                }
            }
        }


class ExportMetadata(BaseModel):
    """내보내기 메타데이터"""
    export_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="내보내기 ID")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    created_by: str = Field(default="Nong-View AI System", description="생성자")
    version: str = Field(default="1.0.0", description="버전")
    
    # 소스 정보
    source_images: List[str] = Field(default_factory=list, description="소스 이미지 리스트")
    analysis_date_range: Dict[str, str] = Field(default_factory=dict, description="분석 날짜 범위")
    
    # 처리 정보
    processing_summary: Dict[str, Any] = Field(default_factory=dict, description="처리 요약")
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="품질 지표")
    
    class Config:
        schema_extra = {
            "example": {
                "export_id": "exp_550e8400e29b41d4a716446655440000",
                "created_at": "2025-10-26T15:30:00Z",
                "created_by": "Nong-View AI System",
                "version": "1.0.0",
                "source_images": [
                    "namwon_20250115_ortho.tif",
                    "namwon_20250120_ortho.tif"
                ],
                "analysis_date_range": {
                    "start": "2025-01-15",
                    "end": "2025-01-20"
                },
                "processing_summary": {
                    "total_parcels": 1520,
                    "successful_detections": 1487,
                    "processing_time_minutes": 45.2
                }
            }
        }


class ExportResult(BaseModel):
    """GPKG 내보내기 결과"""
    export_id: str = Field(..., description="내보내기 ID")
    output_path: str = Field(..., description="출력 파일 경로")
    file_size_mb: float = Field(..., description="파일 크기 (MB)")
    
    # 통계 정보
    layer_statistics: List[LayerStatistics] = Field(default_factory=list, description="레이어별 통계")
    metadata: ExportMetadata = Field(..., description="메타데이터")
    
    # 처리 정보
    processing_time: float = Field(..., description="처리 시간 (초)")
    success: bool = Field(default=True, description="성공 여부")
    warnings: List[str] = Field(default_factory=list, description="경고 메시지")
    
    class Config:
        schema_extra = {
            "example": {
                "export_id": "exp_550e8400e29b41d4a716446655440000",
                "output_path": "/exports/namwon_20250126_report.gpkg",
                "file_size_mb": 15.7,
                "layer_statistics": [
                    {
                        "layer_name": "parcels",
                        "feature_count": 1520,
                        "total_area_sqm": 245000.0
                    }
                ],
                "processing_time": 12.5,
                "success": True,
                "warnings": []
            }
        }


class ExportStatus(BaseModel):
    """내보내기 상태"""
    export_id: str = Field(..., description="내보내기 ID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(..., description="상태")
    progress: float = Field(default=0.0, description="진행률 (0.0-1.0)")
    message: str = Field(default="", description="상태 메시지")
    
    started_at: Optional[datetime] = Field(default=None, description="시작 시간")
    completed_at: Optional[datetime] = Field(default=None, description="완료 시간")
    error_message: Optional[str] = Field(default=None, description="에러 메시지")
    
    # 세부 진행 상황
    current_step: str = Field(default="", description="현재 단계")
    total_steps: int = Field(default=1, description="전체 단계 수")
    completed_steps: int = Field(default=0, description="완료된 단계 수")
    
    class Config:
        schema_extra = {
            "example": {
                "export_id": "exp_550e8400e29b41d4a716446655440000",
                "status": "processing",
                "progress": 0.6,
                "message": "레이어 생성 중...",
                "started_at": "2025-10-26T15:30:00Z",
                "current_step": "Creating parcels layer",
                "total_steps": 5,
                "completed_steps": 3
            }
        }