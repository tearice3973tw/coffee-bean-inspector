#!/usr/bin/env python3
"""
咖啡豆資料收集模式
按 G 鍵：儲存到 data/good/
按 D 鍵：儲存到 data/defect/
按 Q 鍵：結束
"""
import cv2
import os
import sys
from datetime import datetime

# 設定
SAVE_DIR = "/home/pi/coffee-bean-inspector/data"
CAMERA_INDEX = 0
FPS = 5  # 降低 FPS，減少儲存時的丟幀

# 類別資料夾
CLASSES = ["good", "broken", "black", "moldy", "stink"]

def ensure_dirs():
    for cls in CLASSES:
        os.makedirs(f"{SAVE_DIR}/{cls}", exist_ok=True)

def save_frame(frame, cls):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = f"{SAVE_DIR}/{cls}/{ts}.jpg"
    cv2.imwrite(path, frame)
    print(f"[已儲存] {cls}/{ts}.jpg")

def main():
    ensure_dirs()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("錯誤：無法開啟相機，請確認 Camera Index 是否正確", file=sys.stderr)
        sys.exit(1)

    # 設定解析度（不要太高，浪費空間）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    print("=" * 50)
    print("  咖啡豆資料收集模式")
    print("=" * 50)
    print("  按 [G] → 完好豆（good）")
    print("  按 [B] → 破裂豆（broken）")
    print("  按 [K] → 黑色豆（black）")
    print("  按 [M] → 黴菌豆（moldy）")
    print("  按 [S] → 蟲蛀豆（stink）")
    print("  按 [Q] → 結束")
    print("=" * 50)
    print(f"儲存位置：{SAVE_DIR}")
    print()

    key_to_class = {
        ord('g'): 'good',
        ord('b'): 'broken',
        ord('k'): 'black',
        ord('m'): 'moldy',
        ord('s'): 'stink',
    }

    last_save_time = 0
    save_interval = 0.3  # 防止按鍵彈跳造成連續儲存

    while True:
        ret, frame = cap.read()
        if not ret:
            print("錯誤：無法讀取影像", file=sys.stderr)
            break

        # 即時顯示
        cv2.imshow("Coffee Bean Collector - 按 Q 離開", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("結束收集。")
            break

        if key in key_to_class:
            now = cv2.getTickCount() / cv2.getTickFrequency()
            if now - last_save_time > save_interval:
                save_frame(frame, key_to_class[key])
                last_save_time = now

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()