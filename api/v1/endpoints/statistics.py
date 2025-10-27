"""
통계 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.common import BaseResponse
from ..schemas.statistics import RegionalStatisticsResponse, ParcelStatisticsResponse, TemporalStatisticsResponse
from ..dependencies import require_auth, get_db

router = APIRouter()


@router.get("/regional", response_model=BaseResponse[RegionalStatisticsResponse])
async def get_regional_statistics(
    current_user = Depends(require_auth),
    db = Depends(get_db)
):
    """지역별 통계 조회"""
    # TODO: 구현 예정
    raise HTTPException(501, "구현 예정")