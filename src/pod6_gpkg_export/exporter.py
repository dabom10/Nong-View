"""
POD6: GPKG Export 엔진 구현

분석 결과를 GeoPackage 형식으로 내보내는 핵심 기능
"""

import logging
import time
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
import geopandas as gpd
import pandas as pd
from datetime import datetime
import uuid
import hashlib

from .schemas import (
    ExportConfig, ExportResult, ExportRequest, LayerConfig, 
    LayerStatistics, ExportMetadata, PrivacyConfig
)

logger = logging.getLogger(__name__)


class GPKGExporter:
    """GPKG 내보내기 엔진"""
    
    def __init__(self, output_dir: Path):
        """
        GPKG 내보내기 엔진 초기화
        
        Args:
            output_dir: 출력 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        
    def export(self, request: ExportRequest) -> ExportResult:
        """
        GPKG 내보내기 실행
        
        Args:
            request: 내보내기 요청
            
        Returns:
            내보내기 결과
        """
        start_time = time.time()
        export_id = str(uuid.uuid4())
        
        try:
            self.logger.info(f"GPKG 내보내기 시작: {export_id}")
            
            # 출력 파일 경로 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{request.region_name}_{timestamp}_report.gpkg"
            output_path = self.output_dir / filename
            
            # 분석 데이터 수집
            analysis_data = self._collect_analysis_data(request.analysis_ids)
            
            # 메타데이터 생성
            metadata = self._create_metadata(export_id, request, analysis_data)
            
            # 레이어별 데이터 처리 및 내보내기
            layer_statistics = []
            
            # 기본 레이어들 생성
            if not request.config.layers:
                request.config.layers = self._get_default_layers()
            
            for layer_config in request.config.layers:
                self.logger.info(f"레이어 생성 중: {layer_config.name}")
                
                # 레이어 데이터 준비
                layer_data = self._prepare_layer_data(
                    layer_config, 
                    analysis_data, 
                    request.config
                )
                
                if layer_data is not None and not layer_data.empty:
                    # 개인정보 처리
                    layer_data = self._apply_privacy_protection(
                        layer_data, 
                        request.config.privacy_config
                    )
                    
                    # 좌표계 변환
                    if layer_data.crs != request.config.output_crs:
                        layer_data = layer_data.to_crs(request.config.output_crs)
                    
                    # GPKG에 저장
                    layer_data.to_file(
                        output_path, 
                        layer=layer_config.name, 
                        driver="GPKG"
                    )
                    
                    # 통계 계산
                    stats = self._calculate_layer_statistics(layer_config.name, layer_data)
                    layer_statistics.append(stats)
                    
                    self.logger.info(f"레이어 완료: {layer_config.name} ({len(layer_data)} features)")
            
            # 메타데이터 저장
            if request.config.include_metadata:
                self._save_metadata_to_gpkg(output_path, metadata)
            
            # 통계 레이어 생성
            if request.config.include_statistics:
                self._create_statistics_layer(output_path, layer_statistics)
            
            # 파일 크기 검사
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            if file_size_mb > request.config.max_file_size_mb:
                self.logger.warning(f"파일 크기 초과: {file_size_mb:.1f}MB > {request.config.max_file_size_mb}MB")
            
            processing_time = time.time() - start_time
            
            # 결과 생성
            result = ExportResult(
                export_id=export_id,
                output_path=str(output_path),
                file_size_mb=file_size_mb,
                layer_statistics=layer_statistics,
                metadata=metadata,
                processing_time=processing_time,
                success=True,
                warnings=[]
            )
            
            self.logger.info(f"GPKG 내보내기 완료: {output_path} ({file_size_mb:.1f}MB)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"GPKG 내보내기 실패: {str(e)}")
            raise
    
    def _collect_analysis_data(self, analysis_ids: List[str]) -> Dict[str, Any]:
        """
        분석 데이터 수집
        
        Args:
            analysis_ids: 분석 ID 리스트
            
        Returns:
            수집된 분석 데이터
        """
        # TODO: 실제 분석 결과 데이터베이스에서 데이터 로드
        # 현재는 더미 데이터 생성
        
        dummy_data = {
            'parcels': self._create_dummy_parcels_data(),
            'crop_detections': self._create_dummy_crop_data(),
            'facilities': self._create_dummy_facilities_data(),
            'source_info': {
                'images': ['namwon_20250115_ortho.tif'],
                'analysis_date': datetime.now(),
                'total_area': 245000.0
            }
        }
        
        return dummy_data
    
    def _create_dummy_parcels_data(self) -> gpd.GeoDataFrame:
        """더미 필지 데이터 생성"""
        from shapely.geometry import Polygon
        
        # 더미 필지 데이터
        data = []
        for i in range(100):
            # 간단한 사각형 폴리곤 생성
            x_base = 200000 + (i % 10) * 100
            y_base = 400000 + (i // 10) * 100
            
            polygon = Polygon([
                (x_base, y_base),
                (x_base + 80, y_base),
                (x_base + 80, y_base + 80),
                (x_base, y_base + 80),
                (x_base, y_base)
            ])
            
            data.append({
                'pnu': f'451301010010001{i:04d}',
                'land_type': '농지' if i % 3 == 0 else '시설',
                'area_sqm': polygon.area,
                'owner_name': f'김{i:02d}농',
                'geometry': polygon
            })
        
        return gpd.GeoDataFrame(data, crs='EPSG:5186')
    
    def _create_dummy_crop_data(self) -> gpd.GeoDataFrame:
        """더미 작물 탐지 데이터 생성"""
        from shapely.geometry import Polygon
        
        data = []
        crop_types = ['조사료', '사료작물', '기타작물']
        
        for i in range(150):
            x_base = 200020 + (i % 15) * 60
            y_base = 400020 + (i // 15) * 60
            
            polygon = Polygon([
                (x_base, y_base),
                (x_base + 40, y_base),
                (x_base + 40, y_base + 40),
                (x_base, y_base + 40),
                (x_base, y_base)
            ])
            
            data.append({
                'detection_id': f'det_{i:06d}',
                'crop_type': crop_types[i % len(crop_types)],
                'confidence': 0.85 + (i % 15) * 0.01,
                'area_sqm': polygon.area,
                'detection_date': datetime.now(),
                'geometry': polygon
            })
        
        return gpd.GeoDataFrame(data, crs='EPSG:5186')
    
    def _create_dummy_facilities_data(self) -> gpd.GeoDataFrame:
        """더미 시설물 데이터 생성"""
        from shapely.geometry import Polygon
        
        data = []
        facility_types = ['비닐하우스', '축사', '창고']
        
        for i in range(50):
            x_base = 201000 + (i % 5) * 200
            y_base = 401000 + (i // 5) * 200
            
            polygon = Polygon([
                (x_base, y_base),
                (x_base + 30, y_base),
                (x_base + 30, y_base + 100),
                (x_base, y_base + 100),
                (x_base, y_base)
            ])
            
            data.append({
                'facility_id': f'fac_{i:04d}',
                'facility_type': facility_types[i % len(facility_types)],
                'area_sqm': polygon.area,
                'condition': '양호' if i % 3 == 0 else '보통',
                'geometry': polygon
            })
        
        return gpd.GeoDataFrame(data, crs='EPSG:5186')
    
    def _get_default_layers(self) -> List[LayerConfig]:
        """기본 레이어 설정 반환"""
        return [
            LayerConfig(
                name="parcels",
                geometry_type="Polygon",
                fields={
                    "pnu": "str",
                    "land_type": "str",
                    "area_sqm": "float",
                    "owner_name": "str"
                }
            ),
            LayerConfig(
                name="crop_detections",
                geometry_type="Polygon",
                fields={
                    "detection_id": "str",
                    "crop_type": "str",
                    "confidence": "float",
                    "area_sqm": "float"
                }
            ),
            LayerConfig(
                name="facilities",
                geometry_type="Polygon",
                fields={
                    "facility_id": "str",
                    "facility_type": "str",
                    "area_sqm": "float",
                    "condition": "str"
                }
            )
        ]
    
    def _prepare_layer_data(
        self, 
        layer_config: LayerConfig, 
        analysis_data: Dict[str, Any],
        export_config: ExportConfig
    ) -> Optional[gpd.GeoDataFrame]:
        """
        레이어 데이터 준비
        
        Args:
            layer_config: 레이어 설정
            analysis_data: 분석 데이터
            export_config: 내보내기 설정
            
        Returns:
            준비된 레이어 데이터
        """
        layer_name = layer_config.name
        
        if layer_name not in analysis_data:
            self.logger.warning(f"레이어 데이터 없음: {layer_name}")
            return None
        
        # 원본 데이터 가져오기
        gdf = analysis_data[layer_name].copy()
        
        # 필요한 필드만 선택
        available_fields = list(gdf.columns)
        selected_fields = ['geometry']  # 지오메트리는 항상 포함
        
        for field_name in layer_config.fields.keys():
            if field_name in available_fields:
                selected_fields.append(field_name)
            else:
                self.logger.warning(f"필드 없음: {layer_name}.{field_name}")
        
        # 필드 선택 및 타입 변환
        gdf = gdf[selected_fields].copy()
        
        # 데이터 타입 변환
        for field_name, field_type in layer_config.fields.items():
            if field_name in gdf.columns:
                try:
                    if field_type == 'float':
                        gdf[field_name] = pd.to_numeric(gdf[field_name], errors='coerce')
                    elif field_type == 'int':
                        gdf[field_name] = pd.to_numeric(gdf[field_name], errors='coerce').astype('Int64')
                    elif field_type == 'str':
                        gdf[field_name] = gdf[field_name].astype(str)
                except Exception as e:
                    self.logger.warning(f"타입 변환 실패: {layer_name}.{field_name} -> {field_type}: {e}")
        
        return gdf
    
    def _apply_privacy_protection(
        self, 
        gdf: gpd.GeoDataFrame, 
        privacy_config: PrivacyConfig
    ) -> gpd.GeoDataFrame:
        """
        개인정보 보호 적용
        
        Args:
            gdf: 지오데이터프레임
            privacy_config: 개인정보 보호 설정
            
        Returns:
            개인정보 처리된 데이터프레임
        """
        result = gdf.copy()
        
        # 소유자명 마스킹
        if privacy_config.mask_owner_names and 'owner_name' in result.columns:
            result['owner_name'] = result['owner_name'].apply(
                lambda x: self._mask_name(str(x)) if pd.notna(x) else x
            )
        
        # 전화번호 마스킹
        if privacy_config.mask_phone_numbers and 'phone' in result.columns:
            result['phone'] = result['phone'].apply(
                lambda x: self._mask_phone(str(x)) if pd.notna(x) else x
            )
        
        # 개인정보 필드 제거
        for field in privacy_config.remove_personal_fields:
            if field in result.columns:
                result = result.drop(columns=[field])
                self.logger.info(f"개인정보 필드 제거: {field}")
        
        # 위치 정보 익명화 (필요시)
        if privacy_config.anonymize_locations:
            # TODO: 위치 정보 익명화 구현
            pass
        
        return result
    
    def _mask_name(self, name: str) -> str:
        """이름 마스킹"""
        if len(name) <= 1:
            return name
        return name[0] + '*' * (len(name) - 1)
    
    def _mask_phone(self, phone: str) -> str:
        """전화번호 마스킹"""
        # 숫자만 추출
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) >= 8:
            return digits[:4] + '****' + digits[-4:] if len(digits) >= 8 else digits + '****'
        return '****'
    
    def _calculate_layer_statistics(
        self, 
        layer_name: str, 
        gdf: gpd.GeoDataFrame
    ) -> LayerStatistics:
        """레이어 통계 계산"""
        
        total_area = 0.0
        area_by_type = {}
        
        # 면적 계산
        if 'area_sqm' in gdf.columns:
            total_area = gdf['area_sqm'].sum()
        elif not gdf.empty:
            # 지오메트리에서 면적 계산
            total_area = gdf.geometry.area.sum()
        
        # 타입별 면적 계산
        type_columns = ['crop_type', 'facility_type', 'land_type']
        for col in type_columns:
            if col in gdf.columns:
                if 'area_sqm' in gdf.columns:
                    area_by_type = gdf.groupby(col)['area_sqm'].sum().to_dict()
                else:
                    area_by_type = gdf.groupby(col).geometry.area.sum().to_dict()
                break
        
        return LayerStatistics(
            layer_name=layer_name,
            feature_count=len(gdf),
            total_area_sqm=total_area,
            area_by_type=area_by_type
        )
    
    def _create_metadata(
        self, 
        export_id: str, 
        request: ExportRequest, 
        analysis_data: Dict[str, Any]
    ) -> ExportMetadata:
        """메타데이터 생성"""
        
        source_info = analysis_data.get('source_info', {})
        
        return ExportMetadata(
            export_id=export_id,
            source_images=source_info.get('images', []),
            analysis_date_range={
                'start': source_info.get('analysis_date', datetime.now()).strftime('%Y-%m-%d'),
                'end': source_info.get('analysis_date', datetime.now()).strftime('%Y-%m-%d')
            },
            processing_summary={
                'total_analysis_ids': len(request.analysis_ids),
                'region_name': request.region_name,
                'export_purpose': request.export_purpose,
                'total_area_sqm': source_info.get('total_area', 0.0)
            },
            quality_metrics={
                'data_completeness': 0.95,
                'spatial_accuracy': 0.85,
                'temporal_currency': 1.0
            }
        )
    
    def _save_metadata_to_gpkg(self, gpkg_path: Path, metadata: ExportMetadata):
        """GPKG에 메타데이터 저장"""
        
        # 메타데이터를 테이블로 저장
        metadata_df = pd.DataFrame([{
            'key': k,
            'value': str(v),
            'type': type(v).__name__
        } for k, v in metadata.dict().items()])
        
        # SQLite 연결로 직접 저장
        conn = sqlite3.connect(gpkg_path)
        metadata_df.to_sql('metadata', conn, if_exists='replace', index=False)
        conn.close()
        
        self.logger.info("메타데이터 저장 완료")
    
    def _create_statistics_layer(self, gpkg_path: Path, layer_statistics: List[LayerStatistics]):
        """통계 레이어 생성"""
        
        if not layer_statistics:
            return
        
        # 통계를 데이터프레임으로 변환
        stats_data = []
        for stat in layer_statistics:
            stats_data.append({
                'layer_name': stat.layer_name,
                'feature_count': stat.feature_count,
                'total_area_sqm': stat.total_area_sqm,
                'area_by_type': str(stat.area_by_type)
            })
        
        stats_df = pd.DataFrame(stats_data)
        
        # SQLite 연결로 저장
        conn = sqlite3.connect(gpkg_path)
        stats_df.to_sql('layer_statistics', conn, if_exists='replace', index=False)
        conn.close()
        
        self.logger.info("통계 레이어 생성 완료")