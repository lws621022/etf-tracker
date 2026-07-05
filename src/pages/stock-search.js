import { enhanceDataTables } from "../table-utils.js";

function sortByWeight(items) {
  return [...items].sort((a, b) => b.weight - a.weight);
}

function matchesStock(item, query) {
  const normalizedQuery = query.trim().toLowerCase();

  return item.stockCode.toLowerCase().includes(normalizedQuery)
    || item.stockName.toLowerCase().includes(normalizedQuery);
}

function renderResults(results, hasQuery) {
  if (!hasQuery) {
    return `<div class="empty-state">請輸入股票代號或名稱開始查詢。</div>`;
  }

  if (!results.length) {
    return `<div class="empty-state">查無持有此股票的 ETF</div>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ETF 代號</th>
            <th>ETF 名稱</th>
            <th>股票代號</th>
            <th>股票名稱</th>
            <th>持股比例</th>
            <th>持有張數</th>
          </tr>
        </thead>
        <tbody>
          ${results.map((item) => `
            <tr>
              <td><strong>${item.etfCode}</strong></td>
              <td><button class="text-link etf-detail-link" type="button" data-etf-code="${item.etfCode}">${item.etfName}</button></td>
              <td><strong>${item.stockCode}</strong></td>
              <td>${item.stockName}</td>
              <td class="num-strong">${item.weight}%</td>
              <td>${item.shares.toLocaleString("zh-TW")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderEtfDetail(holdings, etfCode) {
  if (!etfCode) {
    return "";
  }

  const rows = sortByWeight(holdings.filter((item) => item.etfCode === etfCode));
  const etfName = rows[0]?.etfName || etfCode;

  if (!rows.length) {
    return "";
  }

  return `
    <section class="panel etf-detail-panel">
      <div class="detail-heading">
        <div>
          <p class="eyebrow">ETF Holdings</p>
          <h3>${etfCode} ${etfName} 持股明細</h3>
        </div>
        <span class="tag">${rows.length} 檔持股</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>股票代號</th>
              <th>股票名稱</th>
              <th>持股比例</th>
              <th>持有張數</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map((item) => `
              <tr>
                <td><strong>${item.stockCode}</strong></td>
                <td>${item.stockName}</td>
                <td class="num-strong">${item.weight}%</td>
                <td>${item.shares.toLocaleString("zh-TW")}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

export function renderStockSearchPage(container, data) {
  let selectedEtfCode = "";

  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">Reverse Lookup</p>
        <h2>用股票查 ETF</h2>
        <p>輸入股票代號或名稱，找出哪些 ETF 持有該股票。</p>
      </div>
    </section>
    <section class="panel search-panel">
      <label class="field compact" for="stock-query">
        <span>股票代號或名稱</span>
        <input id="stock-query" type="search" placeholder="例如：2330、台積電、廣達" autocomplete="off">
      </label>
      <div id="stock-results" class="results-block"></div>
    </section>
    <div id="etf-detail"></div>
  `;

  const input = container.querySelector("#stock-query");
  const results = container.querySelector("#stock-results");
  const detail = container.querySelector("#etf-detail");

  const renderDetail = () => {
    detail.innerHTML = renderEtfDetail(data.holdings, selectedEtfCode);
    enhanceDataTables(detail);
  };

  const update = () => {
    const query = input.value.trim();
    const matches = query
      ? sortByWeight(data.holdings.filter((item) => matchesStock(item, query)))
      : [];

    results.innerHTML = renderResults(matches, query !== "");
    selectedEtfCode = matches.some((item) => item.etfCode === selectedEtfCode) ? selectedEtfCode : "";
    renderDetail();
    enhanceDataTables(results);
  };

  results.addEventListener("click", (event) => {
    const detailButton = event.target.closest("[data-etf-code]");

    if (!detailButton) {
      return;
    }

    selectedEtfCode = detailButton.dataset.etfCode;
    renderDetail();
    detail.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  input.addEventListener("input", update);
  update();
}
