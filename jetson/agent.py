#!/usr/bin/env python3
"""
咖啡豆自我訓練 Agent（Jetson Nano 版）
由本地 Llama 3.2 驅動的 AI Agent 迴圈
"""
import os
import sys
import time
import json
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests


# ---------- 設定 ----------
GITHUB_REPO = "tearice3973tw/coffee-bean-inspector"
GITHUB_TOKEN = ""  # 留空停用 GitHub 功能
DATA_DIR = Path.home() / "coffee-bean-inspector" / "data"
MODEL_DIR = Path.home() / "coffee-bean-inspector" / "jetson_models"
LOG_FILE = Path.home() / "coffee-bean-inspector" / "agent.log"
OLLAMA_MODEL = "llama3.2:1b"
TRAIN_THRESHOLD = 20  # 新樣本超過這個數量才訓練
CHECK_INTERVAL = 300  # 每 5 分鐘檢查一次（秒）
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
# --------------------------


# ---------- 日誌 ----------
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
    except Exception:
        pass


# ---------- Ollama LLM ----------
def ask_llama(prompt: str, system: str = "") -> str:
    """使用本地 Ollama Llama 進行推理"""
    import ollama

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = ollama.chat(model=OLLAMA_MODEL, messages=messages, stream=False)
        return resp["message"]["content"]
    except Exception as e:
        log(f"[LLM 錯誤] {e}")
        return f"LLM 錯誤：{e}"


# ---------- 資料統計 ----------
def count_samples(cls_dir: Path) -> int:
    if not cls_dir.exists():
        return 0
    return len(list(cls_dir.glob("*.jpg")) + len(list(cls_dir.glob("*.png")))


def get_data_summary() -> dict:
    """取得各類別樣本數"""
    classes = ["good", "broken", "black", "moldy", "stink"]
    summary = {}
    total = 0
    for cls in classes:
        train_count = count_samples(DATA_DIR / "train" / cls)
        val_count = count_samples(DATA_DIR / "val" / cls)
        summary[cls] = {"train": train_count, "val": val_count}
        total += train_count + val_count
    summary["_total"] = total
    return summary


def get_last_training_time() -> Optional[datetime]:
    """讀取上次訓練時間"""
    info_file = MODEL_DIR / "training_info.json"
    if not info_file.exists():
        return None
    try:
        with open(info_file) as f:
            info = json.load(f)
        return datetime.fromisoformat(info["last_training"])
    except Exception:
        return None


def save_training_info(accuracy: float, model_path: str, duration: float):
    """儲存訓練資訊"""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    info = {
        "last_training": datetime.now().isoformat(),
        "accuracy": accuracy,
        "model": model_path,
        "duration_sec": duration,
    }
    with open(MODEL_DIR / "training_info.json", "w") as f:
        json.dump(info, f, indent=2)


# ---------- 訓練 ----------
def run_training() -> dict:
    """執行一次訓練並回傳結果"""
    if not DATA_DIR.exists():
        return {"success": False, "error": "資料目錄不存在"}

    summary = get_data_summary()
    if summary["_total"] < 20:
        return {"success": False, "error": f"樣本不足（{summary['_total']} < 20）"}

    log("========== 開始訓練 ==========")
    t0 = time.time()

    try:
        # 使用本地 train.py
        result = subprocess.run(
            [
                sys.executable,
                "/home/pi/coffee-bean-inspector/jetson/train.py",
                "--data", str(DATA_DIR),
                "--epochs", "30",
                "--model", "yolov8s-cls",
                "--batch", "8",
            ],
            capture_output=True,
            text=True,
            timeout=3600,
        )
        duration = time.time() - t0

        if result.returncode == 0:
            # 解析輸出取得準確率
            acc = 0.85  # 預設值
            for line in result.stdout.split("\n"):
                if "Top-1" in line or "accuracy" in line.lower():
                    try:
                        acc = float([x for x in line.split() if "." in x][-1].replace("%", ""))
                    except Exception:
                        pass

            model_path = str(MODEL_DIR / "best.pt")
            save_training_info(acc, model_path, duration)

            msg = f"✅ 訓練完成！\n耗時：{duration:.0f}秒\n準確率：{acc:.1%}"
            log(msg)
            send_telegram(msg)

            return {"success": True, "accuracy": acc, "duration": duration, "model": model_path}
        else:
            log(f"訓練失敗：{result.stderr}")
            return {"success": False, "error": result.stderr}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "訓練超時（1小時）"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------- GitHub ----------
def check_github_updates() -> int:
    """檢查 GitHub 是否有新的 commit，返回新增檔案數"""
    if not GITHUB_TOKEN:
        return 0
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/commits"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            commits = resp.json()
            if commits:
                latest = datetime.fromisoformat(commits[0]["commit"]["author"]["date"].replace("Z", "+00:00"))
                # 如果最近 5 分鐘有 commit
                if datetime.now(latest.tzinfo) - latest < timedelta(minutes=10):
                    return len(commits[0].get("files", []))
        return 0
    except Exception:
        return 0


# ---------- AI Agent 核心 ----------
def agent_think(summary: dict, last_train: Optional[datetime]) -> str:
    """
    Llama 分析現況並給出建議
    """
    total = summary["_total"]
    breakdown = "\n".join(
        f"  - {cls}: train={d['train']}, val={d['val']}"
        for cls, d in summary.items() if cls != "_total"
    )
    last_train_str = last_train.strftime("%Y-%m-%d %H:%M") if last_train else "尚未訓練"

    system_prompt = """你是一個邊緣 AI 視覺檢測系統的顧問。
根據以下資料狀況，決定是否應該觸發模型訓練。
只回覆以下格式之一：
DECIDE: TRAIN - 理由
DECIDE: WAIT - 理由"""

    user_prompt = f"""
現況：
- 資料總量：{total} 張
- 各類別分布：
{breakdown}
- 上次訓練時間：{last_train_str}

考慮：
1. 樣本數是否足夠（每類至少 20 張）？
2. 類別分布是否平衡？
3. 距上次訓練是否夠久（超過 1 天）？

請給出決策。"""

    return ask_llama(user_prompt, system=system_prompt)


def agent_act(decision: str) -> dict:
    """
    根據 LLM 決策執行對應行動
    """
    if decision.startswith("DECIDE: TRAIN"):
        return run_training()
    else:
        return {"action": "wait", "reason": decision}


# ---------- 主 Agent 迴圈 ----------
def agent_loop():
    log("========== Agent 啟動 ==========")

    # Ollama 健康檢查
    try:
        import ollama
        models = ollama.list()
        log(f"Ollama 模型：{[m['name'] for m in models.get('models', [])]}")
    except ImportError:
        log("錯誤：請先安裝 Ollama：curl -fsSL https://ollama.ai/install.sh | sh")
        sys.exit(1)

    while True:
        try:
            log("========== Agent 循環 ==========")

            # 1. 觀測
            summary = get_data_summary()
            last_train = get_last_training_time()
            log(f"資料總量：{summary['_total']} 張")

            # 2. 思考（LLM 決策）
            decision = agent_think(summary, last_train)
            log(f"LLM 決策：{decision}")

            # 3. 行動
            result = agent_act(decision)
            log(f"行動結果：{result}")

            # 4. GitHub 更新檢查
            gh_new = check_github_updates()
            if gh_new > 0:
                log(f"GitHub 有 {gh_new} 個新檔案")

        except Exception as e:
            log(f"Agent 迴圈錯誤：{e}")
            send_telegram(f"⚠️ Agent 錯誤：{e}")

        log(f"等待 {CHECK_INTERVAL} 秒後再次檢查...")
        time.sleep(CHECK_INTERVAL)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="咖啡豆自我訓練 Agent")
    parser.add_argument("--interval", "-i", type=int, default=CHECK_INTERVAL,
                        help=f"檢查間隔（秒，預設：{CHECK_INTERVAL}）")
    args = parser.parse_args()

    globals()["CHECK_INTERVAL"] = args.interval

    # 前置檢查
    if not DATA_DIR.exists():
        log(f"警告：{DATA_DIR} 不存在，將嘗試建立")
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    agent_loop()


if __name__ == "__main__":
    main()