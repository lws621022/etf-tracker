import { renderLineChart, toPerformanceSeries } from "../charts.js";
import { enhanceDataTables } from "../table-utils.js";

const rangeOptions = [
  { key: "1m", label: "1個月", months: 1 },
  { key: "3m", label: "3個月", months: 3 },
  { key: "6m", label: "6個月", months: 6 },
  { key: "1y", label: "1年", months: 12 },
  { key: "ytd", label: "今年以來" },
  { key: "all", label: "全部" }
];

const tablePeriods = [
  { key: "1m", label: "1月報酬", months: 1 },
  { key: "3m", label: "3月報酬", months: 3 },
  { key: "6m", label: "6月報酬", months: 6 },
  { key: "1y", label: "1年報酬", months: 12 }
];

function addMonths(date, months) {
  const next = new Date(date);
  next.setMonth(next.getMonth() + months);
  return next;
}

function formatReturn(value) {
  if (value === null || Number.isNaN(value)) {
    return "—";
  }

  const formatted = `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
  return `<span class="${value >= 0 ? "up" : "down"}">${formatted}</span>`;
}

function getLastDate(dates) {
  return dates.length ? new Date(dates[dates.length - 1]) : null;
}

function getRangeStartIndex(dates, rangeKey) {
  if (!dates.length || rangeKey === "all") {
    return 0;
  }

  const lastDate = getLastDate(dates);
  let startDate = null;

  if (rangeKey === "ytd") {
    startDate = new Date(lastDate.getFullYear(), 0, 1);
  } else {
    const range = rangeOptions.find((item) => item.key === rangeKey);
    startDate = addMonths(lastDate, -range.months);
  }

  const index = dates.findIndex((date) => new Date(date) >= startDate);
  return index === -1 ? 0 : index;
}

function slicePrices(prices, startIndex, endIndex) {
  return prices.slice(startIndex, endIndex + 1);
}

function calculateReturn(values, dates, months) {
  if (!values.length || !dates.length) {
    return null;
  }

  const latestIndex = Math.min(values.length, dates.length) - 1;
  const latestPrice = values[latestIndex];
  const targetDate = addMonths(new Date(dates[latestIndex]), -months);
  let baseIndex = -1;

  for (let index = latestIndex; index >= 0; index -= 1) {
    if (new Date(dates[index]) <= targetDate) {
      baseIndex = index;
      break;
    }
  }

  if (baseIndex === -1 || !values[baseIndex] || !latestPrice) {
    return null;
  }

  return Number((((latestPrice - values[baseIndex]) / values[baseIndex]) * 100).toFixed(2));
}

function renderPicker(etfs) {
  return etfs.map((etf, index) => `
    <label class="check-item">
      <input type="checkbox" value="${etf.code}" ${index < 4 ? "checked" : ""}>
      <span>${etf.code} ${etf.name}</span>
    </label>
  `).join("");
}

function renderRangeControls(activeRange) {
  return `
    <div class="segmented-control" role="group" aria-label="績效期間切換">
      ${rangeOptions.map((range) => `
        <button class="${range.key === activeRange ? "active" : ""}" type="button" data-range="${range.key}">${range.label}</button>
      `).join("")}
    </div>
  `;
}

function renderReturnTable(selectedCodes, etfs, prices) {
  if (!selectedCodes.length) {
    return `<div class="empty-state">請至少勾選 1 檔 ETF。</div>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ETF 代號</th>
            <th>ETF 名稱</th>
            ${tablePeriods.map((period) => `<th>${period.label}</th>`).join("")}
          </tr>
        </thead>
        <tbody>
          ${selectedCodes.map((code) => {
            const etf = etfs.find((item) => item.code === code);
            const values = prices.series[code] || [];

            return `
              <tr>
                <td><strong>${code}</strong></td>
                <td>${etf?.name || "—"}</td>
                ${tablePeriods.map((period) => `<td>${formatReturn(calculateReturn(values, prices.dates, period.months))}</td>`).join("")}
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    </div>
  `;
}

export function renderPerformancePage(container, data) {
  let activeRange = "all";

  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">Performance</p>
        <h2>績效圖</h2>
        <p>最多勾選 8 檔 ETF，比較不同期間的累積報酬率。</p>
      </div>
      <div id="performance-ranges">${renderRangeControls(activeRange)}</div>
    </section>
    <section class="panel chart-layout">
      <div class="selector-list" id="performance-picker">${renderPicker(data.etfs)}</div>
      <div class="chart-card"><canvas id="performance-chart"></canvas></div>
    </section>
    <section class="panel" id="performance-table"></section>
  `;

  const rangeControls = container.querySelector("#performance-ranges");
  const picker = container.querySelector("#performance-picker");
  const tableContainer = container.querySelector("#performance-table");
  const inputs = [...picker.querySelectorAll("input")];

  const getSelectedCodes = () => inputs
    .filter((input) => input.checked)
    .map((input) => input.value)
    .slice(0, 8);

  const update = () => {
    const selectedCodes = getSelectedCodes();
    const startIndex = getRangeStartIndex(data.prices.dates, activeRange);
    const labels = data.prices.dates.slice(startIndex);

    inputs.forEach((input) => {
      input.disabled = !input.checked && selectedCodes.length >= 8;
    });

    const datasets = selectedCodes.map((code) => {
      const etf = data.etfs.find((item) => item.code === code);
      const values = data.prices.series[code] || [];
      const rangeValues = slicePrices(values, startIndex, data.prices.dates.length - 1);

      return {
        label: `${code} ${etf?.name || ""}`,
        data: toPerformanceSeries(rangeValues)
      };
    });

    renderLineChart("performance-chart", labels, datasets, {
      yTickFormatter: (value) => `${value}%`,
      tooltipCallbacks: {
        label: (context) => `${context.dataset.label}: ${context.parsed.y}%`
      }
    });

    tableContainer.innerHTML = renderReturnTable(selectedCodes, data.etfs, data.prices);
    enhanceDataTables(tableContainer);
  };

  picker.addEventListener("change", update);
  rangeControls.addEventListener("click", (event) => {
    const button = event.target.closest("[data-range]");

    if (!button) {
      return;
    }

    activeRange = button.dataset.range;
    rangeControls.innerHTML = renderRangeControls(activeRange);
    update();
  });

  update();
}
