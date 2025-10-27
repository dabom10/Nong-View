"""
분석 API 스키마
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """분석 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisType(str, Enum):
    """분석 타입"""
    CROP_DETECTION = "crop_detection"
    FACILITY_DETECTION = "facility_detection"
    LAND_USE_CLASSIFICATION = "land_use_classification"
    FULL_ANALYSIS = "full_analysis"


class AnalysisRequest(BaseModel):
    """분석 요청"""
    image_id: str = Field(..., description="분석할 이미지 ID")
    analysis_type: AnalysisType = Field(..., description="분석 타입")
    analysis_name: Optional[str] = Field(None, description="분석 이름")
    description: Optional[str] = Field(None, description="분석 설명")
    
    class Config:
        schema_extra = {
            "example": {
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "analysis_type": "crop_detection",
                "analysis_name": "남원시 작물 탐지",
                "description": "스마트빌리지 사업 지역 작물 탐지 분석"
            }
        }


class AnalysisResponse(BaseModel):
    """분석 응답"""
    analysis_id: str = Field(..., description="분석 ID")
    image_id: str = Field(..., description="이미지 ID")
    analysis_type: AnalysisType = Field(..., description="분석 타입")
    status: AnalysisStatus = Field(..., description="분석 상태")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "analysis_550e8400-e29b-41d4-a716-446655440001",
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "analysis_type": "crop_detection",
                "status": "pending",
                "created_at": "2025-10-26T14:30:00Z"
            }
        }


class AnalysisStatusResponse(BaseModel):
    """분석 상태 응답"""
    analysis_id: str = Field(..., description="분석 ID")
    status: AnalysisStatus = Field(..., description="분석 상태")
    progress: float = Field(0.0, description="진행률")
    message: str = Field("", description="상태 메시지")
    created_at: datetime = Field(..., description="생성 시간")
    started_at: Optional[datetime] = Field(None, description="시작 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "analysis_550e8400-e29b-41d4-a716-446655440001",
                "status": "processing",
                "progress": 0.65,
                "message": "AI 추론 진행 중...",
                "created_at": "2025-10-26T14:30:00Z",
                "started_at": "2025-10-26T14:30:05Z"
            }
        }


class AnalysisResultResponse(BaseModel):
    """분석 결과 응답"""
    analysis_id: str = Field(..., description="분석 ID")
    results: Dict[str, Any] = Field(..., description="분석 결과")
    statistics: Dict[str, Any] = Field(..., description="통계 정보")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "analysis_550e8400-e29b-41d4-a716-446655440001",
                "results": {
                    "detections": [
                        {
                            "class": "crop",
                            "confidence": 0.92,
                            "bbox": [100, 100, 200, 200]
                        }
                    ]
                },
                "statistics": {
                    "total_detections": 150,
                    "average_confidence": 0.87
                }
            }
        }