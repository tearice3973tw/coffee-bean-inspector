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
pi/                   # 樹莓派端（直接放 Pi 上跑）
  ├── collect.py      # 資料收集模式（按鍵分類儲存）
  ├── inspect.py      # 即時推論模式
  ├── camera_test.py   # 相機測試
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

## 資料夾結構（蒐集足夠資料後）

```
data/
  ├── train/
  │   ├── good/       # 完好豆影像
  │   └── defect/      # 瑕疵豆影像
  └── val/
      ├── good/
      └── defect/
```

## 咖啡豆瑕疵類別（初期）

| 類別 | 說明 |
|------|------|
| `good` | 完好豆 |
| `broken` | 破裂豆 |
| `black` | 黑色豆（過度發酵） |
| `moldy` | 黴菌豆 |
| `stink` | 蟲蛀/異味豆 |

## 快速開始

### 1. 樹莓派環境設定

```bash
pip install -r pi/requirements.txt
python pi/camera_test.py   # 先確認相機正常
```

### 2. 資料收集

```bash
python pi/collect.py
# 按 G → 存到 data/good/
# 按 D → 存到 data/defect/
# 按 Q → 結束
```

### 3. 訓練模型

在 Google Colab 或本地 GPU PC 開啟 `train/train.ipynb`。

### 4. 部署推論

將訓練好的 `best.pt` 放到 `pi/models/`，然後：

```bash
python pi/inspect.py --model models/best.pt
```

## 技術規格

| 項目 | 數值 |
|------|------|
| 推論延遲 | ~200ms（YOLOv8n） |
| 準確率 | 取決於資料品質與數量 |
| 建議最低資料量 | 每類 50 張 |

---

⚠️ **此為個人研究專案，瑕疵檢測結果僅供參考，實際品質判定請依專業標準。**