#!/bin/bash
# deploy_to_pi.sh
# 將訓練好的模型部署到樹莓派
# 用法：./deploy_to_pi.sh [model_file] [pi_user@pi_host]
set -e

MODEL_FILE="${1:-runs/coffee_classify/weights/best.pt}"
PI_TARGET="${2:-pi@raspberrypi}"
PI_PATH="/home/pi/coffee-bean-inspector/pi/models"

if [ ! -f "$MODEL_FILE" ]; then
    echo "錯誤：模型檔案不存在：$MODEL_FILE"
    exit 1
fi

echo "複製模型到樹莓派..."
ssh "$PI_TARGET" "mkdir -p $PI_PATH"
scp "$MODEL_FILE" "$PI_TARGET:$PI_PATH/best.pt"

echo "完成！模型已部署至 $PI_TARGET:$PI_PATH/best.pt"
echo "在樹莓派上執行："
echo "  cd ~/coffee-bean-inspector/pi"
echo "  python inspect.py --model models/best.pt"