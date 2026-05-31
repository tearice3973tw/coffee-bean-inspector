#!/usr/bin/env python3
"""
Jetson Nano 即時瑕疵檢測（GPU 加速推論）
"""
import cv2
import os
import sys
import time
import argparse
from datetime import datetime

import requests


# ---------- 設定 ----------
CAMERA_INDEX = 0
CONFIDENCE_THRESHOLD = 0.7
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
# --------------------------


def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
    except Exception as e:
        print(f"[Telegram] 發送失敗：{e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Jetson Nano 咖啡豆瑕疵檢測")
    parser.add_argument("--model", "-m", required=True,
                        help="模型路徑（.pt / .onnx / .tflite）")
    parser.add_argument("--camera", "-c", type=int, default=CAMERA_INDEX,
                        help="相機 index")
    parser.add_argument("--conf", type=float, default=CONFIDENCE_THRESHOLD,
                        help=f"信心閾值（預設：{CONFIDENCE_THRESHOLD}）")
    parser.add_argument("--show-fps", action="store_true",
                        help="顯示 FPS")
    args = parser.parse_args()

    from ultralytics import YOLO

    print(f"載入模型：{args.model}")
    model = YOLO(args.model)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print("錯誤：無法開啟相機", file=sys.stderr)
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("=" * 50)
    print("  Jetson Nano 咖啡豆瑕疵檢測（GPU）")
    print(f"  模型：{args.model}")
    print(f"  按 Q 結束")
    print("=" * 50)

    last_alert = 0
    frame_times = []
    last_save = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        t0 = time.time()
        results = model(frame, conf=args.conf, verbose=False, device=0)
        inference_ms = (time.time() - t0) * 1000
        frame_times.append(inference_ms)
        if len(frame_times) > 30:
            frame_times.pop(0)

        result = results[0]
        annotated = frame.copy()
        has_defect = False

        if result.probs is not None:
            top1 = result.probs.top1
            conf = result.probs.top1conf.item()
            name = result.names[top1]

            color = (0, 255, 0) if name == "good" else (0, 0, 255)
            cv2.putText(annotated, f"{name} {conf:.2f}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
            if name != "good" and conf >= args.conf:
                has_defect = True
                cv2.rectangle(annotated, (0, 0),
                              (annotated.shape[1], annotated.shape[0]),
                              (0, 0, 255), 4)
        elif result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                name = result.names[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = (0, 255, 0) if name == "good" else (0, 0, 255)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated, f"{name} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                if name != "good":
                    has_defect = True

        # FPS 顯示
        avg_ms = sum(frame_times) / len(frame_times)
        fps = 1000 / avg_ms if avg_ms > 0 else 0
        if args.show_fps:
            cv2.putText(annotated, f"FPS: {fps:.1f}", (10, annotated.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 0), 1)

        # 異常通知
        if has_defect:
            now = time.time()
            if now - last_alert > 60:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                send_telegram(f"☕ 咖啡豆異常！\n時間：{ts}\n推論延遲：{avg_ms:.0f}ms\nFPS：{fps:.1f}")
                last_alert = now

        cv2.imshow("Jetson Coffee Inspector - Q=Quit", annotated)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()