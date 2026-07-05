import { loadDashboardData } from "./data-loader.js";
import { renderActiveEtfPage } from "./pages/active-etf.js";
import { renderOverviewPage } from "./pages/overview.js";
import { renderInvestmentTrustPage, renderThreeInstitutionsPage } from "./pages/institutions.js";
import { renderStockSearchPage } from "./pages/stock-search.js";
import { renderPerformancePage } from "./pages/performance.js";
import { renderHoldingsPage } from "./pages/holdings.js";
import { renderEventsPage } from "./pages/events.js";
import { renderRetirementPage } from "./pages/retirement.js";

const routes = [
  { id: "active-etf", label: "主動式 ETF 進出", render: renderActiveEtfPage },
  { id: "overview", label: "ETF 總覽", render: renderOverviewPage },
  { id: "investment-trust", label: "投信買賣超", render: renderInvestmentTrustPage },
  { id: "three-institutions", label: "三大法人", render: renderThreeInstitutionsPage },
  { id: "stock-search", label: "用股票查 ETF", render: renderStockSearchPage },
  { id: "performance", label: "績效圖", render: renderPerformancePage },
  { id: "daily-focus", label: "每日焦點", render: renderHoldingsPage },
  { id: "events", label: "事件", render: renderEventsPage },
  { id: "retirement", label: "退休計算機", render: renderRetirementPage }
];

const app = document.querySelector("#app");
const nav = document.querySelector("#tab-nav");
let dashboardData = null;

function getCurrentRoute() {
  const hash = window.location.hash.replace("#", "");
  return routes.find((route) => route.id === hash) || routes[0];
}

function renderNav(activeRouteId) {
  nav.innerHTML = routes.map((route) => `
    <a class="${route.id === activeRouteId ? "active" : ""}" href="#${route.id}">${route.label}</a>
  `).join("");
}

function renderLoading() {
  app.innerHTML = `
    <section class="loading-panel">
      <span class="spinner" aria-hidden="true"></span>
      <div>
        <h2>資料載入中</h2>
        <p>正在整理 ETF、法人籌碼與價格歷史資料。</p>
      </div>
    </section>
  `;
}

function renderError(error) {
  app.innerHTML = `
    <section class="error-panel">
      <span class="status-icon" aria-hidden="true">!</span>
      <div>
        <h2>資料載入失敗</h2>
        <p>${error.message}</p>
        <p>請確認使用本機伺服器開啟網站，而不是直接用檔案模式開啟 index.html。</p>
        <button class="primary-action" type="button" id="retry-load">重新載入</button>
      </div>
    </section>
  `;

  app.querySelector("#retry-load").addEventListener("click", bootstrap);
}

function renderRoute() {
  const route = getCurrentRoute();
  renderNav(route.id);
  app.innerHTML = "";
  route.render(app, dashboardData);
}

async function bootstrap() {
  renderNav(getCurrentRoute().id);
  renderLoading();

  try {
    dashboardData = await loadDashboardData();
    renderRoute();
    window.addEventListener("hashchange", renderRoute);
  } catch (error) {
    renderError(error);
  }
}

bootstrap();
