"""
분석 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.common import BaseResponse
from ..schemas.analyses import AnalysisRequest, AnalysisResponse, AnalysisStatusResponse, AnalysisResultResponse
from ..dependencies import require_auth, get_db

router = APIRouter()


@router.post("/", response_model=BaseResponse[AnalysisResponse])
async def create_analysis(
    request: AnalysisRequest,
    current_user = Depends(require_auth),
    db = Depends(get_db)
):
    """분석 작업 생성"""
    # TODO: 구현 예정
    raise HTTPException(501, "구현 예정")