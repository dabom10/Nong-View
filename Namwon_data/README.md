# Training Production - 학습 모델 정리

YOLOv11 Segmentation 모델 학습 스크립트 및 학습 완료 모델 정리 폴더

## 📁 폴더 구조

```
training_production/
├── scripts/
│   ├── training/              # 학습 스크립트
│   │   ├── train-upgrade.py   # TIF 이미지 학습 (MBP 자동 최적화 + CLI)
│   │   ├── train_class_models.py  # 클래스별 모델 학습
│   │   └── train.py           # 가장자리 최적화 학습
│   ├── preprocessing/         # 전처리 스크립트
│   │   ├── convert_geojson_to_yolo.py
│   │   ├── create_class_specific_datasets.py
│   │   ├── create_unified_dataset.py
│   │   └── prepare_tif_dataset.py
│   └── inference/             # 추론 스크립트
│       ├── upgrade_inf.py     # 고급 추론 (대규모 TIFF)
│       ├── inf.py             # 가장자리 검출 개선 추론
│       └── large_scale_crop_inference.py
├── models/                    # 학습 완료 모델
│   ├── greenhouse_multi/      # 비닐하우스_다동 모델
│   │   ├── weights/
│   │   │   └── best.pt        # 최고 성능 모델 가중치
│   │   ├── graphs/
│   │   │   ├── *.png          # 학습 그래프
│   │   │   └── training_curves.png  # 학습 곡선
│   │   └── results.csv        # 학습 로그
│   ├── greenhouse_single/     # 비닐하우스_단동 모델
│   ├── growth_tif/            # TIF 사료작물 모델
│   └── performance_comparison.png  # 모델 성능 비교 차트
├── dataset_greenhouse_multi/  # 비닐하우스 다동 데이터셋
├── dataset_greenhouse_single/ # 비닐하우스 단동 데이터셋
├── growth_tif_dataset/        # TIF 사료작물 데이터셋
├── create_performance_comparison.py  # 성능 시각화 스크립트
├── requirements.txt           # Python 의존성
└── README.md                  # 이 문서
```

## 🎯 학습 완료 모델 성능

| 모델명 | Precision | Recall | F1-Score | mAP50 | mAP50-95 | 에폭 |
|--------|-----------|--------|----------|-------|----------|------|
| **비닐하우스_다동** | **0.953** | **0.893** | **0.922** | **0.970** | **0.846** | 100 |
| **비닐하우스_단동** | **0.888** | **0.855** | **0.871** | **0.912** | **0.808** | 100 |
| **TIF_사료작물** | **0.649** | **0.620** | **0.634** | **0.628** | **0.514** | 100 |

> 📊 상세 성능 비교는 `models/performance_comparison.png` 참조
> 
> 📈 각 모델의 학습 곡선은 `models/{모델명}/graphs/training_curves.png` 참조

## 🚀 학습 스크립트 사용법

### 1. train-upgrade.py (권장 ⭐)
**TIF 이미지 직접 학습 + MBP 자동 최적화 + CLI 지원**

#### 주요 특징:
- ✅ CLI 인자로 데이터셋 선택 가능
- ✅ MBP (Micro-Batch Processing) 자동 최적화
- ✅ 배치 크기 자동 튜닝 (네트워크 핑처럼 최적값 탐색)
- ✅ TIF 4채널 → 3채널 자동 변환
- ✅ VRAM 사용량 85% 안전 마진

#### 사용 예시:

```bash
# 기본 사용법 (자동 튜닝 활성화)
python scripts/training/train-upgrade.py --dataset dataset_greenhouse_multi --epochs 100

# 이미지 크기 지정
python scripts/training/train-upgrade.py --dataset growth_tif_dataset --imgsz 1024

# 경량 모델 사용
python scripts/training/train-upgrade.py --dataset dataset_greenhouse_single --model yolo11n-seg.pt --epochs 50

# 자동 튜닝 비활성화
python scripts/training/train-upgrade.py --dataset growth_tif_dataset --no-auto-tune

# 프로젝트 이름 지정
python scripts/training/train-upgrade.py --dataset dataset_greenhouse_multi --project my_greenhouse_training
```

#### CLI 인자 설명:

| 인자 | 설명 | 기본값 | 예시 |
|------|------|--------|------|
| `--dataset` | 데이터셋 폴더 경로 (필수) | - | `dataset_greenhouse_multi` |
| `--epochs` | 학습 에폭 수 | 100 | `--epochs 50` |
| `--imgsz` | 이미지 크기 | 1024 | `--imgsz 640` |
| `--model` | YOLO 모델 파일 | `yolo11x-seg.pt` | `--model yolo11n-seg.pt` |
| `--project` | 프로젝트 이름 | `{dataset}_training` | `--project my_project` |
| `--device` | 디바이스 (cuda/cpu) | `cuda` | `--device cpu` |
| `--auto-tune` | 배치 크기 자동 튜닝 활성화 | True | `--auto-tune` |
| `--no-auto-tune` | 배치 크기 자동 튜닝 비활성화 | - | `--no-auto-tune` |

#### 도움말:
```bash
python scripts/training/train-upgrade.py --help
```

### 2. train_class_models.py
**클래스별 모델 학습 (비닐하우스 단동/다동, 곤포사일리지)**

```bash
python scripts/training/train_class_models.py
```

### 3. train.py
**가장자리 최적화 YOLO 세그멘테이션 학습**

```bash
python scripts/training/train.py
```

## 📊 성능 시각화

학습 완료 후 성능 비교 차트를 생성하려면:

```bash
python create_performance_comparison.py
```

생성되는 파일:
- `models/performance_comparison.png` - 전체 모델 성능 비교
- `models/{모델명}/graphs/training_curves.png` - 각 모델의 학습 곡선

## 🔍 추론 스크립트 사용법

### 1. upgrade_inf.py (대규모 TIFF 추론)
```bash
python scripts/inference/upgrade_inf.py
```

### 2. large_scale_crop_inference.py
```bash
python scripts/inference/large_scale_crop_inference.py
```

## 📦 데이터셋 구조

각 데이터셋 폴더는 다음 구조를 따릅니다:

```
dataset_*/
├── dataset.yaml          # YOLO 데이터셋 설정
├── images/
│   ├── train/           # 학습 이미지
│   ├── val/             # 검증 이미지
│   └── test/            # 테스트 이미지
└── labels/
    ├── train/           # 학습 레이블
    ├── val/             # 검증 레이블
    └── test/            # 테스트 레이블
```

## 🛠️ 설치 및 환경 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 필요한 패키지
- ultralytics (YOLOv11)
- torch (PyTorch)
- opencv-python
- numpy
- pandas
- matplotlib
- pillow
- pyyaml
- rasterio (TIF 파일 처리)
- geopandas (공간 데이터 처리)

### 3. GPU 요구사항
- **권장:** NVIDIA RTX A6000 (48GB VRAM)
- **최소:** NVIDIA GPU with 8GB+ VRAM
- CUDA 11.8 이상

## 💡 학습 팁

### 1. 메모리 부족 시
```bash
# 경량 모델 사용
python scripts/training/train-upgrade.py --dataset dataset_* --model yolo11n-seg.pt

# 이미지 크기 줄이기
python scripts/training/train-upgrade.py --dataset dataset_* --imgsz 640

# 자동 튜닝 비활성화 (수동 배치 설정)
python scripts/training/train-upgrade.py --dataset dataset_* --no-auto-tune
```

### 2. 빠른 테스트
```bash
# 적은 에폭으로 테스트
python scripts/training/train-upgrade.py --dataset dataset_* --epochs 10
```

### 3. TIF 파일 처리
- TIF 4채널 이미지는 자동으로 3채널로 변환됩니다
- 첫 실행 시 변환 작업이 수행되며, 이후에는 건너뜁니다

## 📈 학습 모니터링

학습 중 생성되는 파일:
```
{project_name}/
├── run_YYYYMMDD_HHMMSS/
│   ├── weights/
│   │   ├── best.pt          # 최고 성능 모델
│   │   ├── last.pt          # 마지막 에폭 모델
│   │   └── epoch*.pt        # 각 에폭별 체크포인트
│   ├── results.csv          # 학습 로그 (CSV)
│   ├── confusion_matrix.png # 혼동 행렬
│   ├── results.png          # 결과 그래프
│   └── *.png                # 기타 시각화
```

## 🎓 모델 선택 가이드

| 모델 | 크기 | 속도 | 정확도 | 용도 |
|------|------|------|--------|------|
| yolo11n-seg.pt | 소형 | 빠름 | 보통 | 테스트, 엣지 디바이스 |
| yolo11s-seg.pt | 소형 | 빠름 | 보통 | 경량화 |
| yolo11m-seg.pt | 중형 | 중간 | 좋음 | 균형 |
| yolo11l-seg.pt | 대형 | 느림 | 우수 | 고성능 |
| **yolo11x-seg.pt** | 초대형 | 매우 느림 | **최고** | **최고 정확도 필요 시** |

## 🔧 문제 해결

### CUDA Out of Memory
```bash
# 1. 경량 모델 사용
--model yolo11n-seg.pt

# 2. 이미지 크기 줄이기
--imgsz 640

# 3. 자동 튜닝 활성화 (기본값)
--auto-tune
```

### TIF 파일 읽기 오류
```bash
# OpenCV 픽셀 제한이 자동으로 해제됩니다
# 스크립트에서 처리하므로 추가 조치 불필요
```

### 한글 경로 문제
```bash
# 영문 경로 사용 권장
# 또는 상대 경로 사용
```

## 📝 라이선스 및 참고

- **YOLOv11:** Ultralytics (AGPL-3.0)
- **PyTorch:** BSD-style license
- **프로젝트:** 남원 스마트빌리지 AI 모델 개발

## 🤝 기여 및 문의

- 학습 스크립트 개선 제안
- 버그 리포트
- 새로운 기능 요청

---

**Last Updated:** 2025-10-28
**Version:** 1.0.0

