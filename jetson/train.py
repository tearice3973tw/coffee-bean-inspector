#!/usr/bin/env python3
"""
Jetson Nano 咖啡豆檢測 - 訓練腳本
本地 GPU 訓練 + 自動資料增強 + 模型匯出
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
from ultralytics import YOLO


def augment_image(img, seed=None):
    """簡單資料增強（旋轉、翻轉、亮度）"""
    if seed:
        np.random.seed(seed)

    # 水平翻轉
    if np.random.rand() > 0.5:
        img = cv2.flip(img, 1)

    # 旋轉（±15度）
    h, w = img.shape[:2]
    angle = np.random.uniform(-15, 15)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    # 亮度調整
    factor = np.random.uniform(0.7, 1.3)
    img = np.clip(img * factor, 0, 255).astype(np.uint8)

    return img


def prepare_data(data_dir, augment_factor=3):
    """
    將原始資料做增強並重新整理
    data_dir/ 結構：
      train/good/
      train/broken/
      ...
      val/good/
      ...
    """
    data_path = Path(data_dir)
    aug_path = data_path.parent / "data_aug"
    aug_path.mkdir(exist_ok=True)

    splits = ["train", "val"]
    classes = ["good", "broken", "black", "moldy", "stink"]

    for split in splits:
        for cls in classes:
            src = data_path / split / cls
            if not src.exists():
                continue
            dst = aug_path / split / cls
            dst.mkdir(parents=True, exist_ok=True)

            images = list(src.glob("*.jpg")) + list(src.glob("*.png"))
            for img_path in images:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue

                # 原始圖
                out_path = dst / img_path.name
                cv2.imwrite(str(out_path), img)

                # 增強圖
                for i in range(augment_factor):
                    aug_img = augment_image(img, seed=int(img_path.stat().st_mtime) + i)
                    out_path = dst / f"{img_path.stem}_aug{i}{img_path.suffix}"
                    cv2.imwrite(str(out_path), aug_img)

    return str(aug_path)


def main():
    parser = argparse.ArgumentParser(description="Jetson Nano 咖啡豆分類訓練")
    parser.add_argument("--data", "-d", required=True,
                        help="資料目錄（含 train/val 各類別）")
    parser.add_argument("--augment", "-a", type=int, default=3,
                        help="每張增強倍數（預設：3）")
    parser.add_argument("--epochs", "-e", type=int, default=50,
                        help="訓練輪數")
    parser.add_argument("--model", "-m", default="yolov8s-cls",
                        help="模型：yolov8n/s/m-cls")
    parser.add_argument("--batch", "-b", type=int, default=16,
                        help="批次大小（Jetson Nano 4GB 建議 8-16）")
    parser.add_argument("--imgsz", "-i", type=int, default=224,
                        help="影像尺寸")
    parser.add_argument("--project", "-p", default="./runs",
                        help="輸出目錄")
    args = parser.parse_args()

    print("=" * 50)
    print("  Jetson Nano 咖啡豆分類訓練")
    print("=" * 50)
    print(f"  資料目錄：{args.data}")
    print(f"  增強倍數：{args.augment}")
    print(f"  模型：{args.model}")
    print(f"  批次大小：{args.batch}")
    print(f"  影像尺寸：{args.imgsz}")
    print(f"  訓練輪數：{args.epochs}")
    print("=" * 50)

    # 資料增強
    print("\n[1/3] 資料增強處理中...")
    aug_data = prepare_data(args.data, augment_factor=args.augment)
    print(f"      增強後資料：{aug_data}")

    # 訓練
    print("\n[2/3] 開始訓練...")
    model = YOLO(f"{args.model}.pt")

    results = model.train(
        data=aug_data,
        epochs=args.epochs,
        model=args.model,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name="coffee_classify",
        exist_ok=True,
        pretrained=True,
        optimizer="Adam",
        lr0=0.001,
        patience=10,
        verbose=True,
        device=0,  # GPU
    )

    # 驗證
    print("\n[3/3] 最終驗證...")
    val_results = model.val(data=aug_data, verbose=True)
    print(f"      Top-1 準確率：{val_results.top1 * 100:.1f}%")
    print(f"      Top-5 準確率：{val_results.top5 * 100:.1f}%")

    # 匯出
    print("\n    匯出 ONNX 模型...")
    onnx_path = model.export(format="onnx", imgsz=args.imgsz)
    print(f"      已匯出：{onnx_path}")

    print("\n    匯出 TFLite 模型（邊緣部署）...")
    tflite_path = model.export(format="tflite", imgsz=args.imgsz)
    print(f"      已匯出：{tflite_path}")

    best_pt = f"{args.project}/coffee_classify/weights/best.pt"
    print(f"\n✅ 訓練完成！最佳模型：{best_pt}")
    print(f"   ONNX：{onnx_path}")
    print(f"   TFLite：{tflite_path}")


if __name__ == "__main__":
    main()