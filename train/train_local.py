#!/usr/bin/env python3
"""
本地 GPU 訓練腳本（需要 NVIDIA GPU + CUDA）
"""
import argparse
import os
import shutil
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description="咖啡豆分類模型訓練")
    parser.add_argument("--data", "-d", required=True,
                        help="資料目錄（需包含 train/ 和 val/ 子資料夾）")
    parser.add_argument("--epochs", "-e", type=int, default=50,
                        help="訓練輪數（預設：50）")
    parser.add_argument("--model", "-m", default="yolov8n-cls",
                        help="模型大小：yolov8n-cls / yolov8s-cls / yolov8m-cls")
    parser.add_argument("--imgsz", "-i", type=int, default=224,
                        help="影像尺寸（預設：224）")
    parser.add_argument("--batch", "-b", type=int, default=32,
                        help="批次大小（預設：32）")
    parser.add_argument("--project", "-p", default="./runs",
                        help="輸出目錄")
    parser.add_argument("--name", "-n", default="coffee_classify",
                        help="實驗名稱")
    args = parser.parse_args()

    # 確認資料夾存在
    for split in ["train", "val"]:
        for cls in ["good", "broken", "black", "moldy", "stink"]:
            path = f"{args.data}/{split}/{cls}"
            if not os.path.exists(path):
                print(f"警告：{path} 不存在")
                return

    print("=" * 50)
    print(f"  咖啡豆分類模型訓練")
    print("=" * 50)
    print(f"  資料目錄：{args.data}")
    print(f"  模型：{args.model}")
    print(f"  影像尺寸：{args.imgsz}")
    print(f"  訓練輪數：{args.epochs}")
    print(f"  輸出：{args.project}/{args.name}")
    print("=" * 50)

    model = YOLO(f"{args.model}.pt")

    results = model.train(
        data=args.data,
        epochs=args.epochs,
        model=args.model,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
        exist_ok=True,
        pretrained=True,
        optimizer="Adam",
        lr0=0.001,
        patience=10,
        verbose=True,
    )

    print("訓練完成！")
    print(f"最佳模型：{args.project}/{args.name}/weights/best.pt")
    print(f"最終模型：{args.project}/{args.name}/weights/last.pt")

if __name__ == "__main__":
    main()