# 模型訓練說明

## 方式一：Google Colab（推薦新手）

1. 開啟 `train/train.ipynb`
2. 上傳 `data/` 資料夾到 Colab
3. 按順序執行每個 cell
4. 下載 `best.pt` 模型檔案
5. 用 `deploy/deploy_to_pi.sh` 部署到樹莓派

**優點：** 不需要本地 GPU，雲端 T4 GPU 免費

## 方式二：本地 GPU 訓練

```bash
pip install -r train/requirements.txt

python train/train_local.py \
    --data /path/to/data \
    --epochs 50 \
    --model yolov8n-cls \
    --imgsz 224
```

**需要的硬體：** NVIDIA GPU + CUDA 11.x + cuDNN

## 模型選擇

| 模型 | 參數量 | 樹莓派推論速度 | 準確率 |
|------|--------|--------------|--------|
| YOLOv8n-cls | 2.7M | ~50ms/張 | 基礎 |
| YOLOv8s-cls | 6.9M | ~100ms/張 | 較高 |
| YOLOv8m-cls | 15.9M | ~250ms/張 | 高 |

樹莓派建議用 `yolov8n-cls`，犧牲一點準確率換取速度。

## 訓練後確認

```bash
# 在樹莓派上測試模型
python3 pi/inspect.py --model models/best.pt
```

觀察：
- 完好豆是否正確辨識為 good？
- 各種瑕疵豆是否被正確分類？
- 是否有誤判？

## 如何提升準確率

1. **增加資料量** — 最有效
2. **資料增強** — 旋轉、翻轉、亮度調整（在訓練指令中加入 `--augment`）
3. **光線統一** — 拍攝時盡量控制光源
4. **類別平衡** — 各類別資料數量要接近（差太多會傾斜學習）

## 持續學習流程

```
收集新樣本（Pi）→ Commit 到 GitHub → PC Pull → 重新訓練 → Deploy 回 Pi
```

可以在 PC 上設一個 cron job 每天自動 pull 並訓練新模型。