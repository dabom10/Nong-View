"""
POD2 크로핑 관련 스키마 정의
"""

from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ROIBounds(BaseModel):
    """관심영역 경계 좌표"""
    minx: float = Field(..., description="최소 X 좌표")
    miny: float = Field(..., description="최소 Y 좌표")
    maxx: float = Field(..., description="최대 X 좌표")
    maxy: float = Field(..., description="최대 Y 좌표")
    crs: str = Field(default="EPSG:5186", description="좌표계")

    def width(self) -> float:
        """경계의 너비 반환"""
        return self.maxx - self.minx

    def height(self) -> float:
        """경계의 높이 반환"""
        return self.maxy - self.miny

    def area(self) -> float:
        """경계의 면적 반환"""
        return self.width() * self.height()


class CropConfig(BaseModel):
    """크로핑 설정"""
    buffer_distance: float = Field(default=10.0, description="버퍼 거리 (미터)")
    min_area_threshold: float = Field(default=100.0, description="최소 면적 임계값 (제곱미터)")
    use_convex_hull: bool = Field(default=True, description="Convex Hull 사용 여부")
    output_resolution: Optional[float] = Field(default=None, description="출력 해상도 (미터/픽셀)")
    compression: str = Field(default="LZW", description="압축 방식")
    
    class Config:
        schema_extra = {
            "example": {
                "buffer_distance": 10.0,
                "min_area_threshold": 100.0,
                "use_convex_hull": True,
                "output_resolution": 0.25,
                "compression": "LZW"
            }
        }


class GeometryData(BaseModel):
    """지오메트리 데이터"""
    coordinates: List[List[Tuple[float, float]]] = Field(..., description="좌표 리스트")
    geometry_type: str = Field(default="Polygon", description="지오메트리 타입")
    crs: str = Field(default="EPSG:5186", description="좌표계")
    properties: Dict[str, Any] = Field(default_factory=dict, description="속성 정보")


class CropRequest(BaseModel):
    """크로핑 요청"""
    image_id: str = Field(..., description="이미지 ID")
    geometries: List[GeometryData] = Field(..., description="크로핑할 지오메트리 리스트")
    config: CropConfig = Field(default_factory=CropConfig, description="크로핑 설정")
    
    class Config:
        schema_extra = {
            "example": {
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "geometries": [
                    {
                        "coordinates": [[[127.1, 35.8], [127.2, 35.8], [127.2, 35.9], [127.1, 35.9], [127.1, 35.8]]],
                        "geometry_type": "Polygon",
                        "crs": "EPSG:4326",
                        "properties": {"pnu": "4513010100100010000", "land_type": "농지"}
                    }
                ],
                "config": {
                    "buffer_distance": 10.0,
                    "use_convex_hull": True
                }
            }
        }


class CropResult(BaseModel):
    """크로핑 결과"""
    crop_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="크롭 ID")
    image_id: str = Field(..., description="원본 이미지 ID")
    roi_bounds: ROIBounds = Field(..., description="ROI 경계")
    output_path: str = Field(..., description="크롭된 이미지 파일 경로")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    processing_time: float = Field(..., description="처리 시간 (초)")
    
    # 통계 정보
    original_size: Tuple[int, int] = Field(..., description="원본 이미지 크기 (width, height)")
    cropped_size: Tuple[int, int] = Field(..., description="크롭된 이미지 크기 (width, height)")
    pixel_scale: float = Field(..., description="픽셀 스케일 (미터/픽셀)")
    
    class Config:
        schema_extra = {
            "example": {
                "crop_id": "550e8400-e29b-41d4-a716-446655440001",
                "image_id": "550e8400-e29b-41d4-a716-446655440000",
                "roi_bounds": {
                    "minx": 200000.0,
                    "miny": 400000.0,
                    "maxx": 201000.0,
                    "maxy": 401000.0,
                    "crs": "EPSG:5186"
                },
                "output_path": "/data/crops/namwon_20250115_4513010100100010000_crop.tif",
                "processing_time": 1.25,
                "original_size": [10000, 8000],
                "cropped_size": [4000, 4000],
                "pixel_scale": 0.25
            }
        }


class CropStatus(BaseModel):
    """크로핑 상태"""
    crop_id: str = Field(..., description="크롭 ID")
    status: str = Field(..., description="상태 (pending, processing, completed, failed)")
    progress: float = Field(default=0.0, description="진행률 (0.0-1.0)")
    message: str = Field(default="", description="상태 메시지")
    started_at: Optional[datetime] = Field(default=None, description="시작 시간")
    completed_at: Optional[datetime] = Field(default=None, description="완료 시간")
    error_message: Optional[str] = Field(default=None, description="에러 메시지")
    
    class Config:
        schema_extra = {
            "example": {
                "crop_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "completed",
                "progress": 1.0,
                "message": "크로핑이 성공적으로 완료되었습니다",
                "started_at": "2025-10-26T10:30:00Z",
                "completed_at": "2025-10-26T10:31:15Z"
            }
        }