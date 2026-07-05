import { enhanceDataTables } from "../table-utils.js";

export function renderActiveEtfPage(container, data) {
  const activeEtfs = data.etfs.filter((etf) => etf.isActive);

  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">Active ETF Flow</p>
        <h2>主動式 ETF 進出</h2>
        <p>追蹤主動式 ETF 範例持股的新增、加碼與減碼動作。</p>
      </div>
    </section>
    <section class="card-grid compact-cards">
      ${activeEtfs.map((etf) => `
        <article class="etf-card">
          <div class="card-topline"><span class="code-pill">${etf.code}</span><span class="tag">主動式</span></div>
          <h3>${etf.name}</h3>
          <p>${etf.issuer}｜規模 <strong class="num-strong">${etf.aum}</strong> 億｜費用率 <strong class="num-strong">${etf.expenseRatio}%</strong></p>
        </article>
      `).join("")}
    </section>
    <section class="panel">
      <div class="table-wrap flush">
        <table>
          <thead><tr><th>ETF</th><th>股票</th><th>動作</th><th>權重變化</th><th>張數變化</th></tr></thead>
          <tbody>
            ${data.trades.activeEtfFlows.map((item) => `
              <tr>
                <td><strong>${item.etfCode}</strong> ${item.etfName}</td>
                <td><strong>${item.stockCode}</strong> ${item.stockName}</td>
                <td><span class="tag ${item.action === "減碼" ? "danger" : "success"}">${item.action}</span></td>
                <td class="${item.weightChange >= 0 ? "up" : "down"}">${item.weightChange}%</td>
                <td class="${item.sharesChange >= 0 ? "up" : "down"}">${item.sharesChange.toLocaleString("zh-TW")}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;

  enhanceDataTables(container);
}
