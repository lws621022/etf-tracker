const form = document.querySelector("#calculator-form");
const monthlyInput = document.querySelector("#monthly-investment");
const yearsInput = document.querySelector("#investment-years");
const returnInput = document.querySelector("#annual-return");
const totalContributionEl = document.querySelector("#total-contribution");
const futureValueEl = document.querySelector("#future-value");
const investmentGainEl = document.querySelector("#investment-gain");
const yearlyResultsEl = document.querySelector("#yearly-results");
const summaryTextEl = document.querySelector("#summary-text");
const presetButtons = document.querySelectorAll(".preset-button");

const currencyFormatter = new Intl.NumberFormat("zh-TW", {
  style: "currency",
  currency: "TWD",
  maximumFractionDigits: 0
});

const percentFormatter = new Intl.NumberFormat("zh-TW", {
  maximumFractionDigits: 1
});

function getNumberValue(input) {
  return Number.parseFloat(input.value) || 0;
}

function formatCurrency(value) {
  return currencyFormatter.format(Math.round(value));
}

function calculateProjection(monthlyInvestment, years, annualReturnPercent) {
  const totalMonths = years * 12;
  const monthlyRate = Math.pow(1 + annualReturnPercent / 100, 1 / 12) - 1;
  const yearlyRows = [];
  let balance = 0;

  for (let month = 1; month <= totalMonths; month += 1) {
    balance = balance * (1 + monthlyRate) + monthlyInvestment;

    if (month % 12 === 0) {
      const year = month / 12;
      const contribution = monthlyInvestment * month;
      yearlyRows.push({
        year,
        contribution,
        balance,
        gain: balance - contribution
      });
    }
  }

  const totalContribution = monthlyInvestment * totalMonths;

  return {
    totalContribution,
    futureValue: balance,
    investmentGain: balance - totalContribution,
    yearlyRows
  };
}

function renderYearlyRows(rows) {
  yearlyResultsEl.innerHTML = rows
    .map((row) => `
      <tr>
        <td>第 ${row.year} 年</td>
        <td>${formatCurrency(row.contribution)}</td>
        <td>${formatCurrency(row.balance)}</td>
        <td>${formatCurrency(row.gain)}</td>
      </tr>
    `)
    .join("");
}

function updateCalculator() {
  const monthlyInvestment = Math.max(0, getNumberValue(monthlyInput));
  const years = Math.min(60, Math.max(1, Math.round(getNumberValue(yearsInput))));
  const annualReturn = getNumberValue(returnInput);
  const result = calculateProjection(monthlyInvestment, years, annualReturn);

  totalContributionEl.textContent = formatCurrency(result.totalContribution);
  futureValueEl.textContent = formatCurrency(result.futureValue);
  investmentGainEl.textContent = formatCurrency(result.investmentGain);
  summaryTextEl.textContent = `每月投入 ${formatCurrency(monthlyInvestment)}，投資 ${years} 年，年化報酬率 ${percentFormatter.format(annualReturn)}%。`;
  renderYearlyRows(result.yearlyRows);
}

form.addEventListener("input", updateCalculator);
form.addEventListener("submit", (event) => event.preventDefault());

presetButtons.forEach((button) => {
  button.addEventListener("click", () => {
    monthlyInput.value = button.dataset.monthly;
    yearsInput.value = button.dataset.years;
    returnInput.value = button.dataset.return;
    updateCalculator();
  });
});

updateCalculator();
