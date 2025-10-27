"""
POD2: 크로핑 엔진 구현

농지 경계 기반 ROI 추출 및 이미지 크로핑 기능
"""

import logging
import time
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_bounds, transform_geom
from rasterio.windows import from_bounds
import geopandas as gpd
from concurrent.futures import ThreadPoolExecutor
import uuid

from .schemas import CropConfig, ROIBounds, CropResult, GeometryData, CropRequest
from ..common.config import settings

logger = logging.getLogger(__name__)


class CroppingEngine:
    """ROI 추출 및 크로핑 엔진"""
    
    def __init__(self, max_workers: int = 4):
        """
        크로핑 엔진 초기화
        
        Args:
            max_workers: 병렬 처리를 위한 최대 워커 수
        """
        self.max_workers = max_workers
        self.logger = logger
        
    def crop_image(
        self,
        image_path: Path,
        geometries: List[GeometryData],
        config: CropConfig,
        output_dir: Path
    ) -> List[CropResult]:
        """
        이미지 크로핑 실행
        
        Args:
            image_path: 입력 이미지 경로
            geometries: 크로핑할 지오메트리 리스트
            config: 크로핑 설정
            output_dir: 출력 디렉토리
            
        Returns:
            크로핑 결과 리스트
        """
        start_time = time.time()
        
        try:
            # 이미지 메타데이터 로드
            with rasterio.open(image_path) as src:
                image_crs = src.crs
                image_bounds = src.bounds
                image_transform = src.transform
                image_size = (src.width, src.height)
                pixel_scale = abs(src.transform.a)  # 픽셀 크기 (미터/픽셀)
            
            self.logger.info(f"이미지 로드 완료: {image_path}")
            self.logger.info(f"이미지 크기: {image_size}, CRS: {image_crs}")
            
            results = []
            
            # 지오메트리별 크로핑 수행
            for i, geometry_data in enumerate(geometries):
                self.logger.info(f"지오메트리 {i+1}/{len(geometries)} 처리 중...")
                
                try:
                    result = self._crop_single_geometry(
                        image_path=image_path,
                        geometry_data=geometry_data,
                        config=config,
                        output_dir=output_dir,
                        image_crs=image_crs,
                        image_size=image_size,
                        pixel_scale=pixel_scale
                    )
                    
                    if result:
                        results.append(result)
                        self.logger.info(f"지오메트리 {i+1} 크로핑 완료: {result.crop_id}")
                    
                except Exception as e:
                    self.logger.error(f"지오메트리 {i+1} 크로핑 실패: {str(e)}")
                    continue
            
            total_time = time.time() - start_time
            self.logger.info(f"전체 크로핑 완료: {len(results)}개 결과, {total_time:.2f}초")
            
            return results
            
        except Exception as e:
            self.logger.error(f"크로핑 엔진 오류: {str(e)}")
            raise
    
    def _crop_single_geometry(
        self,
        image_path: Path,
        geometry_data: GeometryData,
        config: CropConfig,
        output_dir: Path,
        image_crs: str,
        image_size: Tuple[int, int],
        pixel_scale: float
    ) -> Optional[CropResult]:
        """
        단일 지오메트리 크로핑
        
        Args:
            image_path: 이미지 경로
            geometry_data: 지오메트리 데이터
            config: 크로핑 설정
            output_dir: 출력 디렉토리
            image_crs: 이미지 좌표계
            image_size: 이미지 크기
            pixel_scale: 픽셀 스케일
            
        Returns:
            크로핑 결과 또는 None
        """
        start_time = time.time()
        
        try:
            # 지오메트리 생성
            polygon = self._create_polygon_from_coordinates(geometry_data.coordinates)
            
            # 좌표계 변환 (필요한 경우)
            if geometry_data.crs != str(image_crs):
                polygon = self._transform_geometry(polygon, geometry_data.crs, str(image_crs))
            
            # 면적 검사
            if polygon.area < config.min_area_threshold:
                self.logger.warning(f"면적이 임계값보다 작음: {polygon.area:.2f} < {config.min_area_threshold}")
                return None
            
            # Convex Hull 적용 (설정에 따라)
            if config.use_convex_hull:
                polygon = polygon.convex_hull
            
            # 버퍼 적용
            if config.buffer_distance > 0:
                polygon = polygon.buffer(config.buffer_distance)
            
            # ROI 경계 계산
            roi_bounds = ROIBounds(
                minx=polygon.bounds[0],
                miny=polygon.bounds[1],
                maxx=polygon.bounds[2],
                maxy=polygon.bounds[3],
                crs=str(image_crs)
            )
            
            # 출력 파일 경로 생성
            crop_id = str(uuid.uuid4())
            pnu = geometry_data.properties.get('pnu', crop_id[:8])
            output_filename = f"{image_path.stem}_{pnu}_crop.tif"
            output_path = output_dir / output_filename
            
            # 실제 크로핑 수행
            cropped_size = self._perform_cropping(
                image_path=image_path,
                polygon=polygon,
                output_path=output_path,
                config=config
            )
            
            processing_time = time.time() - start_time
            
            # 결과 생성
            result = CropResult(
                crop_id=crop_id,
                image_id=str(image_path.stem),
                roi_bounds=roi_bounds,
                output_path=str(output_path),
                metadata={
                    'source_image': str(image_path),
                    'geometry_properties': geometry_data.properties,
                    'buffer_distance': config.buffer_distance,
                    'use_convex_hull': config.use_convex_hull
                },
                processing_time=processing_time,
                original_size=image_size,
                cropped_size=cropped_size,
                pixel_scale=pixel_scale
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"단일 지오메트리 크로핑 오류: {str(e)}")
            return None
    
    def _create_polygon_from_coordinates(self, coordinates: List[List[Tuple[float, float]]]) -> Polygon:
        """
        좌표에서 Polygon 생성
        
        Args:
            coordinates: 좌표 리스트
            
        Returns:
            Shapely Polygon 객체
        """
        # 외부 링 (첫 번째 좌표 리스트)
        exterior = coordinates[0]
        
        # 내부 홀 (나머지 좌표 리스트들)
        holes = coordinates[1:] if len(coordinates) > 1 else None
        
        return Polygon(exterior, holes)
    
    def _transform_geometry(self, geometry: Polygon, source_crs: str, target_crs: str) -> Polygon:
        """
        지오메트리 좌표계 변환
        
        Args:
            geometry: 변환할 지오메트리
            source_crs: 소스 좌표계
            target_crs: 타겟 좌표계
            
        Returns:
            변환된 지오메트리
        """
        # GeoPandas를 사용한 좌표계 변환
        gdf = gpd.GeoDataFrame([1], geometry=[geometry], crs=source_crs)
        gdf_transformed = gdf.to_crs(target_crs)
        return gdf_transformed.geometry.iloc[0]
    
    def _perform_cropping(
        self,
        image_path: Path,
        polygon: Polygon,
        output_path: Path,
        config: CropConfig
    ) -> Tuple[int, int]:
        """
        실제 이미지 크로핑 수행
        
        Args:
            image_path: 입력 이미지 경로
            polygon: 크로핑할 폴리곤
            output_path: 출력 경로
            config: 크로핑 설정
            
        Returns:
            크롭된 이미지 크기 (width, height)
        """
        with rasterio.open(image_path) as src:
            # 마스크 생성 및 크로핑
            out_image, out_transform = mask(
                src, 
                [polygon], 
                crop=True,
                filled=True,
                pad=False
            )
            
            # 메타데이터 업데이트
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "compress": config.compression
            })
            
            # 해상도 조정 (필요한 경우)
            if config.output_resolution:
                # TODO: 해상도 리샘플링 구현
                pass
            
            # 출력 디렉토리 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 크롭된 이미지 저장
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(out_image)
            
            self.logger.info(f"크롭된 이미지 저장: {output_path}")
            
            return (out_meta["width"], out_meta["height"])
    
    def get_roi_bounds(
        self,
        geometries: List[GeometryData],
        buffer_distance: float = 0.0,
        target_crs: str = "EPSG:5186"
    ) -> ROIBounds:
        """
        지오메트리들의 전체 ROI 경계 계산
        
        Args:
            geometries: 지오메트리 리스트
            buffer_distance: 버퍼 거리
            target_crs: 타겟 좌표계
            
        Returns:
            전체 ROI 경계
        """
        polygons = []
        
        for geometry_data in geometries:
            polygon = self._create_polygon_from_coordinates(geometry_data.coordinates)
            
            # 좌표계 변환
            if geometry_data.crs != target_crs:
                polygon = self._transform_geometry(polygon, geometry_data.crs, target_crs)
            
            polygons.append(polygon)
        
        # 모든 폴리곤 합치기
        union_polygon = unary_union(polygons)
        
        # 버퍼 적용
        if buffer_distance > 0:
            union_polygon = union_polygon.buffer(buffer_distance)
        
        return ROIBounds(
            minx=union_polygon.bounds[0],
            miny=union_polygon.bounds[1],
            maxx=union_polygon.bounds[2],
            maxy=union_polygon.bounds[3],
            crs=target_crs
        )
    
    def validate_geometries(self, geometries: List[GeometryData]) -> List[str]:
        """
        지오메트리 유효성 검사
        
        Args:
            geometries: 검사할 지오메트리 리스트
            
        Returns:
            검증 오류 메시지 리스트
        """
        errors = []
        
        for i, geometry_data in enumerate(geometries):
            try:
                polygon = self._create_polygon_from_coordinates(geometry_data.coordinates)
                
                # 기본 유효성 검사
                if not polygon.is_valid:
                    errors.append(f"지오메트리 {i}: 유효하지 않은 폴리곤")
                
                if polygon.is_empty:
                    errors.append(f"지오메트리 {i}: 빈 폴리곤")
                
                if polygon.area <= 0:
                    errors.append(f"지오메트리 {i}: 면적이 0 이하")
                
                # 좌표 개수 검사
                if len(geometry_data.coordinates[0]) < 4:
                    errors.append(f"지오메트리 {i}: 최소 4개의 좌표 필요")
                
                # 닫힌 링 검사
                first_coord = geometry_data.coordinates[0][0]
                last_coord = geometry_data.coordinates[0][-1]
                if first_coord != last_coord:
                    errors.append(f"지오메트리 {i}: 닫힌 링이 아님")
                
            except Exception as e:
                errors.append(f"지오메트리 {i}: {str(e)}")
        
        return errors