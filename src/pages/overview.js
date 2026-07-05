const formatNumber = new Intl.NumberFormat("zh-TW");

function renderCards(etfs) {
  return etfs.map((etf) => `
    <article class="etf-card">
      <div class="card-topline">
        <span class="code-pill">${etf.code}</span>
        <span class="tag">${etf.type}</span>
      </div>
      <h3>${etf.name}</h3>
      <p>${etf.issuer}｜${etf.category}</p>
      <dl class="metric-grid mini">
        <div><dt>規模</dt><dd>${formatNumber.format(etf.aum)} 億</dd></div>
        <div><dt>費用率</dt><dd>${etf.expenseRatio}%</dd></div>
        <div><dt>殖利率</dt><dd>${etf.yield}%</dd></div>
        <div><dt>漲跌</dt><dd class="${etf.changePct >= 0 ? "up" : "down"}">${etf.changePct}%</dd></div>
      </dl>
    </article>
  `).join("");
}

function renderTable(etfs) {
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>代號</th>
            <th>ETF 名稱</th>
            <th>類型</th>
            <th>發行商</th>
            <th>價格</th>
            <th>規模</th>
            <th>費用率</th>
            <th>殖利率</th>
          </tr>
        </thead>
        <tbody>
          ${etfs.map((etf) => `
            <tr>
              <td>${etf.code}</td>
              <td>${etf.name}</td>
              <td>${etf.type}</td>
              <td>${etf.issuer}</td>
              <td>${etf.price}</td>
              <td>${formatNumber.format(etf.aum)} 億</td>
              <td>${etf.expenseRatio}%</td>
              <td>${etf.yield}%</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

export function renderOverviewPage(container, data) {
  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">ETF Overview</p>
        <h2>ETF 總覽</h2>
        <p>以卡片或列表快速比較 ETF 類型、費用率、規模與殖利率。</p>
      </div>
      <div class="segmented-control" role="group" aria-label="顯示模式">
        <button class="active" type="button" data-view="cards">卡片</button>
        <button type="button" data-view="table">列表</button>
      </div>
    </section>
    <section id="overview-content" class="card-grid">${renderCards(data.etfs)}</section>
  `;

  const content = container.querySelector("#overview-content");
  const buttons = container.querySelectorAll("[data-view]");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      buttons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");

      if (button.dataset.view === "cards") {
        content.className = "card-grid";
        content.innerHTML = renderCards(data.etfs);
        return;
      }

      content.className = "panel";
      content.innerHTML = renderTable(data.etfs);
    });
  });
}
