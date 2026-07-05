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
│  └─ price_history.json
├─ scripts/
│  └─ update_data.py
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

目前 `data/` 內是範例資料。未來可擴充 `scripts/update_data.py`，把正式資料來源轉換成相同 JSON 格式後覆蓋：

- `data/etf_list.json`
- `data/etf_holdings.json`
- `data/institution_trades.json`
- `data/price_history.json`
