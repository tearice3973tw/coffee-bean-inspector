#!/bin/bash
# 懶人安裝腳本：Jetson Nano 環境設定
# 適用於 Jetson Nano B01（4GB）
# 執行方式：bash jetson/setup.sh

set -e

echo "=========================================="
echo "  Jetson Nano 環境設定"
echo "=========================================="

# 檢查架構
if ! uname -a | grep -q aarch64; then
    echo "錯誤：此腳本僅支援 ARM64 架構（Jetson Nano）"
    exit 1
fi

echo "[1/6] 更新系統..."
sudo apt update && sudo apt upgrade -y

echo "[2/6] 安裝系統依賴..."
sudo apt install -y \
    python3-pip libopencv-dev python3-opencv \
    git curl htop cmake build-essential \
    libopenblas-dev liblapack-dev libjpeg-dev \
    zlib1g-dev python3-dev libncurses5-dev

echo "[3/6] 安裝 Python 依賴..."
pip3 install --upgrade pip setuptools wheel

# 安裝 PyTorch（GPU 支援）
echo "[4/6] 安裝 PyTorch + TorchVision（CUDA）..."
# 確認 JetPack 版本
JETPACK_VERSION=$(head -c 1 /etc/nv_tegra_release 2>/dev/null || echo "4")
echo "JetPack 版本：${JETPACK_VERSION}"

# 安裝 ultralytics（包含 YOLOv8）
pip3 install ultralytics --quiet

# 安裝其他依賴
pip3 install -q \
    opencv-python-headless \
    numpy pandas scikit-learn \
    pillow requests pyserial

echo "[5/6] 安裝 Ollama（本地 LLM）..."
curl -fsSL https://ollama.ai/install.sh | sh

echo "[6/6] 下載 Llama 模型..."
ollama pull llama3.2:1b   # 輕量版本，適合 Jetson Nano

echo ""
echo "=========================================="
echo "  設定完成！"
echo "=========================================="
echo ""
echo "啟動 Ollama："
echo "  ollama serve"
echo ""
echo "測試 YOLOv8："
echo "  python3 jetson/train.py --help"
echo ""
echo "啟動 Agent："
echo "  python3 jetson/agent.py"
echo "=========================================="