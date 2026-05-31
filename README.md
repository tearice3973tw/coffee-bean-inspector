# Coffee Bean Visual Inspector

使用 Raspberry Pi + UVC Webcam + YOLOv8 進行咖啡豆瑕疵檢測。

## 系統架構

```
[UVC Webcam] → [Raspberry Pi] → [YOLOv8 分類] → [Telegram 異常通報]
                      ↓
               [資料收集模式]
                /data/good/    ← 按 G 鍵
                /data/defect/  ← 按 D 鍵
                      ↓
               [GitHub Repo]
                      ↓
              [PC GPU 訓練]
                      ↓
            [匯出模型部署回 Pi]
```

## 目錄結構

```
pi/                   # 樹莓派端
  ├── gui.py          # Tkinter 整合視窗（推荐使用）
  ├── collect.py      # 純指令列資料收集
  ├── inspect.py      # 純指令列推論模式
  ├── camera_test.py  # 相機測試
  └── requirements.txt

train/                # PC / Google Colab 訓練用
  ├── train.ipynb     # Colab notebook（含訓練流程）
  ├── train_local.py  # 本地 GPU 訓練腳本
  └── requirements.txt

deploy/               # 部署腳本
  └── deploy_to_pi.sh

docs/
  ├── setup.md        # 樹莓派環境設定
  ├── data_collection.md  # 資料收集說明
  └── model_training.md   # 模型訓練說明
```

## 咖啡豆瑕疵類別

| 類別 | 按鍵 | 說明 |
|------|------|------|
| `good` | G | 完好豆 |
| `broken` | B | 破裂豆 |
| `black` | K | 黑色豆（過度發酵） |
| `moldy` | M | 黴菌豆 |
| `stink` | S | 蟲蛀/異味豆 |

## 快速開始

### 1. 樹莓派環境設定

```bash
pip install -r pi/requirements.txt
python pi/camera_test.py   # 先確認相機正常
```

### 2. 啟動 GUI（推薦）

```bash
python pi/gui.py
```

GUI 包含：
- 左側：即時相機預覽 + 模式切換
- 右側：已收集統計、模型狀態、推論結果、操作日誌
- 按 `G/B/K/M/S` 快速分類儲存
- 按 `Q` 結束

### 3. 單獨使用指令列模式

```bash
# 資料收集
python pi/collect.py
# 按 G/B/K/M/S 分類，按 Q 結束

# 即時推論（需先有模型）
python pi/inspect.py --model models/best.pt
```

### 4. 訓練模型

在 Google Colab 或本地 GPU PC 開啟 `train/train.ipynb`，
或使用本地訓練：

```bash
python train/train_local.py --data /path/to/data --epochs 50
```

### 5. 部署推論

將 `best.pt` 放到 `pi/models/`，然後：

```bash
python pi/inspect.py --model models/best.pt
# 或 GUI 模式
python pi/gui.py --model models/best.pt
```

## 技術規格

| 項目 | 數值 |
|------|------|
| 推論延遲 | ~200ms（YOLOv8n） |
| 建議最低資料量 | 每類 50 張（建議 100+） |
| 建議樹莓派型號 | Raspberry Pi 4（2GB+） |

## 自主訓練流程

```
收集新樣本（Pi GUI）→ Commit 到 GitHub → PC Pull → 訓練 → Deploy 回 Pi
```

1. **收集：** `python pi/gui.py` 按 G/B/K/M/S 分類儲存
2. **同步：** `git add data/ && git commit && git push`
3. **訓練：** Colab 或本地 GPU 訓練
4. **部署：** `deploy/deploy_to_pi.sh` 或手動複製

---

⚠️ **此為個人研究專案，瑕疵檢測結果僅供參考，實際品質判定請依專業標準。**