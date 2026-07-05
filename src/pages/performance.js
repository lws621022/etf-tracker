import { renderLineChart, toPerformanceSeries } from "../charts.js";

function renderPicker(etfs) {
  return etfs.map((etf, index) => `
    <label class="check-item">
      <input type="checkbox" value="${etf.code}" ${index < 4 ? "checked" : ""}>
      <span>${etf.code} ${etf.name}</span>
    </label>
  `).join("");
}

export function renderPerformancePage(container, data) {
  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">Performance</p>
        <h2>績效圖</h2>
        <p>最多勾選 8 檔 ETF，比較範例價格區間內的報酬走勢。</p>
      </div>
    </section>
    <section class="panel chart-layout">
      <div class="selector-list" id="performance-picker">${renderPicker(data.etfs)}</div>
      <div class="chart-card"><canvas id="performance-chart"></canvas></div>
    </section>
  `;

  const picker = container.querySelector("#performance-picker");
  const inputs = [...picker.querySelectorAll("input")];

  const update = () => {
    const selected = inputs.filter((input) => input.checked).map((input) => input.value).slice(0, 8);

    inputs.forEach((input) => {
      input.disabled = !input.checked && selected.length >= 8;
    });

    const datasets = selected.map((code) => {
      const etf = data.etfs.find((item) => item.code === code);
      return {
        label: `${code} ${etf?.name || ""}`,
        data: toPerformanceSeries(data.prices.series[code] || [])
      };
    });

    renderLineChart("performance-chart", data.prices.dates, datasets, {
      yTickFormatter: (value) => `${value}%`,
      tooltipCallbacks: {
        label: (context) => `${context.dataset.label}: ${context.parsed.y}%`
      }
    });
  };

  picker.addEventListener("change", update);
  update();
}
