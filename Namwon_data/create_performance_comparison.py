#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
학습 모델 성능 비교 시각화 스크립트
CSV 파일에서 성능 지표를 추출하여 비교 그래프 생성
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
import numpy as np

# 한글 폰트 설정 (Windows)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


def extract_final_metrics(csv_path):
    """
    CSV 파일에서 최종 에폭의 성능 지표 추출
    """
    df = pd.read_csv(csv_path)
    last_row = df.iloc[-1]
    
    # F1 Score 계산: F1 = 2 * (Precision * Recall) / (Precision + Recall)
    precision_m = last_row['metrics/precision(M)']
    recall_m = last_row['metrics/recall(M)']
    f1_score = 2 * (precision_m * recall_m) / (precision_m + recall_m) if (precision_m + recall_m) > 0 else 0
    
    metrics = {
        'Precision': precision_m,
        'Recall': recall_m,
        'F1-Score': f1_score,
        'mAP50': last_row['metrics/mAP50(M)'],
        'mAP50-95': last_row['metrics/mAP50-95(M)'],
        'Final Epoch': int(last_row['epoch'])
    }
    
    return metrics


def create_comparison_chart():
    """
    3개 모델의 성능 비교 차트 생성
    """
    # 모델 경로 정의
    models = {
        '비닐하우스_다동': 'models/greenhouse_multi/results.csv',
        '비닐하우스_단동': 'models/greenhouse_single/results.csv',
        'TIF_사료작물': 'models/growth_tif/results.csv'
    }
    
    # 성능 지표 추출
    all_metrics = {}
    for model_name, csv_path in models.items():
        csv_full_path = Path(csv_path)
        if csv_full_path.exists():
            all_metrics[model_name] = extract_final_metrics(csv_full_path)
            print(f"✓ {model_name} 성능 지표 추출 완료")
        else:
            print(f"✗ {model_name} CSV 파일 없음: {csv_path}")
    
    if not all_metrics:
        print("❌ 성능 지표를 추출할 수 없습니다.")
        return
    
    # 차트 생성
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('학습 모델 성능 비교', fontsize=20, fontweight='bold', y=0.98)
    
    metrics_to_plot = ['Precision', 'Recall', 'F1-Score', 'mAP50', 'mAP50-95']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    model_names = list(all_metrics.keys())
    x = np.arange(len(model_names))
    width = 0.6
    
    # 각 지표별 막대 그래프
    for idx, metric in enumerate(metrics_to_plot):
        ax = axes[idx // 3, idx % 3]
        values = [all_metrics[model][metric] for model in model_names]
        
        bars = ax.bar(x, values, width, color=colors[idx], alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # 값 레이블 추가
        for i, (bar, value) in enumerate(zip(bars, values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.3f}',
                   ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_ylabel(metric, fontsize=13, fontweight='bold')
        ax.set_title(f'{metric} 비교', fontsize=14, fontweight='bold', pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(model_names, fontsize=11)
        ax.set_ylim(0, 1.1)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    # 마지막 빈 subplot에 전체 요약 테이블
    ax = axes[1, 2]
    ax.axis('off')
    
    # 요약 테이블 데이터 준비
    table_data = []
    headers = ['모델명', 'Precision', 'Recall', 'F1', 'mAP50', 'mAP50-95']
    
    for model_name in model_names:
        metrics = all_metrics[model_name]
        row = [
            model_name,
            f"{metrics['Precision']:.3f}",
            f"{metrics['Recall']:.3f}",
            f"{metrics['F1-Score']:.3f}",
            f"{metrics['mAP50']:.3f}",
            f"{metrics['mAP50-95']:.3f}"
        ]
        table_data.append(row)
    
    # 테이블 생성
    table = ax.table(cellText=table_data, colLabels=headers,
                    cellLoc='center', loc='center',
                    colWidths=[0.25, 0.15, 0.15, 0.15, 0.15, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)
    
    # 헤더 스타일
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4ECDC4')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # 데이터 행 스타일
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#F0F0F0')
    
    ax.set_title('성능 요약 테이블', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # 저장
    output_path = Path('models/performance_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ 성능 비교 차트 저장: {output_path}")
    
    plt.close()


def create_individual_model_charts():
    """
    각 모델별 학습 곡선 차트 생성
    """
    models = {
        '비닐하우스_다동': 'models/greenhouse_multi',
        '비닐하우스_단동': 'models/greenhouse_single',
        'TIF_사료작물': 'models/growth_tif'
    }
    
    for model_name, model_dir in models.items():
        csv_path = Path(model_dir) / 'results.csv'
        if not csv_path.exists():
            print(f"✗ {model_name} CSV 파일 없음")
            continue
        
        df = pd.read_csv(csv_path)
        
        # 학습 곡선 그래프
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'{model_name} 학습 곡선', fontsize=18, fontweight='bold')
        
        # mAP50 & mAP50-95
        ax = axes[0, 0]
        ax.plot(df['epoch'], df['metrics/mAP50(M)'], 'b-', linewidth=2, label='mAP50')
        ax.plot(df['epoch'], df['metrics/mAP50-95(M)'], 'r-', linewidth=2, label='mAP50-95')
        ax.set_xlabel('Epoch', fontsize=12, fontweight='bold')
        ax.set_ylabel('mAP', fontsize=12, fontweight='bold')
        ax.set_title('mAP 변화', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(alpha=0.3)
        
        # Precision & Recall
        ax = axes[0, 1]
        ax.plot(df['epoch'], df['metrics/precision(M)'], 'g-', linewidth=2, label='Precision')
        ax.plot(df['epoch'], df['metrics/recall(M)'], 'm-', linewidth=2, label='Recall')
        ax.set_xlabel('Epoch', fontsize=12, fontweight='bold')
        ax.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax.set_title('Precision & Recall 변화', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(alpha=0.3)
        
        # Losses
        ax = axes[1, 0]
        ax.plot(df['epoch'], df['train/box_loss'], 'b-', linewidth=1.5, label='Box Loss', alpha=0.7)
        ax.plot(df['epoch'], df['train/seg_loss'], 'r-', linewidth=1.5, label='Seg Loss', alpha=0.7)
        ax.plot(df['epoch'], df['train/cls_loss'], 'g-', linewidth=1.5, label='Cls Loss', alpha=0.7)
        ax.set_xlabel('Epoch', fontsize=12, fontweight='bold')
        ax.set_ylabel('Loss', fontsize=12, fontweight='bold')
        ax.set_title('Training Loss 변화', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(alpha=0.3)
        
        # F1-Score 계산 및 플롯
        ax = axes[1, 1]
        precision = df['metrics/precision(M)']
        recall = df['metrics/recall(M)']
        f1_scores = 2 * (precision * recall) / (precision + recall)
        f1_scores = f1_scores.fillna(0)
        
        ax.plot(df['epoch'], f1_scores, 'purple', linewidth=2, label='F1-Score')
        ax.set_xlabel('Epoch', fontsize=12, fontweight='bold')
        ax.set_ylabel('F1-Score', fontsize=12, fontweight='bold')
        ax.set_title('F1-Score 변화', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        output_path = Path(model_dir) / 'graphs' / 'training_curves.png'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ {model_name} 학습 곡선 저장: {output_path}")
        
        plt.close()


def main():
    """
    메인 실행 함수
    """
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("="*70)
    print("학습 모델 성능 시각화")
    print("="*70)
    
    print("\n[1/2] 모델 비교 차트 생성 중...")
    create_comparison_chart()
    
    print("\n[2/2] 개별 모델 학습 곡선 생성 중...")
    create_individual_model_charts()
    
    print("\n" + "="*70)
    print("모든 성능 시각화 완료!")
    print("="*70)


if __name__ == "__main__":
    main()

