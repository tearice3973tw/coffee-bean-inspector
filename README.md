# Coffee Bean Visual Inspector

使用 Raspberry Pi / Jetson Nano + UVC Webcam + YOLOv8 進行咖啡豆瑕疵檢測。

## 兩種版本

| 版本 | 適用硬體 | 特點 |
|------|---------|------|
| **樹莓派版** | Raspberry Pi 3/4/5 | 輕量、便宜、純推論 |
| **Jetson Nano 版** | NVIDIA Jetson Nano | 訓練+推論一體 + AI Agent |

---

## 系統架構

```
[UVC Webcam] → [Raspberry Pi / Jetson Nano]
                      ↓
               [YOLOv8 分類]
                      ↓
               [Telegram 異常通報]
                      ↓
               [GitHub Repo]
                      ↓
         [Jetson Nano 本地訓練]
                      ↓
            [自動部署 + Agent 迴圈]
```

## 目錄結構

```
pi/                   # 樹莓派端（純推論）
  ├── gui.py          # Tkinter 整合視窗（推荐使用）
  ├── collect.py      # 純指令列資料收集
  ├── inspect.py      # 純指令列推論模式
  ├── camera_test.py  # 相機測試
  └── requirements.txt

jetson/               # Jetson Nano 版（訓練+推論+Agent）
  ├── setup.sh         # JetPack + 環境一次安裝
  ├── collect.py      # 資料收集
  ├── train.py        # 本地 GPU 訓練 + 資料增強
  ├── inspect.py      # GPU 加速即時推論
  ├── agent.py        # AI Agent（Llama 驅動，自我訓練）
  └── requirements.txt

train/                # PC / Google Colab 訓練用
  ├── train.ipynb     # Colab notebook
  ├── train_local.py  # 本地 GPU 訓練腳本
  └── requirements.txt

deploy/
  └── deploy_to_pi.sh

docs/
  ├── setup.md
  ├── data_collection.md
  └── model_training.md
```

## 咖啡豆瑕疵類別

| 類別 | 按鍵 | 說明 |
|------|------|------|
| `good` | G | 完好豆 |
| `broken` | B | 破裂豆 |
| `black` | K | 黑色豆（過度發酵） |
| `moldy` | M | 黴菌豆 |
| `stink` | S | 蟲蛀/異味豆 |

---

## 快速開始

### 樹莓派版

```bash
pip install -r pi/requirements.txt
python pi/camera_test.py
python pi/gui.py
```

### Jetson Nano 版

```bash
# 一次安裝所有環境
bash jetson/setup.sh

# 啟動 AI Agent（自動訓練）
python3 jetson/agent.py
```

---

## AI Agent 自我訓練（Jetson 版）

```
每 N 分鐘自動執行：

1. [觀測] 統計各類別樣本數
2. [思考] Llama 3.2 分析是否需要訓練
3. [行動] 若決定訓練 → 執行 train.py → 評估 → 部署
4. [回報] Telegram 通知結果
```

**Agent 特點：**
- 完全本地化 Llama 3.2（不依賴雲端）
- 自訂訓練門檻與檢查間隔
- 新資料觸發自動再訓練

---

## 技術規格

| 項目 | 樹莓派 | Jetson Nano |
|------|--------|------------|
| 推論延遲 | ~200ms | ~30ms |
| 訓練 | ❌ | ✅ |
| AI Agent | ❌ | ✅ Llama 3.2 |
| 建議資料量 | 每類 50+ | 每類 50+ |
| 建議型號 | Pi 4（2GB+） | B01（4GB） |

---

⚠️ **此為個人研究專案，瑕疵檢測結果僅供參考，實際品質判定請依專業標準。**