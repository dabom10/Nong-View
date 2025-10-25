"""
이미지 관리 API 엔드포인트
"""

import logging
import uuid
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
import aiofiles
import rasterio
from datetime import datetime

from ..schemas.common import BaseResponse, PaginatedResponse, PaginationMeta
from ..schemas.images import (
    ImageUploadRequest, ImageUploadResponse, ImageListRequest, ImageListResponse,
    ImageDetailResponse, ImageUpdateRequest, ImageDeleteResponse, ImageSummary,
    ImageMetadata, ImageFormat, ImageStatus
)
from ..dependencies import (
    get_db, get_upload_path, get_pagination_params, PaginationParams,
    require_auth, get_logger
)

router = APIRouter()
logger = logging.getLogger(__name__)

# 설정값들
MAX_FILE_SIZE = 1024 * 1024 * 1024 * 2  # 2GB
ALLOWED_EXTENSIONS = ['.tif', '.tiff', '.jp2']


@router.post("/", 
    response_model=BaseResponse[ImageUploadResponse], 
    status_code=status.HTTP_201_CREATED,
    summary="이미지 업로드",
    description="GeoTIFF, TIFF, JP2 형식의 지리공간 이미지를 업로드합니다."
)
async def upload_image(
    file: UploadFile = File(..., description="업로드할 이미지 파일"),
    description: Optional[str] = None,
    region_name: Optional[str] = None,
    drone_model: Optional[str] = None,
    camera_model: Optional[str] = None,
    altitude: Optional[float] = None,
    overlap: Optional[float] = None,
    current_user = Depends(require_auth),
    upload_path: Path = Depends(get_upload_path),
    db = Depends(get_db)
) -> BaseResponse[ImageUploadResponse]:
    """
    이미지 업로드 API
    
    지원 포맷:
    - GeoTIFF (.tif, .tiff)
    - JPEG 2000 (.jp2)
    
    처리 과정:
    1. 파일 검증 (형식, 크기)
    2. 메타데이터 추출
    3. 파일 저장
    4. 데이터베이스 등록
    """
    
    try:
        # 파일 검증
        if not file.filename:
            raise HTTPException(400, "파일명이 필요합니다")
        
        # 확장자 검증
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                400, 
                f"지원되지 않는 파일 형식입니다. 허용된 형식: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 파일 크기 검증 (실제 읽어서 확인)
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024**3)}GB")
        
        # 고유 파일명 생성
        image_id = str(uuid.uuid4())
        safe_filename = f"{image_id}_{file.filename}"
        file_path = upload_path / safe_filename
        
        # 파일 저장
        upload_path.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        logger.info(f"파일 저장 완료: {file_path}")
        
        # 메타데이터 추출
        try:
            metadata = await extract_image_metadata(file_path)
            image_format = detect_image_format(file_path)
        except Exception as e:
            # 메타데이터 추출 실패 시 파일 삭제
            file_path.unlink()
            logger.error(f"메타데이터 추출 실패: {e}")
            raise HTTPException(400, f"이미지 메타데이터 추출에 실패했습니다: {str(e)}")
        
        # TODO: 데이터베이스에 저장
        # 현재는 더미 데이터로 응답
        
        response_data = ImageUploadResponse(
            id=image_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=len(file_content),
            format=image_format,
            status=ImageStatus.READY,
            metadata=metadata,
            uploaded_at=datetime.now()
        )
        
        logger.info(f"이미지 업로드 완료: {image_id}")
        
        return BaseResponse(
            success=True,
            data=response_data,
            message="이미지가 성공적으로 업로드되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 업로드 중 오류 발생: {e}")
        raise HTTPException(500, f"이미지 업로드에 실패했습니다: {str(e)}")


@router.get("/",
    response_model=PaginatedResponse[ImageSummary],
    summary="이미지 목록 조회",
    description="업로드된 이미지 목록을 페이지네이션과 필터링을 통해 조회합니다."
)
async def list_images(
    status_filter: Optional[ImageStatus] = Query(None, alias="status", description="상태 필터"),
    region_name: Optional[str] = Query(None, description="지역명 필터"),
    format_filter: Optional[ImageFormat] = Query(None, alias="format", description="포맷 필터"),
    date_from: Optional[datetime] = Query(None, description="시작 날짜"),
    date_to: Optional[datetime] = Query(None, description="종료 날짜"),
    search: Optional[str] = Query(None, description="검색어 (파일명, 설명)"),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user = Depends(require_auth),
    db = Depends(get_db)
) -> PaginatedResponse[ImageSummary]:
    """
    이미지 목록 조회 API
    
    필터링 옵션:
    - status: 이미지 상태로 필터링
    - region_name: 지역명으로 필터링
    - format: 이미지 포맷으로 필터링
    - date_from/date_to: 업로드 날짜 범위로 필터링
    - search: 파일명이나 설명에서 검색
    
    정렬: 업로드 날짜 내림차순
    """
    
    try:
        # TODO: 실제 데이터베이스 쿼리 구현
        # 현재는 더미 데이터 반환
        
        dummy_images = []
        for i in range(pagination.size):
            if pagination.offset + i >= 25:  # 총 25개 데이터라고 가정
                break
                
            dummy_images.append(ImageSummary(
                id=f"550e8400-e29b-41d4-a716-44665544{i:04d}",
                filename=f"namwon_2025011{i%9+1}_ortho.tif",
                description=f"남원시 스마트빌리지 사업 지역 정사영상 #{i+1}",
                region_name="남원시",
                format=ImageFormat.GEOTIFF,
                status=ImageStatus.READY,
                file_size=157286400 + i * 1000000,
                resolution=0.25,
                area_sqm=6250000.0,
                capture_date=datetime(2025, 1, 15, 10, 30) if i % 2 == 0 else None,
                uploaded_at=datetime(2025, 1, 16, 9, 15),
                tags=["남원시", "스마트빌리지"],
                analysis_count=i % 5
            ))
        
        # 페이지네이션 메타데이터
        total_count = 25
        pages = (total_count + pagination.size - 1) // pagination.size
        
        meta = PaginationMeta(
            page=pagination.page,
            size=pagination.size,
            total=total_count,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1
        )
        
        return PaginatedResponse(
            success=True,
            data=dummy_images,
            meta=meta,
            message=f"{len(dummy_images)}개의 이미지를 조회했습니다"
        )
        
    except Exception as e:
        logger.error(f"이미지 목록 조회 중 오류: {e}")
        raise HTTPException(500, f"이미지 목록 조회에 실패했습니다: {str(e)}")


@router.get("/{image_id}",
    response_model=BaseResponse[ImageDetailResponse],
    summary="이미지 상세 조회",
    description="특정 이미지의 상세 정보를 조회합니다."
)
async def get_image_detail(
    image_id: str,
    current_user = Depends(require_auth),
    db = Depends(get_db)
) -> BaseResponse[ImageDetailResponse]:
    """
    이미지 상세 정보 조회 API
    
    반환 정보:
    - 기본 정보 (파일명, 크기, 상태 등)
    - 메타데이터 (해상도, 좌표계, 경계 등)
    - 촬영 정보 (드론, 카메라, 고도 등)
    - 분석 이력 정보
    """
    
    try:
        # TODO: 실제 데이터베이스에서 조회
        # 현재는 더미 데이터
        
        # 이미지 존재 확인
        if not image_id.startswith("550e8400"):
            raise HTTPException(404, "이미지를 찾을 수 없습니다")
        
        # 더미 메타데이터
        metadata = ImageMetadata(
            width=10000,
            height=8000,
            bands=3,
            dtype="uint8",
            crs="EPSG:5186",
            transform=[0.25, 0.0, 200000.0, 0.0, -0.25, 500000.0],
            bounds={
                "minx": 200000.0,
                "miny": 498000.0,
                "maxx": 202500.0,
                "maxy": 500000.0
            },
            resolution=0.25
        )
        
        detail = ImageDetailResponse(
            id=image_id,
            filename="namwon_20250115_ortho.tif",
            description="남원시 스마트빌리지 사업 지역 정사영상",
            region_name="남원시",
            format=ImageFormat.GEOTIFF,
            status=ImageStatus.READY,
            file_path=f"/data/uploads/{image_id}_namwon_20250115_ortho.tif",
            file_size=157286400,
            metadata=metadata,
            capture_date=datetime(2025, 1, 15, 10, 30),
            drone_model="DJI Matrice 300",
            camera_model="Zenmuse P1",
            altitude=150.0,
            overlap=0.8,
            tags=["남원시", "스마트빌리지"],
            uploaded_at=datetime(2025, 1, 16, 9, 15),
            updated_at=datetime(2025, 1, 16, 9, 15),
            uploaded_by="admin",
            analysis_count=3,
            last_analysis_at=datetime(2025, 1, 20, 14, 30)
        )
        
        return BaseResponse(
            success=True,
            data=detail,
            message="이미지 상세 정보를 조회했습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 상세 조회 중 오류: {e}")
        raise HTTPException(500, f"이미지 상세 조회에 실패했습니다: {str(e)}")


@router.patch("/{image_id}",
    response_model=BaseResponse[ImageDetailResponse],
    summary="이미지 정보 수정",
    description="이미지의 메타 정보(설명, 지역명, 태그)를 수정합니다."
)
async def update_image(
    image_id: str,
    update_data: ImageUpdateRequest,
    current_user = Depends(require_auth),
    db = Depends(get_db)
) -> BaseResponse[ImageDetailResponse]:
    """
    이미지 정보 수정 API
    
    수정 가능한 항목:
    - description: 이미지 설명
    - region_name: 지역명
    - tags: 태그 목록
    """
    
    try:
        # TODO: 실제 데이터베이스 업데이트
        
        # 이미지 존재 확인
        if not image_id.startswith("550e8400"):
            raise HTTPException(404, "이미지를 찾을 수 없습니다")
        
        # 더미 응답 (실제로는 업데이트된 데이터 반환)
        updated_detail = ImageDetailResponse(
            id=image_id,
            filename="namwon_20250115_ortho.tif",
            description=update_data.description or "남원시 스마트빌리지 사업 지역 정사영상",
            region_name=update_data.region_name or "남원시",
            format=ImageFormat.GEOTIFF,
            status=ImageStatus.READY,
            file_path=f"/data/uploads/{image_id}_namwon_20250115_ortho.tif",
            file_size=157286400,
            tags=update_data.tags or ["남원시", "스마트빌리지"],
            uploaded_at=datetime(2025, 1, 16, 9, 15),
            updated_at=datetime.now(),  # 현재 시간으로 업데이트
            analysis_count=3
        )
        
        logger.info(f"이미지 정보 수정 완료: {image_id}")
        
        return BaseResponse(
            success=True,
            data=updated_detail,
            message="이미지 정보가 성공적으로 수정되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 정보 수정 중 오류: {e}")
        raise HTTPException(500, f"이미지 정보 수정에 실패했습니다: {str(e)}")


@router.delete("/{image_id}",
    response_model=BaseResponse[ImageDeleteResponse],
    summary="이미지 삭제",
    description="이미지를 완전히 삭제합니다. 관련된 분석 결과도 함께 삭제됩니다."
)
async def delete_image(
    image_id: str,
    current_user = Depends(require_auth),
    db = Depends(get_db)
) -> BaseResponse[ImageDeleteResponse]:
    """
    이미지 삭제 API
    
    삭제 과정:
    1. 이미지 파일 삭제
    2. 관련 분석 결과 삭제
    3. 데이터베이스 레코드 삭제
    
    주의: 삭제된 데이터는 복구할 수 없습니다.
    """
    
    try:
        # TODO: 실제 삭제 로직 구현
        
        # 이미지 존재 확인
        if not image_id.startswith("550e8400"):
            raise HTTPException(404, "이미지를 찾을 수 없습니다")
        
        # TODO: 
        # 1. 관련 분석 작업 확인 및 중단
        # 2. 분석 결과 파일 삭제
        # 3. 원본 이미지 파일 삭제
        # 4. 데이터베이스 레코드 삭제
        
        logger.info(f"이미지 삭제 완료: {image_id}")
        
        response_data = ImageDeleteResponse(
            deleted_id=image_id,
            message="이미지와 관련된 모든 데이터가 삭제되었습니다"
        )
        
        return BaseResponse(
            success=True,
            data=response_data,
            message="이미지가 성공적으로 삭제되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 삭제 중 오류: {e}")
        raise HTTPException(500, f"이미지 삭제에 실패했습니다: {str(e)}")


@router.get("/{image_id}/download",
    summary="이미지 다운로드",
    description="원본 이미지 파일을 다운로드합니다."
)
async def download_image(
    image_id: str,
    current_user = Depends(require_auth),
    db = Depends(get_db)
) -> FileResponse:
    """
    이미지 다운로드 API
    
    원본 이미지 파일을 다운로드할 수 있습니다.
    """
    
    try:
        # TODO: 실제 파일 경로 조회
        
        # 이미지 존재 확인
        if not image_id.startswith("550e8400"):
            raise HTTPException(404, "이미지를 찾을 수 없습니다")
        
        # TODO: 실제 파일 경로 반환
        file_path = f"/data/uploads/{image_id}_namwon_20250115_ortho.tif"
        
        if not Path(file_path).exists():
            raise HTTPException(404, "이미지 파일을 찾을 수 없습니다")
        
        return FileResponse(
            path=file_path,
            filename="namwon_20250115_ortho.tif",
            media_type="image/tiff"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 다운로드 중 오류: {e}")
        raise HTTPException(500, f"이미지 다운로드에 실패했습니다: {str(e)}")


# 헬퍼 함수들
async def extract_image_metadata(file_path: Path) -> ImageMetadata:
    """이미지 메타데이터 추출"""
    
    try:
        with rasterio.open(file_path) as src:
            # 기본 정보
            width = src.width
            height = src.height
            bands = src.count
            dtype = str(src.dtypes[0])
            crs = str(src.crs) if src.crs else "UNKNOWN"
            transform = list(src.transform)[:6]
            
            # 경계 좌표
            bounds = {
                "minx": src.bounds.left,
                "miny": src.bounds.bottom,
                "maxx": src.bounds.right,
                "maxy": src.bounds.top
            }
            
            # 해상도 (픽셀 크기)
            resolution = abs(src.transform.a)
            
            return ImageMetadata(
                width=width,
                height=height,
                bands=bands,
                dtype=dtype,
                crs=crs,
                transform=transform,
                bounds=bounds,
                resolution=resolution
            )
            
    except Exception as e:
        logger.error(f"메타데이터 추출 오류: {e}")
        raise ValueError(f"메타데이터 추출 실패: {str(e)}")


def detect_image_format(file_path: Path) -> ImageFormat:
    """이미지 포맷 감지"""
    
    suffix = file_path.suffix.lower()
    
    if suffix in ['.tif', '.tiff']:
        # GeoTIFF인지 일반 TIFF인지 확인
        try:
            with rasterio.open(file_path) as src:
                if src.crs is not None:
                    return ImageFormat.GEOTIFF
                else:
                    return ImageFormat.TIFF
        except:
            return ImageFormat.TIFF
    elif suffix == '.jp2':
        return ImageFormat.JP2
    else:
        raise ValueError(f"지원되지 않는 이미지 포맷: {suffix}")