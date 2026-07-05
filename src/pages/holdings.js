export function renderHoldingsPage(container, data) {
  const topHoldings = [...data.holdings].sort((a, b) => b.weight - a.weight).slice(0, 12);

  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">Holdings</p>
        <h2>每日焦點</h2>
        <p>以範例資料彙整權重較高、ETF 重複持有的關注標的。</p>
      </div>
    </section>
    <section class="panel">
      <div class="table-wrap flush">
        <table>
          <thead><tr><th>股票</th><th>ETF</th><th>持股比例</th><th>持有張數</th></tr></thead>
          <tbody>
            ${topHoldings.map((item) => `
              <tr>
                <td>${item.stockCode} ${item.stockName}</td>
                <td>${item.etfCode} ${item.etfName}</td>
                <td>${item.weight}%</td>
                <td>${item.shares.toLocaleString("zh-TW")}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}
