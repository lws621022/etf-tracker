const defaultColors = ["#0f8b6f", "#2563eb", "#d97706", "#7c3aed", "#dc2626", "#0891b2", "#65a30d", "#be185d"];
const chartRegistry = new Map();

function destroyChart(canvasId) {
  const currentChart = chartRegistry.get(canvasId);

  if (currentChart) {
    currentChart.destroy();
    chartRegistry.delete(canvasId);
  }
}

export function renderLineChart(canvasId, labels, datasets, options = {}) {
  const canvas = document.getElementById(canvasId);

  if (!canvas || !window.Chart) {
    return;
  }

  destroyChart(canvasId);

  const chart = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: datasets.map((dataset, index) => ({
        borderColor: dataset.color || defaultColors[index % defaultColors.length],
        backgroundColor: dataset.color || defaultColors[index % defaultColors.length],
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.28,
        fill: false,
        ...dataset
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "bottom" },
        tooltip: { callbacks: options.tooltipCallbacks || {} }
      },
      scales: {
        y: {
          ticks: {
            callback: options.yTickFormatter || ((value) => value)
          }
        }
      }
    }
  });

  chartRegistry.set(canvasId, chart);
}

export function toPerformanceSeries(values) {
  const firstValue = values[0] || 1;
  return values.map((value) => Number((((value - firstValue) / firstValue) * 100).toFixed(2)));
}
