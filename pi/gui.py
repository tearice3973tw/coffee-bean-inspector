#!/usr/bin/env python3
"""
咖啡豆視覺檢測系統 - Tkinter GUI
整合相機預覽、資料收集、瑕疵推論於一體
"""
import cv2
import os
import sys
import threading
import argparse
from datetime import datetime
from pathlib import Path

# Tkinter
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# PIL for converting OpenCV → Tkinter
from PIL import Image, ImageTk

# YOLO（延遲載入，避免啟動慢）
MODEL = None

# ---------- 設定 ----------
SAVE_DIR = Path.home() / "coffee-bean-inspector" / "data"
CLASSES = ["good", "broken", "black", "moldy", "stink"]
KEY_MAP = {
    'g': 'good',
    'b': 'broken',
    'k': 'black',
    'm': 'moldy',
    's': 'stink',
}
# --------------------------

class CameraThread(threading.Thread):
    """背景執行取幀，避免 GUI 卡住"""
    def __init__(self, camera_index=0):
        super().__init__(daemon=True)
        self.camera_index = camera_index
        self.frame = None
        self.running = True
        self.lock = threading.Lock()

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        while self.running:
            ret, frame = cap.read()
            with self.lock:
                self.frame = frame if ret else None
        cap.release()

    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.running = False


class CoffeeBeanGUI:
    def __init__(self, model_path=None):
        self.model_path = model_path
        self.camera = None
        self.model = None
        self.mode = tk.StringVar(value="collect")  # collect | inspect
        self.save_dir = SAVE_DIR
        self.counts = {c: 0 for c in CLASSES}
        self.running = True

        # 視窗
        self.root = tk.Tk()
        self.root.title("☕ 咖啡豆視覺檢測系統")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 布局
        self._build_layout()
        self._load_model()
        self._start_camera()

        # 定時更新影像
        self._update_frame()

    def _build_layout(self):
        # --- 左側：影像預覽 ---
        left = ttk.Frame(self.root)
        left.pack(side=tk.LEFT, padx=10, pady=10)

        ttk.Label(left, text="相機預覽", font=("Arial", 14, "bold")).pack()
        self.video_label = ttk.Label(left)
        self.video_label.pack()

        # 模式切換
        mode_frame = ttk.LabelFrame(left, text="模式")
        mode_frame.pack(pady=10, fill=tk.X)
        ttk.Radiobutton(mode_frame, text="📷 資料收集", variable=self.mode,
                        value="collect", command=self._on_mode_change).pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(mode_frame, text="🔍 瑕疵檢測", variable=self.mode,
                        value="inspect", command=self._on_mode_change).pack(anchor=tk.W, padx=10)

        # 收集說明
        self.hint_label = ttk.Label(left, text=self._collect_hint(), foreground="gray")
        self.hint_label.pack(pady=5)

        # --- 右側：狀態與紀錄 ---
        right = ttk.Frame(self.root)
        right.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 統計
        stats = ttk.LabelFrame(right, text="已收集")
        stats.pack(fill=tk.X, pady=(0, 10))
        self.count_labels = {}
        for cls in CLASSES:
            row = ttk.Frame(stats)
            row.pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(row, text=f"  {cls:8s}", width=10).pack(side=tk.LEFT)
            self.count_labels[cls] = ttk.Label(row, text="0", width=6, foreground="blue")
            self.count_labels[cls].pack(side=tk.LEFT)

        # 模型狀態
        status_frame = ttk.Frame(right)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(status_frame, text="模型：").pack(side=tk.LEFT)
        self.model_label = ttk.Label(status_frame, text="未載入", foreground="gray")
        self.model_label.pack(side=tk.LEFT)

        # 推論結果
        result_frame = ttk.LabelFrame(right, text="推論結果")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.result_label = ttk.Label(result_frame, text="—", font=("Arial", 20, "bold"))
        self.result_label.pack(pady=10)
        self.conf_label = ttk.Label(result_frame, text="", foreground="gray")
        self.conf_label.pack()

        # 日誌
        log_frame = ttk.LabelFrame(right, text="操作日誌")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _collect_hint(self):
        return "按鍵蒐集：G=完好 B=破裂 K=黑色 M=黴菌 S=蟲蛀"

    def _on_mode_change(self):
        hint = self._collect_hint() if self.mode.get() == "collect" else "推論模式：自動判斷瑕疵"
        self.hint_label.config(text=hint)
        self.log("模式切換：" + ("收集" if self.mode.get() == "collect" else "檢測"))

    def _load_model(self):
        if self.model_path and os.path.exists(self.model_path):
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
                self.model_label.config(text=os.path.basename(self.model_path), foreground="green")
                self.log("模型已載入：" + self.model_path)
            except Exception as e:
                self.model_label.config(text="載入失敗", foreground="red")
                self.log(f"模型載入錯誤：{e}")

    def _start_camera(self):
        self.camera = CameraThread(0)
        self.camera.start()
        self.log("相機已啟動")

    def _update_frame(self):
        if not self.running:
            return
        frame = self.camera.get_frame()
        if frame is not None:
            # 推論
            annotated = frame.copy()
            result_text = "—"
            conf_text = ""

            if self.model and self.mode.get() == "inspect":
                try:
                    results = self.model(frame, verbose=False)
                    r = results[0]
                    if r.probs is not None:
                        top1 = r.probs.top1
                        conf = r.probs.top1conf.item()
                        name = r.names[top1]
                        result_text = name.upper()
                        conf_text = f"信心：{conf:.1%}"
                        color = (0, 255, 0) if name == "good" else (0, 0, 255)
                        cv2.putText(annotated, f"{name} {conf:.2f}", (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
                        if name != "good":
                            cv2.rectangle(annotated, (0, 0),
                                          (annotated.shape[1], annotated.shape[0]),
                                          (0, 0, 255), 4)
                except Exception:
                    pass

            # 更新 GUI
            self._display_frame(annotated)
            self.result_label.config(text=result_text)
            self.conf_label.config(text=conf_text)

        self.root.after(30, self._update_frame)

    def _display_frame(self, frame):
        # OpenCV BGR → RGB → PIL → Tkinter
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rg
```

The file appears to be truncated at line 206. Let me rewrite the complete GUI file properly.
</think>


<minimax:tool_call>
<invoke name="write_file">
<parameter name="content">#!/usr/bin/env python3
"""
咖啡豆視覺檢測系統 - Tkinter GUI
整合相機預覽、資料收集、瑕疵推論於一體
"""
import cv2
import os
import sys
import threading
import argparse
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk

# ---------- 設定 ----------
SAVE_DIR = Path.home() / "coffee-bean-inspector" / "data"
CLASSES = ["good", "broken", "black", "moldy", "stink"]
MODEL = None
# --------------------------


class CameraThread(threading.Thread):
    def __init__(self, camera_index=0):
        super().__init__(daemon=True)
        self.camera_index = camera_index
        self.frame = None
        self.running = True
        self.lock = threading.Lock()

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        while self.running:
            ret, frame = cap.read()
            with self.lock:
                self.frame = frame if ret else None
        cap.release()

    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.running = False


class CoffeeBeanGUI:
    def __init__(self, model_path=None):
        self.model_path = model_path
        self.camera = None
        self.model = None
        self.mode = tk.StringVar(value="collect")
        self.running = True
        self.counts = {c: 0 for c in CLASSES}
        self.last_save_time = 0

        self.root = tk.Tk()
        self.root.title("☕ 咖啡豆視覺檢測系統")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_layout()
        self._load_model()
        self._start_camera()
        self._update_frame()

    def _build_layout(self):
        # 左側：預覽
        left = ttk.Frame(self.root)
        left.pack(side=tk.LEFT, padx=10, pady=10)

        ttk.Label(left, text="相機預覽", font=("Arial", 14, "bold")).pack()
        self.video_label = ttk.Label(left)
        self.video_label.pack()

        # 模式切換
        mf = ttk.LabelFrame(left, text="模式")
        mf.pack(pady=10, fill=tk.X)
        ttk.Radiobutton(mf, text="📷 資料收集", variable=self.mode,
                        value="collect", command=self._on_mode_change).pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(mf, text="🔍 瑕疵檢測", variable=self.mode,
                        value="inspect", command=self._on_mode_change).pack(anchor=tk.W, padx=10)

        self.hint = ttk.Label(left, text="按鍵蒐集：G=完好 B=破裂 K=黑色 M=黴菌 S=蟲蛀 Q=結束", foreground="gray")
        self.hint.pack(pady=5)

        # 右側：狀態
        right = ttk.Frame(self.root)
        right.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 統計
        sf = ttk.LabelFrame(right, text="已收集")
        sf.pack(fill=tk.X, pady=(0, 10))
        self.count_labels = {}
        for cls in CLASSES:
            row = ttk.Frame(sf)
            row.pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(row, text=f"  {cls:8s}", width=10).pack(side=tk.LEFT)
            self.count_labels[cls] = ttk.Label(row, text="0", width=6, foreground="blue")
            self.count_labels[cls].pack(side=tk.LEFT)

        # 模型狀態
        tf = ttk.Frame(right)
        tf.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(tf, text="模型：").pack(side=tk.LEFT)
        self.model_label = ttk.Label(tf, text="未載入", foreground="gray")
        self.model_label.pack(side=tk.LEFT)

        # 推論結果
        rf = ttk.LabelFrame(right, text="推論結果")
        rf.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.result_label = ttk.Label(rf, text="—", font=("Arial", 24, "bold"))
        self.result_label.pack(pady=10)
        self.conf_label = ttk.Label(rf, text="", foreground="gray")
        self.conf_label.pack()

        # 日誌
        lf = ttk.LabelFrame(right, text="操作日誌")
        lf.pack(fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(lf, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 按鍵綁定
        self.root.bind('g', lambda e: self._save('good'))
        self.root.bind('b', lambda e: self._save('broken'))
        self.root.bind('k', lambda e: self._save('black'))
        self.root.bind('m', lambda e: self._save('moldy'))
        self.root.bind('s', lambda e: self._save('stink'))
        self.root.bind('q', lambda e: self.on_close())

    def _on_mode_change(self):
        m = "收集" if self.mode.get() == "collect" else "檢測"
        self.hint.config(text="按鍵蒐集：G=完好 B=破裂 K=黑色 M=黴菌 S=蟲蛀 Q=結束" if self.mode.get() == "collect" else "自動檢測中...")
        self.log(f"切換至{m}模式")

    def _load_model(self):
        if self.model_path and os.path.exists(self.model_path):
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
                self.model_label.config(text=os.path.basename(self.model_path), foreground="green")
                self.log(f"模型已載入：{os.path.basename(self.model_path)}")
            except Exception as e:
                self.model_label.config(text="載入失敗", foreground="red")
                self.log(f"模型錯誤：{e}")

    def _start_camera(self):
        self.camera = CameraThread(0)
        self.camera.start()
        self.log("相機已啟動")

    def _update_frame(self):
        if not self.running:
            return
        frame = self.camera.get_frame()
        if frame is not None:
            annotated = frame.copy()
            result_text = "—"
            conf_text = ""

            if self.model and self.mode.get() == "inspect":
                try:
                    results = self.model(frame, verbose=False)
                    r = results[0]
                    if r.probs is not None:
                        top1 = r.probs.top1
                        conf = r.probs.top1conf.item()
                        name = r.names[top1]
                        result_text = name.upper()
                        conf_text = f"信心：{conf:.1%}"
                        color = (0, 255, 0) if name == "good" else (0, 0, 255)
                        cv2.putText(annotated, f"{name} {conf:.2f}", (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
                        if name != "good":
                            cv2.rectangle(annotated, (0, 0),
                                          (annotated.shape[1], annotated.shape[0]),
                                          (0, 0, 255), 4)
                except Exception:
                    pass

            self._display_frame(annotated)
            self.result_label.config(text=result_text)
            self.conf_label.config(text=conf_text)

        self.root.after(30, self._update_frame)

    def _display_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

    def _save(self, cls):
        frame = self.camera.get_frame()
        if frame is None:
            return
        self.counts[cls] += 1
        self.count_labels[cls].config(text=str(self.counts[cls]))
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.save_dir / cls / f"{ts}.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), frame)
        self.log(f"已儲存：{cls}/{ts}.jpg")

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def on_close(self):
        self.running = False
        if self.camera:
            self.camera.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="咖啡豆視覺檢測 GUI")
    parser.add_argument("--model", "-m", default=None,
                        help="模型路徑（可之後再指定）")
    args = parser.parse_args()

    app = CoffeeBeanGUI(model_path=args.model)
    app.run()


if __name__ == "__main__":
    main()