"""
공통 API 스키마 정의
"""

from typing import Any, Dict, List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """기본 API 응답 스키마"""
    success: bool = Field(True, description="요청 성공 여부")
    data: Optional[T] = Field(None, description="응답 데이터")
    message: str = Field("", description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "example"},
                "message": "요청이 성공적으로 처리되었습니다",
                "timestamp": "2025-10-26T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    success: bool = Field(False, description="요청 성공 여부")
    error: Dict[str, Any] = Field(..., description="에러 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "입력 데이터가 유효하지 않습니다",
                    "details": ["필드 'name'은 필수입니다"]
                },
                "timestamp": "2025-10-26T10:30:00Z"
            }
        }


class PaginationMeta(BaseModel):
    """페이지네이션 메타데이터"""
    page: int = Field(..., description="현재 페이지 번호")
    size: int = Field(..., description="페이지 크기")
    total: int = Field(..., description="전체 아이템 수")
    pages: int = Field(..., description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")
    
    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "size": 20,
                "total": 150,
                "pages": 8,
                "has_next": True,
                "has_prev": False
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답 스키마"""
    success: bool = Field(True, description="요청 성공 여부")
    data: List[T] = Field(..., description="응답 데이터 리스트")
    meta: PaginationMeta = Field(..., description="페이지네이션 메타데이터")
    message: str = Field("", description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")


class JobStatus(BaseModel):
    """작업 상태 기본 스키마"""
    job_id: str = Field(..., description="작업 ID")
    status: str = Field(..., description="작업 상태")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="진행률 (0.0-1.0)")
    message: str = Field("", description="상태 메시지")
    started_at: Optional[datetime] = Field(None, description="시작 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    error_message: Optional[str] = Field(None, description="에러 메시지")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": 0.65,
                "message": "이미지 처리 중...",
                "started_at": "2025-10-26T10:30:00Z",
                "completed_at": None,
                "error_message": None
            }
        }


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답"""
    status: str = Field("healthy", description="서비스 상태")
    version: str = Field("1.0.0", description="서비스 버전")
    timestamp: datetime = Field(default_factory=datetime.now, description="체크 시간")
    services: Dict[str, str] = Field(default_factory=dict, description="서비스별 상태")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-10-26T10:30:00Z",
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                    "storage": "healthy"
                }
            }
        }