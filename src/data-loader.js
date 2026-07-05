const DATA_FILES = {
  etfs: "data/etf_list.json",
  holdings: "data/etf_holdings.json",
  trades: "data/institution_trades.json",
  prices: "data/price_history.json"
};

async function fetchJson(path) {
  const response = await fetch(path);

  if (!response.ok) {
    throw new Error(`無法載入資料：${path}`);
  }

  return response.json();
}

function normalizeHolding(holding) {
  return {
    ...holding,
    etfCode: holding.etfCode || holding.etf_code || "",
    etfName: holding.etfName || holding.etf_name || "",
    stockCode: holding.stockCode || holding.stock_code || "",
    stockName: holding.stockName || holding.stock_name || "",
    weight: Number(holding.weight) || 0,
    shares: Number(holding.shares) || 0
  };
}

export async function loadDashboardData() {
  const [etfs, rawHoldings, trades, prices] = await Promise.all([
    fetchJson(DATA_FILES.etfs),
    fetchJson(DATA_FILES.holdings),
    fetchJson(DATA_FILES.trades),
    fetchJson(DATA_FILES.prices)
  ]);

  const holdings = rawHoldings.map(normalizeHolding);

  return { etfs, holdings, trades, prices };
}

export function findEtf(data, code) {
  return data.etfs.find((etf) => etf.code === code);
}
