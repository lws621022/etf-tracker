import { renderLineChart } from "../charts.js";
import { enhanceDataTables } from "../table-utils.js";

const currency = new Intl.NumberFormat("zh-TW", {
  style: "currency",
  currency: "TWD",
  maximumFractionDigits: 0
});

function projectRetirement(currentAge, retirementAge, monthlyInvestment, annualReturn) {
  const years = Math.max(0, retirementAge - currentAge);
  const months = years * 12;
  const monthlyRate = Math.pow(1 + annualReturn / 100, 1 / 12) - 1;
  const rows = [];
  let balance = 0;

  for (let month = 1; month <= months; month += 1) {
    balance = balance * (1 + monthlyRate) + monthlyInvestment;

    if (month % 12 === 0) {
      const age = currentAge + month / 12;
      const contribution = monthlyInvestment * month;
      rows.push({ age, contribution, balance, gain: balance - contribution });
    }
  }

  return { years, rows, balance, contribution: monthlyInvestment * months };
}

function renderRows(rows) {
  return rows.map((row) => `
    <tr>
      <td>${row.age} 歲</td>
      <td>${currency.format(row.contribution)}</td>
      <td class="num-strong">${currency.format(row.balance)}</td>
      <td class="${row.gain >= 0 ? "up" : "down"}">${currency.format(row.gain)}</td>
    </tr>
  `).join("");
}

export function renderRetirementPage(container) {
  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">Retirement Calculator</p>
        <h2>退休計算機</h2>
        <p>用目前年齡、退休年齡、每月投入與年化報酬率估算退休資產。</p>
      </div>
    </section>
    <section class="calculator-layout">
      <form class="panel form-grid" id="retirement-form">
        <label class="field"><span>目前年齡</span><input id="current-age" type="number" min="0" max="100" value="35"></label>
        <label class="field"><span>退休年齡</span><input id="retirement-age" type="number" min="1" max="100" value="65"></label>
        <label class="field"><span>每月投入金額</span><input id="monthly-investment" type="number" min="0" step="1000" value="10000"></label>
        <label class="field"><span>年化報酬率</span><input id="annual-return" type="number" min="-50" max="100" step="0.1" value="7"></label>
      </form>
      <section class="panel summary-panel">
        <span>退休時可能累積資產</span>
        <strong id="retirement-total">NT$0</strong>
        <p id="retirement-summary"></p>
      </section>
    </section>
    <section class="panel chart-layout single">
      <div class="chart-card"><canvas id="retirement-chart"></canvas></div>
    </section>
    <section class="panel">
      <div class="table-wrap flush">
        <table>
          <thead><tr><th>年齡</th><th>累積投入</th><th>預估資產</th><th>投資收益</th></tr></thead>
          <tbody id="retirement-table"></tbody>
        </table>
      </div>
    </section>
  `;

  const form = container.querySelector("#retirement-form");
  const total = container.querySelector("#retirement-total");
  const summary = container.querySelector("#retirement-summary");
  const table = container.querySelector("#retirement-table");

  const read = (id) => Number.parseFloat(container.querySelector(`#${id}`).value) || 0;

  const update = () => {
    const currentAge = read("current-age");
    const retirementAge = read("retirement-age");
    const monthlyInvestment = read("monthly-investment");
    const annualReturn = read("annual-return");
    const result = projectRetirement(currentAge, retirementAge, monthlyInvestment, annualReturn);

    total.textContent = currency.format(result.balance);
    summary.textContent = `投資 ${result.years} 年，累積投入 ${currency.format(result.contribution)}。`;
    table.innerHTML = renderRows(result.rows);

    renderLineChart("retirement-chart", result.rows.map((row) => `${row.age}歲`), [
      { label: "累積投入", data: result.rows.map((row) => Math.round(row.contribution)) },
      { label: "預估資產", data: result.rows.map((row) => Math.round(row.balance)) }
    ], {
      yTickFormatter: (value) => currency.format(value)
    });
  };

  form.addEventListener("input", update);
  form.addEventListener("submit", (event) => event.preventDefault());
  update();
  enhanceDataTables(container);
}
