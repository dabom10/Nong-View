"""
통계 API 스키마
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RegionalStatisticsResponse(BaseModel):
    """지역별 통계 응답"""
    region_name: str = Field(..., description="지역명")
    total_area_sqm: float = Field(..., description="총 면적 (제곱미터)")
    analysis_count: int = Field(..., description="분석 횟수")
    crop_statistics: Dict[str, float] = Field(..., description="작물별 통계")
    
    class Config:
        schema_extra = {
            "example": {
                "region_name": "남원시",
                "total_area_sqm": 245000.0,
                "analysis_count": 15,
                "crop_statistics": {
                    "조사료": 125000.0,
                    "사료작물": 87000.0
                }
            }
        }


class ParcelStatisticsResponse(BaseModel):
    """필지별 통계 응답"""
    pnu: str = Field(..., description="PNU 코드")
    area_sqm: float = Field(..., description="면적 (제곱미터)")
    crop_type: str = Field(..., description="작물 타입")
    
    class Config:
        schema_extra = {
            "example": {
                "pnu": "4513010100100010000",
                "area_sqm": 1500.0,
                "crop_type": "조사료"
            }
        }


class TemporalStatisticsResponse(BaseModel):
    """시계열 통계 응답"""
    date: datetime = Field(..., description="날짜")
    statistics: Dict[str, float] = Field(..., description="통계 데이터")
    
    class Config:
        schema_extra = {
            "example": {
                "date": "2025-01-15T00:00:00Z",
                "statistics": {
                    "total_area": 245000.0,
                    "crop_area": 200000.0
                }
            }
        }