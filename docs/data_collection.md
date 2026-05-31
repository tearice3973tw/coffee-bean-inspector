# 資料收集說明

## 收集原則

**數量越多越好，但品質比數量重要。**

- 每個類別最少 50 張（建議 100 張以上）
- 光線要穩定（正面光，不要陰影）
- 背景盡量單純（深色或白色背景最佳）
- 豆子擺放方向要有變化（旋轉、翻面）

## 收集流程

### 1. 啟動收集模式

```bash
cd ~/coffee-bean-inspector/pi
python collect.py
```

### 2. 按鍵操作

| 按鍵 | 動作 | 儲存位置 |
|------|------|---------|
| G | 完好豆 | data/train/good/ |
| B | 破裂豆 | data/train/broken/ |
| K | 黑色豆 | data/train/black/ |
| M | 黴菌豆 | data/train/moldy/ |
| S | 蟲蛀/異味豆 | data/train/stink/ |
| Q | 結束 | — |

### 3. 資料分割

收集完成後，手動將部分資料移到 `data/val/`（建議 80% train / 20% val）。

```bash
# 範例：每次取 5 張移到 val
for cls in good broken black moldy stink; do
    ls data/train/$cls/ | head -5 | xargs -I{} mv data/train/$cls/{} data/val/$cls/
done
```

## 瑕疵豆哪裡來？

沒有現成的話，可以：
1. **自己種 / 買瑕疵豆** — 最準確
2. **用正常豆加工** — 破裂（用刀切）、發霉（潮濕環境放置數天）
3. **線上資料集** — Coffee Bean Quality Dataset（Kaggle 搜尋 coffee bean dataset）

## 同步到 GitHub

```bash
cd ~/coffee-bean-inspector
git add data/
git commit -m "data: collect more defect samples"
git push origin main
```

建議資料上傳到 private repo，避免敏感性。