function renderResults(results) {
  if (!results.length) {
    return `<div class="empty-state">查無符合的 ETF 持股，請改用股票代號或名稱搜尋。</div>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>股票</th>
            <th>ETF 代號</th>
            <th>ETF 名稱</th>
            <th>持股比例</th>
            <th>持有張數</th>
          </tr>
        </thead>
        <tbody>
          ${results.map((item) => `
            <tr>
              <td>${item.stockCode} ${item.stockName}</td>
              <td>${item.etfCode}</td>
              <td>${item.etfName}</td>
              <td>${item.weight}%</td>
              <td>${item.shares.toLocaleString("zh-TW")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

export function renderStockSearchPage(container, data) {
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
        <input id="stock-query" type="search" placeholder="例如：2330、台積電、廣達">
      </label>
      <div id="stock-results" class="results-block"></div>
    </section>
  `;

  const input = container.querySelector("#stock-query");
  const results = container.querySelector("#stock-results");

  const update = () => {
    const query = input.value.trim().toLowerCase();
    const matches = query
      ? data.holdings.filter((item) => item.stockCode.toLowerCase().includes(query) || item.stockName.toLowerCase().includes(query))
      : data.holdings.slice(0, 8);

    results.innerHTML = renderResults(matches);
  };

  input.addEventListener("input", update);
  update();
}
