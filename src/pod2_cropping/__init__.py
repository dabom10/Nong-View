"""
POD2: ROI 추출 (크로핑) 모듈

농지 경계에 따른 관심영역(ROI) 추출 및 크로핑 기능을 제공합니다.
"""

from .engine import CroppingEngine
from .schemas import CropConfig, ROIBounds, CropResult

__all__ = ['CroppingEngine', 'CropConfig', 'ROIBounds', 'CropResult']
__version__ = '1.0.0'