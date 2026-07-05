function normalizeText(value) {
  return value.trim().toLowerCase();
}

function readCellValue(row, index) {
  const text = normalizeText(row.cells[index]?.textContent || "");
  const numericText = text
    .replace(/nt\$/gi, "")
    .replace(/[,%$\s]/g, "")
    .replace(/億|百萬|張|歲/g, "");

  if (/^[+-]?\d+(\.\d+)?$/.test(numericText)) {
    return Number.parseFloat(numericText);
  }

  return text;
}

function sortTable(table, columnIndex, direction) {
  const tbody = table.tBodies[0];
  const rows = [...tbody.rows];

  rows.sort((rowA, rowB) => {
    const valueA = readCellValue(rowA, columnIndex);
    const valueB = readCellValue(rowB, columnIndex);
    const result = typeof valueA === "number" && typeof valueB === "number"
      ? valueA - valueB
      : String(valueA).localeCompare(String(valueB), "zh-Hant");

    return direction === "asc" ? result : -result;
  });

  rows.forEach((row) => tbody.appendChild(row));
}

function filterTable(table, query) {
  const normalizedQuery = normalizeText(query);
  [...table.tBodies[0].rows].forEach((row) => {
    const rowText = normalizeText(row.textContent || "");
    row.hidden = normalizedQuery !== "" && !rowText.includes(normalizedQuery);
  });
}

export function enhanceDataTables(root = document) {
  root.querySelectorAll(".table-wrap table").forEach((table) => {
    if (table.dataset.enhanced === "true") {
      return;
    }

    table.dataset.enhanced = "true";
    table.classList.add("data-table");

    const tableWrap = table.closest(".table-wrap");
    const toolbar = document.createElement("div");
    toolbar.className = "table-toolbar";
    toolbar.innerHTML = `
      <label class="table-search">
        <span>搜尋</span>
        <input type="search" placeholder="輸入關鍵字">
      </label>
    `;

    tableWrap.before(toolbar);
    const input = toolbar.querySelector("input");
    input.addEventListener("input", () => filterTable(table, input.value));

    table.querySelectorAll("thead th").forEach((header, index) => {
      header.tabIndex = 0;
      header.dataset.sort = "none";
      header.setAttribute("role", "button");
      header.setAttribute("aria-sort", "none");
      header.title = "點擊排序";

      const toggleSort = () => {
        const nextDirection = header.dataset.sort === "asc" ? "desc" : "asc";
        table.querySelectorAll("thead th").forEach((item) => {
          item.dataset.sort = "none";
          item.setAttribute("aria-sort", "none");
        });
        header.dataset.sort = nextDirection;
        header.setAttribute("aria-sort", nextDirection === "asc" ? "ascending" : "descending");
        sortTable(table, index, nextDirection);
        filterTable(table, input.value);
      };

      header.addEventListener("click", toggleSort);
      header.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          toggleSort();
        }
      });
    });
  });
}
