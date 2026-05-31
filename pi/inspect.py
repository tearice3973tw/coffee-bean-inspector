#!/usr/bin/env python3
"""
咖啡豆即時瑕疵檢測
推論模式 + 異常時發送 Telegram 通知
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
TELEGRAM_BOT_TOKEN = ""  # 留空停用
TELEGRAM_CHAT_ID = ""    # 留空停用
# --------------------------

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=5)
    except Exception as e:
        print(f"[Telegram 發送失敗] {e}", file=sys.stderr)

def load_model(model_path):
    """使用 Ultralytics YOLO"""
    from ultralytics import YOLO
    if not os.path.exists(model_path):
        print(f"錯誤：模型檔案不存在：{model_path}", file=sys.stderr)
        sys.exit(1)
    model = YOLO(model_path)
    return model

def main():
    parser = argparse.ArgumentParser(description="咖啡豆瑕疵檢測")
    parser.add_argument("--model", "-m", default="models/best.pt",
                        help="模型路徑（預設：models/best.pt）")
    parser.add_argument("--camera", "-c", type=int, default=CAMERA_INDEX,
                        help="相機 index（預設：0）")
    parser.add_argument("--conf", type=float, default=CONFIDENCE_THRESHOLD,
                        help=f"信心閾值（預設：{CONFIDENCE_THRESHOLD}）")
    args = parser.parse_args()

    print("載入模型中...")
    model = load_model(args.model)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print("錯誤：無法開啟相機", file=sys.stderr)
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("=" * 50)
    print("  咖啡豆瑕疵檢測系統")
    print(f"  模型：{args.model}")
    print(f"  信心閾值：{args.conf}")
    print("  按 Q 結束")
    print("=" * 50)

    last_alert_time = 0
    alert_cooldown = 30  # 30 秒內不重複通知

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # 推論
        results = model(frame, conf=args.conf, verbose=False)
        result = results[0]

        # 繪製結果
        annotated = frame.copy()
        has_defect = False

        if result.probs is not None:
            # 分類模式
            top1 = result.probs.top1
            conf = result.probs.top1conf.item()
            cls_name = result.names[top1]

            label = f"{cls_name} {conf:.2f}"
            color = (0, 255, 0) if cls_name == "good" else (0, 0, 255)
            cv2.putText(annotated, label, (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)

            if cls_name != "good" and conf >= args.conf:
                has_defect = True
                cv2.rectangle(annotated, (0, 0),
                              (annotated.shape[1], annotated.shape[0]),
                              (0, 0, 255), 3)
        else:
            # 偵測模式
            if result.boxes is not None:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = result.names[cls_id]
                    label = f"{cls_name} {conf:.2f}"

                    color = (0, 255, 0) if cls_name == "good" else (0, 0, 255)
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(annotated, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    if cls_name != "good":
                        has_defect = True

        # 異常通知
        if has_defect:
            now = time.time()
            if now - last_alert_time > alert_cooldown:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                send_telegram(f"☕️ 咖啡豆異常！\n時間：{ts}\n請確認")
                last_alert_time = now

        # FPS 顯示
        cv2.putText(annotated, "Q=Quit", (10, annotated.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Coffee Bean Inspector - 按 Q 結束", annotated)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()