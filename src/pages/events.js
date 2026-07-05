export function renderEventsPage(container) {
  const events = [
    { date: "2026-07-05", title: "主動式 ETF 持股調整觀察", note: "追蹤新增、加碼、減碼標的，觀察主動經理人布局方向。" },
    { date: "2026-07-10", title: "高股息 ETF 除息週", note: "留意配息前後價格波動與成分股換股影響。" },
    { date: "2026-07-15", title: "台股 ETF 規模月報", note: "比較資金流入、規模變化與成交量是否同步升溫。" }
  ];

  container.innerHTML = `
    <section class="page-heading">
      <div>
        <p class="eyebrow">Events</p>
        <h2>事件</h2>
        <p>整理 ETF 追蹤時值得留意的換股、除息與資料更新節點。</p>
      </div>
    </section>
    <section class="timeline panel">
      ${events.map((event) => `
        <article class="timeline-item">
          <time>${event.date}</time>
          <div>
            <h3>${event.title}</h3>
            <p>${event.note}</p>
          </div>
        </article>
      `).join("")}
    </section>
  `;
}
