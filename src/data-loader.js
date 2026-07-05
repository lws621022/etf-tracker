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

export async function loadDashboardData() {
  const [etfs, holdings, trades, prices] = await Promise.all([
    fetchJson(DATA_FILES.etfs),
    fetchJson(DATA_FILES.holdings),
    fetchJson(DATA_FILES.trades),
    fetchJson(DATA_FILES.prices)
  ]);

  return { etfs, holdings, trades, prices };
}

export function findEtf(data, code) {
  return data.etfs.find((etf) => etf.code === code);
}
