"""
크로핑 API 엔드포인트
"""

import logging
import uuid
import asyncio
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import FileResponse
from datetime import datetime, timedelta

from ..schemas.common import BaseResponse, PaginatedResponse, JobStatus
from ..schemas.crops import (
    CropJobRequest, CropJobResponse, CropJobStatusResponse, CropJobListResponse,
    CropJobSummary, CropDownloadRequest, CropDownloadResponse, CropValidationRequest,
    CropValidationResponse, CropJobStatus, CropResultSummary, GeometryValidationResult
)
from ..dependencies import (
    get_db, get_cropping_engine, get_crop_path, get_pagination_params, 
    PaginationParams, require_auth
)
from ...src.pod2_cropping import CroppingEngine

router = APIRouter()
logger = logging.getLogger(__name__)

# 작업 상태를 저장할 임시 저장소 (실제로는 Redis나 데이터베이스 사용)
job_status_store = {}


@router.post("/validate",
    response_model=BaseResponse[CropValidationResponse],
    summary="크로핑 사전 검증",
    description="크로핑 작업 전에 지오메트리의 유효성을 검증하고 예상 결과를 제공합니다."
)
async def validate_crop_geometries(
    request: CropValidationRequest,
    current_user = Depends(require_auth),
    cropping_engine: CroppingEngine = Depends(get_cropping_engine),
    db = Depends(get_db)
) -> BaseResponse[CropValidationResponse]:
    """
    크로핑 사전 검증 API
    
    검증 항목:
    - 지오메트리 유효성 (닫힌 링, 면적, 좌표 등)
    - 이미지 경계 내 포함 여부
    - 예상 크롭 크기 및 파일 크기
    - 처리 시간 추정
    """
    
    try:
        # 이미지 존재 확인
        if not request.image_id.startswith("550e8400"):
            raise HTTPException(404, "이미지를 찾을 수 없습니다")
        
        # 지오메트리 검증
        validation_errors = cropping_engine.validate_geometries(request.geometries)
        
        # 각 지오메트리별 검증 결과 생성
        validation_results = []
        valid_count = 0
        
        for i, geometry in enumerate(request.geometries):
            geometry_errors = [error for error in validation_errors if error.startswith(f"지오메트리 {i}:")]
            is_valid = len(geometry_errors) == 0
            
            if is_valid:
                valid_count += 1
            
            # 예상 크롭 크기 계산 (더미 데이터)
            estimated_crop_size = (4000, 4000) if is_valid else None
            estimated_file_size = 25600000 if is_valid else None
            
            validation_results.append(GeometryValidationResult(
                index=i,
                is_valid=is_valid,
                errors=[error.split(": ", 1)[1] for error in geometry_errors],
                warnings=[] if is_valid else [],
                estimated_crop_size=estimated_crop_size,
                estimated_file_size=estimated_file_size
            ))
        
        # 전체 통계 계산
        total_geometries = len(request.geometries)
        invalid_count = total_geometries - valid_count
        estimated_processing_time = valid_count * 2  # 지오메트리당 2초 가정
        estimated_total_file_size = valid_count * 25600000
        
        response_data = CropValidationResponse(
            image_id=request.image_id,
            total_geometries=total_geometries,
            valid_geometries=valid_count,
            invalid_geometries=invalid_count,
            validation_results=validation_results,
            estimated_total_processing_time=estimated_processing_time,
            estimated_total_file_size=estimated_total_file_size
        )
        
        return BaseResponse(
            success=True,
            data=response_data,
            message=f"검증 완료: {valid_count}/{total_geometries}개 지오메트리가 유효합니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"크로핑 검증 중 오류: {e}")
        raise HTTPException(500, f"크로핑 검증에 실패했습니다: {str(e)}")


@router.post("/",
    response_model=BaseResponse[CropJobResponse],
    status_code=status.HTTP_201_CREATED,
    summary="크로핑 작업 생성",
    description="새로운 크로핑 작업을 생성하고 백그라운드에서 처리를 시작합니다."
)
async def create_crop_job(
    request: CropJobRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(require_auth),
    cropping_engine: CroppingEngine = Depends(get_cropping_engine),
    crop_path: Path = Depends(get_crop_path),
    db = Depends(get_db)
) -> BaseResponse[CropJobResponse]:
    """
    크로핑 작업 생성 API
    
    처리 과정:
    1. 입력 검증
    2. 작업 ID 생성
    3. 백그라운드 작업 시작
    4. 작업 정보 반환
    """
    
    try:
        # 이미지 존재 확인
        if not request.image_id.startswith("550e8400"):
            raise HTTPException(404, "이미지를 찾을 수 없습니다")
        
        # 사전 검증
        validation_errors = cropping_engine.validate_geometries(request.geometries)
        if validation_errors:
            raise HTTPException(400, f"지오메트리 검증 실패: {validation_errors}")
        
        # 작업 ID 생성
        job_id = f"crop_{str(uuid.uuid4())}"
        
        # 예상 소요 시간 계산
        estimated_duration = len(request.geometries) * 3  # 지오메트리당 3초 가정
        
        # 작업 상태 초기화
        job_status_store[job_id] = {
            "job_id": job_id,
            "image_id": request.image_id,
            "status": CropJobStatus.PENDING,
            "progress": 0.0,
            "message": "작업 대기 중...",
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "total_geometries": len(request.geometries),
            "processed_geometries": 0,
            "successful_crops": 0,
            "failed_crops": 0,
            "results": [],
            "error_message": None,
            "error_details": None
        }
        
        # 백그라운드 작업 시작
        background_tasks.add_task(
            process_cropping_job,
            job_id,
            request,
            cropping_engine,
            crop_path
        )
        
        response_data = CropJobResponse(
            job_id=job_id,
            image_id=request.image_id,
            status=CropJobStatus.PENDING,
            geometry_count=len(request.geometries),
            estimated_duration=estimated_duration,
            created_at=datetime.now()
        )
        
        logger.info(f"크로핑 작업 생성: {job_id} (지오메트리 {len(request.geometries)}개)")
        
        return BaseResponse(
            success=True,
            data=response_data,
            message="크로핑 작업이 생성되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"크로핑 작업 생성 중 오류: {e}")
        raise HTTPException(500, f"크로핑 작업 생성에 실패했습니다: {str(e)}")


@router.get("/",
    response_model=PaginatedResponse[CropJobSummary],
    summary="크로핑 작업 목록 조회",
    description="크로핑 작업 목록을 필터링과 페이지네이션을 통해 조회합니다."
)
async def list_crop_jobs(
    status_filter: Optional[CropJobStatus] = Query(None, alias="status", description="상태 필터"),
    image_id: Optional[str] = Query(None, description="이미지 ID 필터"),
    date_from: Optional[datetime] = Query(None, description="시작 날짜"),
    date_to: Optional[datetime] = Query(None, description="종료 날짜"),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user = Depends(require_auth),
    db = Depends(get_db)
) -> PaginatedResponse[CropJobSummary]:
    """
    크로핑 작업 목록 조회 API
    
    필터링 옵션:
    - status: 작업 상태로 필터링
    - image_id: 특정 이미지의 작업만 조회
    - date_from/date_to: 날짜 범위로 필터링
    """
    
    try:
        # TODO: 실제 데이터베이스 쿼리 구현
        # 현재는 메모리 저장소와 더미 데이터 사용
        
        dummy_jobs = []
        for i in range(pagination.size):
            if pagination.offset + i >= 10:  # 총 10개 작업이라고 가정
                break
            
            job_id = f"crop_550e8400-e29b-41d4-a716-44665544{i:04d}"
            status_list = [CropJobStatus.COMPLETED, CropJobStatus.PROCESSING, CropJobStatus.FAILED]
            
            dummy_jobs.append(CropJobSummary(
                job_id=job_id,
                job_name=f"크로핑 작업 #{i+1}",
                image_id=f"550e8400-e29b-41d4-a716-446655440000",
                image_filename=f"namwon_2025011{i%9+1}_ortho.tif",
                status=status_list[i % 3],
                progress=1.0 if i % 3 == 0 else 0.7,
                geometry_count=15 + i,
                successful_crops=14 + i if i % 3 == 0 else 10 + i,
                created_at=datetime.now() - timedelta(days=i),
                completed_at=datetime.now() - timedelta(days=i, hours=1) if i % 3 == 0 else None,
                created_by="admin"
            ))
        
        # 페이지네이션 메타데이터
        total_count = 10
        pages = (total_count + pagination.size - 1) // pagination.size
        
        from ..schemas.common import PaginationMeta
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
            data=dummy_jobs,
            meta=meta,
            message=f"{len(dummy_jobs)}개의 크로핑 작업을 조회했습니다"
        )
        
    except Exception as e:
        logger.error(f"크로핑 작업 목록 조회 중 오류: {e}")
        raise HTTPException(500, f"크로핑 작업 목록 조회에 실패했습니다: {str(e)}")


@router.get("/{job_id}",
    response_model=BaseResponse[CropJobStatusResponse],
    summary="크로핑 작업 상태 조회",
    description="특정 크로핑 작업의 상세 상태를 조회합니다."
)
async def get_crop_job_status(
    job_id: str,
    current_user = Depends(require_auth),
    db = Depends(get_db)
) -> BaseResponse[CropJobStatusResponse]:
    """
    크로핑 작업 상태 조회 API
    
    반환 정보:
    - 작업 진행 상황
    - 처리 통계
    - 결과 요약 (완료 시)
    - 에러 정보 (실패 시)
    """
    
    try:
        # 작업 상태 조회
        if job_id in job_status_store:
            job_data = job_status_store[job_id]
            
            response_data = CropJobStatusResponse(
                job_id=job_data["job_id"],
                image_id=job_data["image_id"],
                status=job_data["status"],
                progress=job_data["progress"],
                message=job_data["message"],
                created_at=job_data["created_at"],
                started_at=job_data["started_at"],
                completed_at=job_data["completed_at"],
                total_geometries=job_data["total_geometries"],
                processed_geometries=job_data["processed_geometries"],
                successful_crops=job_data["successful_crops"],
                failed_crops=job_data["failed_crops"],
                results=job_data["results"],
                total_processing_time=job_data.get("total_processing_time"),
                error_message=job_data["error_message"],
                error_details=job_data["error_details"]
            )
        else:
            # 더미 데이터 (작업을 찾을 수 없는 경우)
            if not job_id.startswith("crop_"):
                raise HTTPException(404, "크로핑 작업을 찾을 수 없습니다")
            
            response_data = CropJobStatusResponse(
                job_id=job_id,
                image_id="550e8400-e29b-41d4-a716-446655440000",
                status=CropJobStatus.COMPLETED,
                progress=1.0,
                message="크로핑 작업이 완료되었습니다",
                created_at=datetime.now() - timedelta(hours=1),
                started_at=datetime.now() - timedelta(minutes=59),
                completed_at=datetime.now() - timedelta(minutes=55),
                total_geometries=15,
                processed_geometries=15,
                successful_crops=14,
                failed_crops=1,
                results=[
                    CropResultSummary(
                        crop_id=f"crop_{job_id}_{i:03d}",
                        geometry_index=i,
                        roi_bounds={
                            "minx": 200000.0 + i * 100,
                            "miny": 400000.0 + i * 100,
                            "maxx": 201000.0 + i * 100,
                            "maxy": 401000.0 + i * 100,
                            "crs": "EPSG:5186"
                        },
                        output_filename=f"crop_{i:03d}.tif",
                        file_size=25600000,
                        cropped_size=(4000, 4000),
                        processing_time=1.25
                    ) for i in range(14)  # 성공한 크롭만
                ],
                total_processing_time=245.0
            )
        
        return BaseResponse(
            success=True,
            data=response_data,
            message="크로핑 작업 상태를 조회했습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"크로핑 작업 상태 조회 중 오류: {e}")
        raise HTTPException(500, f"크로핑 작업 상태 조회에 실패했습니다: {str(e)}")


@router.delete("/{job_id}",
    response_model=BaseResponse[dict],
    summary="크로핑 작업 취소",
    description="진행 중인 크로핑 작업을 취소하고 관련 파일을 정리합니다."
)
async def cancel_crop_job(
    job_id: str,
    current_user = Depends(require_auth),
    db = Depends(get_db)
) -> BaseResponse[dict]:
    """
    크로핑 작업 취소 API
    
    취소 과정:
    1. 작업 상태 확인
    2. 진행 중인 처리 중단
    3. 임시 파일 정리
    4. 상태 업데이트
    """
    
    try:
        # 작업 존재 확인
        if job_id not in job_status_store:
            if not job_id.startswith("crop_"):
                raise HTTPException(404, "크로핑 작업을 찾을 수 없습니다")
        
        # 작업 상태 확인
        if job_id in job_status_store:
            job_data = job_status_store[job_id]
            
            if job_data["status"] in [CropJobStatus.COMPLETED, CropJobStatus.FAILED]:
                raise HTTPException(400, "이미 완료되거나 실패한 작업은 취소할 수 없습니다")
            
            if job_data["status"] == CropJobStatus.CANCELLED:
                raise HTTPException(400, "이미 취소된 작업입니다")
            
            # 작업 취소
            job_data["status"] = CropJobStatus.CANCELLED
            job_data["message"] = "작업이 취소되었습니다"
            job_data["completed_at"] = datetime.now()
        
        # TODO: 실제 작업 중단 로직 구현
        # - 진행 중인 백그라운드 작업 중단
        # - 임시 파일 정리
        
        logger.info(f"크로핑 작업 취소: {job_id}")
        
        return BaseResponse(
            success=True,
            data={"cancelled_job_id": job_id},
            message="크로핑 작업이 취소되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"크로핑 작업 취소 중 오류: {e}")
        raise HTTPException(500, f"크로핑 작업 취소에 실패했습니다: {str(e)}")


@router.post("/{job_id}/download",
    response_model=BaseResponse[CropDownloadResponse],
    summary="크롭 결과 다운로드 준비",
    description="완료된 크로핑 작업의 결과를 다운로드할 수 있는 URL을 생성합니다."
)
async def prepare_crop_download(
    job_id: str,
    request: CropDownloadRequest,
    current_user = Depends(require_auth),
    db = Depends(get_db)
) -> BaseResponse[CropDownloadResponse]:
    """
    크롭 결과 다운로드 준비 API
    
    기능:
    - 선택한 크롭 결과를 압축
    - 임시 다운로드 URL 생성
    - 만료 시간 설정
    """
    
    try:
        # 작업 존재 및 완료 상태 확인
        if job_id not in job_status_store:
            if not job_id.startswith("crop_"):
                raise HTTPException(404, "크로핑 작업을 찾을 수 없습니다")
        
        # TODO: 실제 압축 파일 생성 로직
        # 현재는 더미 응답
        
        download_id = f"dl_{str(uuid.uuid4())}"
        download_url = f"/api/v1/crops/download/{download_id}"
        
        response_data = CropDownloadResponse(
            download_id=download_id,
            download_url=download_url,
            file_size=127834560,  # 약 122MB
            expires_at=datetime.now() + timedelta(hours=12),
            crop_count=len(request.crop_ids) if request.crop_ids else 14
        )
        
        return BaseResponse(
            success=True,
            data=response_data,
            message="다운로드 준비가 완료되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"크롭 다운로드 준비 중 오류: {e}")
        raise HTTPException(500, f"크롭 다운로드 준비에 실패했습니다: {str(e)}")


@router.get("/download/{download_id}",
    summary="크롭 결과 파일 다운로드",
    description="준비된 크롭 결과 압축 파일을 다운로드합니다."
)
async def download_crop_results(
    download_id: str,
    current_user = Depends(require_auth)
) -> FileResponse:
    """
    크롭 결과 파일 다운로드 API
    """
    
    try:
        # TODO: 실제 파일 다운로드 로직
        
        if not download_id.startswith("dl_"):
            raise HTTPException(404, "다운로드 링크를 찾을 수 없습니다")
        
        # 더미 파일 경로 (실제로는 압축된 파일 경로)
        file_path = "/tmp/crop_results.zip"
        
        # 파일 존재 확인 (실제 구현에서는 필요)
        # if not Path(file_path).exists():
        #     raise HTTPException(404, "다운로드 파일을 찾을 수 없습니다")
        
        return FileResponse(
            path=file_path,
            filename=f"crop_results_{download_id[:8]}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"크롭 결과 다운로드 중 오류: {e}")
        raise HTTPException(500, f"크롭 결과 다운로드에 실패했습니다: {str(e)}")


# 백그라운드 작업 함수
async def process_cropping_job(
    job_id: str,
    request: CropJobRequest,
    cropping_engine: CroppingEngine,
    crop_path: Path
):
    """
    크로핑 백그라운드 작업 처리
    """
    
    try:
        # 작업 시작
        job_status_store[job_id]["status"] = CropJobStatus.PROCESSING
        job_status_store[job_id]["started_at"] = datetime.now()
        job_status_store[job_id]["message"] = "크로핑 처리 시작..."
        
        logger.info(f"크로핑 작업 시작: {job_id}")
        
        # TODO: 실제 크로핑 엔진 호출
        # 현재는 시뮬레이션
        
        total_geometries = len(request.geometries)
        results = []
        successful_crops = 0
        failed_crops = 0
        
        for i, geometry in enumerate(request.geometries):
            # 진행률 업데이트
            progress = (i + 1) / total_geometries
            job_status_store[job_id]["progress"] = progress
            job_status_store[job_id]["message"] = f"지오메트리 {i+1}/{total_geometries} 처리 중..."
            job_status_store[job_id]["processed_geometries"] = i + 1
            
            # 처리 시뮬레이션 (실제로는 cropping_engine.crop_image 호출)
            await asyncio.sleep(1)  # 1초 처리 시간 시뮬레이션
            
            # 90% 확률로 성공
            import random
            if random.random() < 0.9:
                # 성공
                successful_crops += 1
                results.append(CropResultSummary(
                    crop_id=f"crop_{job_id}_{i:03d}",
                    geometry_index=i,
                    roi_bounds={
                        "minx": 200000.0 + i * 100,
                        "miny": 400000.0 + i * 100,
                        "maxx": 201000.0 + i * 100,
                        "maxy": 401000.0 + i * 100,
                        "crs": "EPSG:5186"
                    },
                    output_filename=f"crop_{i:03d}.tif",
                    file_size=25600000,
                    cropped_size=(4000, 4000),
                    processing_time=1.0
                ))
            else:
                # 실패
                failed_crops += 1
        
        # 작업 완료
        job_status_store[job_id]["status"] = CropJobStatus.COMPLETED
        job_status_store[job_id]["progress"] = 1.0
        job_status_store[job_id]["message"] = "크로핑 작업이 완료되었습니다"
        job_status_store[job_id]["completed_at"] = datetime.now()
        job_status_store[job_id]["successful_crops"] = successful_crops
        job_status_store[job_id]["failed_crops"] = failed_crops
        job_status_store[job_id]["results"] = results
        job_status_store[job_id]["total_processing_time"] = total_geometries * 1.0
        
        logger.info(f"크로핑 작업 완료: {job_id} (성공: {successful_crops}, 실패: {failed_crops})")
        
    except Exception as e:
        # 작업 실패
        job_status_store[job_id]["status"] = CropJobStatus.FAILED
        job_status_store[job_id]["message"] = "크로핑 작업이 실패했습니다"
        job_status_store[job_id]["completed_at"] = datetime.now()
        job_status_store[job_id]["error_message"] = str(e)
        
        logger.error(f"크로핑 작업 실패: {job_id} - {e}")