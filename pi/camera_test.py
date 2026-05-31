#!/usr/bin/env python3
"""相機測試腳本 - 確認 UVC 相機正常運作"""
import cv2
import sys

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("錯誤：無法開啟相機（Index 0）", file=sys.stderr)
        print("請確認：", file=sys.stderr)
        print("  1. 相機已插入 USB", file=sys.stderr)
        print("  2. 嘗試更換 USB 埠", file=sys.stderr)
        print("  3. 確認 camera index 是否正確（可嘗試 1, 2...）", file=sys.stderr)
        sys.exit(1)

    # 讀取相機資訊
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cap.get(cv2.CAP_PROP_FOURCC)

    print("=" * 50)
    print("  相機測試")
    print("=" * 50)
    print(f"  解析度：{int(width)} x {int(height)}")
    print(f"  FPS：{fps:.1f}")
    print(f"  格式：{chr(fourcc & 0xFF)}{chr((fourcc >> 8) & 0xFF)}{chr((fourcc >> 16) & 0xFF)}{chr((fourcc >> 24) & 0xFF)}")
    print()
    print("按 Q 結束測試")
    print("=" * 50)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("錯誤：無法讀取影像幀", file=sys.stderr)
            break

        cv2.imshow("Camera Test - 按 Q 結束", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("測試完成。")

if __name__ == "__main__":
    main()