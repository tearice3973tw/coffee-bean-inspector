# 樹莓派環境設定

## 硬體需求

- Raspberry Pi 3/4/5（建議 4GB+）
- UVC 相機（USB Webcam，支援 V4L2）
- 16GB+ microSD 卡

## 作業系統

建議使用 Raspberry Pi OS（64-bit），已預裝 Python 3。

## 安裝步驟

### 1. 安裝系統依賴

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip libopencv-dev python3-opencv
```

### 2. 安裝 Python 依賴

```bash
pip install -r requirements.txt
```

### 3. 設定相機權限

```bash
sudo usermod -a -G video $USER
# 重新登入生效
```

### 4. 建立資料目錄

```bash
mkdir -p ~/coffee-bean-inspector/data/{train,val}/{good,broken,black,moldy,stink}
mkdir -p ~/coffee-bean-inspector/pi/models
```

### 5. 測試相機

```bash
python3 pi/camera_test.py
```

確認能看到影像後，按 Q 結束。

### 6. 測試 YOLOv8

```bash
python3 -c "from ultralytics import YOLO; print('OK')"
```

## 常見問題

### 相機無法開啟

1. 確認 USB 已插入
2. 檢查 `dmesg | tail` 看是否有影像裝置
3. 嘗試不同的 Camera Index（修改 `collect.py` 和 `inspect.py` 中的 `CAMERA_INDEX`）

### 記憶體不足

樹莓派 1GB 版本可能不夠，建議使用 2GB+ 型號，或減少 `batch` 大小。