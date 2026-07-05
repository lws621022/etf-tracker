const rangeLabels = {
  day: "當日",
  "5d": "5日",
  "20d": "20日",
  "60d": "60日"
};

function rankingTable(items, type) {
  const sorted = [...items]
    .filter((item) => type === "buy" ? item.buySell > 0 : item.buySell < 0)
    .sort((a, b) => type === "buy" ? b.buySell - a.buySell : a.buySell - b.buySell);

  return `
    <div class="panel">
      <h3>${type === "buy" ? "買超排行" : "賣超排行"}</h3>
      <div class="table-wrap flush">
        <table>
          <thead><tr><th>股票</th><th>張數</th><th>金額</th></tr></thead>
          <tbody>
            ${sorted.map((item) => `
              <tr>
                <td>${item.code} ${item.name}</td>
                <td class="${item.buySell >= 0 ? "up" : "down"}">${item.buySell.toLocaleString("zh-TW")}</td>
                <td>${item.amount.toLocaleString("zh-TW")} 百萬</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

export function renderInvestmentTrustPage(container, data) {
  const ranges = Object.keys(data.trades.investmentTrust);

  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">Investment Trust</p>
        <h2>投信買賣超</h2>
        <p>切換不同期間，查看投信資金偏好的買超與賣超標的。</p>
      </div>
      <div class="segmented-control" role="group" aria-label="期間切換">
        ${ranges.map((range, index) => `<button class="${index === 0 ? "active" : ""}" type="button" data-range="${range}">${rangeLabels[range]}</button>`).join("")}
      </div>
    </section>
    <section id="trust-rankings" class="two-column"></section>
  `;

  const rankings = container.querySelector("#trust-rankings");
  const buttons = container.querySelectorAll("[data-range]");

  const update = (range) => {
    const items = data.trades.investmentTrust[range];
    rankings.innerHTML = rankingTable(items, "buy") + rankingTable(items, "sell");
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      buttons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      update(button.dataset.range);
    });
  });

  update(ranges[0]);
}

export function renderThreeInstitutionsPage(container, data) {
  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">Market Chips</p>
        <h2>三大法人</h2>
        <p>以億元為單位，追蹤外資、投信與自營商每日買賣超。</p>
      </div>
    </section>
    <section class="panel">
      <div class="table-wrap flush">
        <table>
          <thead><tr><th>日期</th><th>外資</th><th>投信</th><th>自營商</th><th>合計</th></tr></thead>
          <tbody>
            ${data.trades.threeInstitutions.map((item) => `
              <tr>
                <td>${item.date}</td>
                <td class="${item.foreign >= 0 ? "up" : "down"}">${item.foreign}</td>
                <td class="${item.investmentTrust >= 0 ? "up" : "down"}">${item.investmentTrust}</td>
                <td class="${item.dealer >= 0 ? "up" : "down"}">${item.dealer}</td>
                <td class="${item.total >= 0 ? "up" : "down"}">${item.total}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}
