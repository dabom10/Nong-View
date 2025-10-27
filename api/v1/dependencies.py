"""
API 의존성 주입 모듈

FastAPI 의존성 주입을 통한 공통 서비스 제공
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# 데이터베이스 의존성 (추후 구현)
async def get_db():
    """
    데이터베이스 세션 의존성
    
    TODO: SQLAlchemy 세션 구현
    """
    # 현재는 더미 구현
    try:
        db = {"connection": "dummy"}
        yield db
    finally:
        # 연결 정리
        pass


# 인증 의존성 (추후 구현)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    현재 사용자 정보 의존성
    
    Args:
        authorization: Authorization 헤더
        
    Returns:
        사용자 정보
    """
    # 현재는 더미 구현
    if authorization:
        # TODO: JWT 토큰 검증 구현
        return {"user_id": "admin", "username": "admin"}
    
    # 인증이 필요한 엔드포인트에서만 예외 발생
    return None


async def require_auth(current_user = Depends(get_current_user)):
    """
    인증 필수 의존성
    
    Args:
        current_user: 현재 사용자
        
    Returns:
        인증된 사용자 정보
        
    Raises:
        HTTPException: 인증 실패시
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


# 파일 저장 경로 의존성
def get_upload_path() -> Path:
    """
    업로드 파일 저장 경로 반환
    
    Returns:
        업로드 경로
    """
    upload_path = Path("data/uploads")
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def get_crop_path() -> Path:
    """
    크롭 파일 저장 경로 반환
    
    Returns:
        크롭 경로
    """
    crop_path = Path("data/crops")
    crop_path.mkdir(parents=True, exist_ok=True)
    return crop_path


def get_export_path() -> Path:
    """
    내보내기 파일 저장 경로 반환
    
    Returns:
        내보내기 경로
    """
    export_path = Path("data/exports")
    export_path.mkdir(parents=True, exist_ok=True)
    return export_path


# 서비스 의존성들
def get_cropping_engine():
    """크로핑 엔진 의존성"""
    from ...src.pod2_cropping import CroppingEngine
    return CroppingEngine()


def get_tiling_engine():
    """타일링 엔진 의존성"""
    from ...src.pod3_tiling import TilingEngine
    return TilingEngine()


def get_inference_engine():
    """추론 엔진 의존성"""
    from ...src.pod4_ai_inference import InferenceEngine
    return InferenceEngine()


def get_merge_engine():
    """병합 엔진 의존성"""
    from ...src.pod5_merging import MergeEngine
    return MergeEngine()


def get_gpkg_exporter():
    """GPKG 내보내기 엔진 의존성"""
    from ...src.pod6_gpkg_export import GPKGExporter
    export_path = get_export_path()
    return GPKGExporter(export_path)


# 페이지네이션 의존성
class PaginationParams:
    """페이지네이션 파라미터"""
    
    def __init__(
        self,
        page: int = 1,
        size: int = 20,
        max_size: int = 100
    ):
        if page < 1:
            page = 1
        if size < 1:
            size = 20
        if size > max_size:
            size = max_size
            
        self.page = page
        self.size = size
        self.offset = (page - 1) * size


def get_pagination_params(
    page: int = 1,
    size: int = 20
) -> PaginationParams:
    """
    페이지네이션 파라미터 의존성
    
    Args:
        page: 페이지 번호 (1부터 시작)
        size: 페이지 크기
        
    Returns:
        페이지네이션 파라미터
    """
    return PaginationParams(page=page, size=size)


# 로깅 의존성
def get_logger(name: str = __name__):
    """
    로거 의존성
    
    Args:
        name: 로거 이름
        
    Returns:
        로거 인스턴스
    """
    return logging.getLogger(name)