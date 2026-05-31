# Jetson Nano AI Agent 版本

訓練 + 推論 + Agent（自我訓練）一體，執行於 NVIDIA Jetson Nano。

## 與樹莓派版本的差異

| 功能 | 樹莓派 | Jetson Nano |
|------|--------|------------|
| 本地訓練 | ❌ | ✅ GPU 訓練 |
| 推論速度 | ~200ms（YOLOv8n） | ~20ms（YOLOv8s） |
| AI Agent | ❌ | ✅ Llama 3.2 本地決策 |
| 模型規模 | YOLOv8n（輕量） | YOLOv8s/m（較大） |

## 目錄結構

```
jetson/
├── setup.sh        # JetPack + 環境一次安裝
├── collect.py      # 資料收集（與 RPi 版相同）
├── train.py        # 本地 GPU 訓練 + 資料增強
├── inspect.py      # GPU 加速即時推論
├── agent.py        # AI Agent 核心（Llama 驅動）
└── requirements.txt
```

## 懶人安裝

```bash
bash jetson/setup.sh
```

## 使用方式

### 1. 資料收集

```bash
python3 jetson/collect.py
# 按 G/B/K/M/S 分類儲存
```

### 2. 本地訓練

```bash
python3 jetson/train.py --data ~/coffee-bean-inspector/data --epochs 30 --model yolov8s-cls
```

### 3. 即時推論

```bash
python3 jetson/inspect.py --model runs/coffee_classify/weights/best.pt --show-fps
```

### 4. 啟動 AI Agent（自動訓練）

```bash
python3 jetson/agent.py
```

## AI Agent 工作流程

```
每 N 分鐘自動執行：

1. [觀測] 統計各類別樣本數、檢查 GitHub 更新
2. [思考] Llama 3.2 分析是否需要訓練
3. [行動] 若決定訓練 → 執行 train.py → 評估 → 部署
4. [回報] Telegram 通知訓練結果
```

## Agent 設定

編輯 `agent.py` 中的參數：

```python
OLLAMA_MODEL = "llama3.2:1b"       # LLM 模型
TRAIN_THRESHOLD = 20                # 新樣本門檻
CHECK_INTERVAL = 300                 # 檢查間隔（秒）
GITHUB_REPO = "your/repo"           # GitHub Repo
```

## Ollama 模型選擇

Jetson Nano 4GB 建議：

| 模型 | VRAM | 速度 |
|------|------|------|
| llama3.2:1b | ~1GB | 快 |
| llama3.2:3b | ~2GB | 中 |
| phi3:3.8b | ~2GB | 中 |

更換模型：
```bash
ollama pull llama3.2:3b
# 修改 agent.py 中的 OLLAMA_MODEL
```

## 技術規格

| 項目 | 數值 |
|------|------|
| GPU | NVIDIA Maxwell (128 cores) |
| 訓練速度 | ~3-5 it/s（YOLOv8s） |
| 推論延遲 | ~20-30ms/張（YOLOv8s） |
| 記憶體需求 | 訓練 4GB+ / 推論 1GB+ |