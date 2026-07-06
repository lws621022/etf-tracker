# 籌碼小宇｜台股 ETF 持股追蹤

純前端台股 ETF 持股追蹤網站，使用 HTML、CSS、JavaScript 與本機 JSON 資料，不需要後端資料庫。

## 功能

- 主動式 ETF 進出
- ETF 總覽，支援卡片與列表模式
- 投信買賣超，支援當日、5日、20日、60日切換
- 三大法人買賣超
- 用股票查 ETF，可搜尋股票代號或名稱
- 績效圖，最多勾選 8 檔 ETF 並使用 Chart.js 比較績效
- 每日焦點
- 事件
- 退休計算機，估算退休時可能累積資產並顯示圖表與表格

## 專案結構

```text
etf-tracker/
├─ .github/
│  └─ workflows/
│     └─ update-data.yml
├─ index.html
├─ src/
│  ├─ main.js
│  ├─ style.css
│  ├─ data-loader.js
│  ├─ charts.js
│  └─ pages/
│     ├─ active-etf.js
│     ├─ overview.js
│     ├─ holdings.js
│     ├─ institutions.js
│     ├─ stock-search.js
│     ├─ performance.js
│     ├─ events.js
│     └─ retirement.js
├─ data/
│  ├─ etf_list.json
│  ├─ etf_holdings.json
│  ├─ institution_trades.json
│  ├─ investment_trust_trades.json
│  ├─ holdings_update_report.json
│  ├─ last_updated.json
│  └─ price_history.json
├─ sources/
│  ├─ holdings/
│  │  ├─ 0050.csv
│  │  ├─ 0056.csv
│  │  ├─ 006208.csv
│  │  ├─ 00878.csv
│  │  └─ 00919.csv
│  ├─ etf_list.csv
│  ├─ etf_holdings.csv
│  ├─ institution_trades.csv
│  └─ price_history.csv
├─ scripts/
│  ├─ convert_holdings.py
│  ├─ update_all.py
│  ├─ update_data.py
│  └─ update_holdings.py
├─ requirements.txt
├─ 更新網站資料.bat
├─ package.json
└─ README.md
```

## 本機執行

因為網站會用 `fetch()` 讀取 `data/*.json`，請使用本機靜態伺服器開啟，不要直接雙擊 `index.html`。

### 使用 Node.js

```bash
npm install
npm run dev
```

接著開啟終端機顯示的本機網址，通常是 `http://localhost:5173`。

### 使用 Python

```bash
python -m http.server 8000
```

接著開啟 `http://localhost:8000`。

## 部署到 Cloudflare Pages

1. 將 repository 連接到 Cloudflare Pages。
2. Framework preset 選擇 `None`。
3. Build command 可留空，或填入 `npm run build`。
4. Build output directory 填入 `/`。
5. 部署完成後，Cloudflare Pages 會直接提供靜態網站。

## 資料更新

目前 `sources/` 內是範例 CSV。執行更新流程後，`scripts/update_data.py` 會把 CSV 轉成網站使用的 JSON，並覆蓋 `data/` 內的資料檔：

- `data/etf_list.json`
- `data/etf_holdings.json`
- `data/institution_trades.json`
- `data/price_history.json`

### ETF 持股資料備援更新

`scripts/update_holdings.py` 會更新 `data/etf_holdings.json`，第一版支援以下 ETF：

- `0050` 元大台灣50
- `0056` 元大高股息
- `006208` 富邦台50
- `00878` 國泰永續高股息
- `00919` 群益台灣精選高息

目前自動抓取來源保留為可擴充架構。若某一檔 ETF 自動抓取失敗，腳本會改讀 `sources/holdings/` 裡的 CSV；若 CSV 也不存在或格式無法辨識，會保留 `data/etf_holdings.json` 中該 ETF 的最近一次資料，不會清空原本持股。

手動 CSV 請放在：

```text
sources/holdings/
```

檔名請使用 ETF 代號加 `.csv`，目前支援：

```text
sources/holdings/0050.csv
sources/holdings/0056.csv
sources/holdings/006208.csv
sources/holdings/00878.csv
sources/holdings/00919.csv
```

CSV 欄位會盡量辨識常見名稱：

- 股票代號：`股票代號`、`stock_code`、`code`
- 股票名稱：`股票名稱`、`stock_name`、`name`
- 持股比例：`持股比例`、`weight`、`ratio`
- 持有股數：`持有股數`、`shares`
- 持有張數：`持有張數`、`lots`

如果 CSV 提供的是「持有張數」，腳本會自動換算成股數：

```text
shares = lots * 1000
```

手動執行：

```bash
python scripts/update_holdings.py
```

成功後會更新：

- `data/etf_holdings.json`：網站使用的 ETF 持股資料
- `data/holdings_update_report.json`：每檔 ETF 的更新狀態與備援結果

可以打開 `data/holdings_update_report.json` 檢查每檔 ETF 的狀態：

- `success`：自動更新成功
- `fallback_csv`：自動抓取失敗，已使用 CSV 備援
- `failed`：自動與 CSV 都失敗，已盡量保留最近一次資料
- `skipped`：保留欄位，目前預設為 0

網站首頁的資料狀態區塊會依報表顯示：

- `ETF 持股資料：已更新`
- `ETF 持股資料：部分使用 CSV 備援`
- `ETF 持股資料：使用最近一次資料`

### ETF 持股資料半自動轉檔

`scripts/convert_holdings.py` 是舊版批次轉檔工具，會讀取 `sources/holdings/` 內所有 CSV，統一輸出成 `data/etf_holdings.json`。若只是要更新目前網站使用的五檔 ETF，建議優先使用 `python scripts/update_holdings.py`，因為它會產生更新報表並保留失敗 ETF 的既有資料。

```bash
python scripts/convert_holdings.py
```

目前第一版支援 CSV。若下載的是 Excel，請先另存為 CSV 後再放入 `sources/holdings/`。

### 從 TWSE 自動更新法人資料

`scripts/update_all.py` 會從臺灣證券交易所 TWSE「三大法人買賣超日報」抓取最近一個有效交易日的資料。如果今天是假日或尚未收盤沒有資料，腳本會自動往前找最近一個有資料的交易日。

手動執行：

```bash
python scripts/update_all.py
```

成功後會更新：

- `data/institution_trades.json`：網站目前三大法人與投信買賣超頁面使用的相容格式
- `data/investment_trust_trades.json`：投信買賣超排行，包含買超、賣超與完整清單
- `data/last_updated.json`：更新時間、資料來源、交易日期與狀態
- `data/etf_holdings.json`：ETF 持股資料，若單檔失敗會改用 CSV 或最近一次資料
- `data/holdings_update_report.json`：ETF 持股更新報表

若 ETF 持股更新失敗，`update_all.py` 只會輸出錯誤訊息，不會讓整個法人資料更新流程中斷。

若單一天沒有 TWSE 法人資料，腳本會繼續往前查詢，不會因為假日或尚未收盤就中斷整個流程。若回溯期間內都沒有有效資料，會在 `data/last_updated.json` 寫入 `failed` 狀態與錯誤訊息。

### GitHub Actions 自動更新

`.github/workflows/update-data.yml` 會在週一到週五台灣時間下午 4:30 自動執行。GitHub Actions 使用 UTC，因此排程設定為 `30 8 * * 1-5`。

workflow 會執行：

```bash
pip install -r requirements.txt
python scripts/update_all.py
```

若 `data/*.json` 有變更，GitHub Actions 會自動 commit 並 push 回 `main`，commit message 為：

```text
chore: update market data
```

若沒有資料變更，workflow 會略過 commit，不會產生空 commit。

啟用前請確認 GitHub repository 的 Actions 權限允許 workflow 寫入：

1. 進入 GitHub repo 的 `Settings`。
2. 選擇 `Actions` → `General`。
3. 在 `Workflow permissions` 選擇 `Read and write permissions`。
4. 儲存後，合併此 workflow 到 `main` 即會依排程執行。

也可以手動執行：進入 GitHub repo 的 `Actions` → `Update market data` → `Run workflow`。

### Windows 更新方式

在 Windows 可直接執行根目錄的 `更新網站資料.bat`，內容會執行：

```bat
python scripts/update_data.py
```

成功後會顯示「更新完成。」。

### 手動更新方式

也可以在終端機執行：

```bash
python scripts/update_data.py
```

腳本只使用 Python 標準函式庫，不需要另外安裝套件。

### CSV 檔案說明

`etf_list.csv`：ETF 基本資料，會輸出成 `data/etf_list.json`。

`etf_holdings.csv`：ETF 持股資料，會輸出成 `data/etf_holdings.json`。

`institution_trades.csv`：法人與主動式 ETF 進出資料，使用 `recordType` 區分：

- `investment_trust`：投信買賣超排行，需填 `range`、`code`、`name`、`buySell`、`amount`
- `three_institutions`：三大法人每日買賣超，需填 `date`、`foreign`、`investmentTrust`、`dealer`、`total`
- `active_etf_flow`：主動式 ETF 進出，需填 `etfCode`、`etfName`、`stockCode`、`stockName`、`action`、`weightChange`、`sharesChange`

`price_history.csv`：ETF 淨值與價格歷史，需填 `date`、`etfCode`、`price`，可選填 `nav`。輸出時會保留網站目前使用的 `dates` 與 `series`，若有填 `nav` 也會另外輸出 `navSeries`。
