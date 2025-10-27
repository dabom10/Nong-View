"""
API 스키마 모듈 초기화
"""

from .common import BaseResponse, ErrorResponse, PaginationMeta
from .images import *
from .analyses import *
from .crops import *
from .exports import *
from .statistics import *

__all__ = [
    # Common schemas
    'BaseResponse',
    'ErrorResponse', 
    'PaginationMeta',
    
    # Image schemas
    'ImageUploadRequest',
    'ImageUploadResponse',
    'ImageListResponse',
    'ImageDetailResponse',
    
    # Analysis schemas
    'AnalysisRequest',
    'AnalysisResponse',
    'AnalysisStatusResponse',
    'AnalysisResultResponse',
    
    # Crop schemas
    'CropJobRequest',
    'CropJobResponse',
    'CropStatusResponse',
    
    # Export schemas
    'ExportRequest',
    'ExportResponse',
    'ExportStatusResponse',
    
    # Statistics schemas
    'RegionalStatisticsResponse',
    'ParcelStatisticsResponse',
    'TemporalStatisticsResponse'
]