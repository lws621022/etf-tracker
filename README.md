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
│  ├─ last_updated.json
│  └─ price_history.json
├─ sources/
│  ├─ etf_list.csv
│  ├─ etf_holdings.csv
│  ├─ institution_trades.csv
│  └─ price_history.csv
├─ scripts/
│  ├─ update_all.py
│  └─ update_data.py
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

若單一天沒有資料，腳本會繼續往前查詢，不會因為假日或尚未收盤就中斷整個流程。若回溯期間內都沒有有效資料，會在 `data/last_updated.json` 寫入 `failed` 狀態與錯誤訊息。

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
