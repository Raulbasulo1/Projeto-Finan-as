
let categoryChart = null;
let monthlyChart = null;

let accountsCache = [];
let categoriesCache = [];

function formatCurrency(value) {
  return new Intl.NumberFormat("pt-PT", {
    style: "currency",
    currency: "EUR"
  }).format(value || 0);
}

function getSelectedFilters() {
  const year = document.getElementById("filter-year").value;
  const month = document.getElementById("filter-month").value;

  return {
    year,
    month
  };
}

function getCategoryName(id) {
  const category = categoriesCache.find((item) => item.id === id);
  return category ? category.name : "Sem categoria";
}

function getAccountName(id) {
  const account = accountsCache.find((item) => item.id === id);
  return account ? account.name : "Sem conta";
}

async function loadDashboard() {
  const filters = getSelectedFilters();

  const [summary, categoryData, monthlyData, healthData] = await Promise.all([
    Api.getDashboardSummary(filters),
    Api.getDashboardCategories(filters),
    Api.getDashboardMonthly(filters.year || 2026),
    Api.getDashboardHealth(filters)
  ]);

  document.getElementById("total-income").textContent = formatCurrency(summary.total_income);
  document.getElementById("total-expense").textContent = formatCurrency(summary.total_expense);
  document.getElementById("balance").textContent = formatCurrency(summary.balance);
  document.getElementById("budget-usage").textContent = `${summary.budget_usage_percent}%`;

  document.getElementById("health-status").textContent = healthData.status;
  document.getElementById("health-message").textContent = healthData.message;
  document.getElementById("health-score").textContent = healthData.score;

  renderCategoryChart(categoryData);
  renderMonthlyChart(monthlyData);
}

function renderCategoryChart(data) {
  const ctx = document.getElementById("category-chart");

  const labels = data.map((item) => item.category);
  const values = data.map((item) => item.total);

  if (categoryChart) {
    categoryChart.destroy();
  }

  categoryChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: values
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom"
        }
      }
    }
  });
}

function renderMonthlyChart(data) {
  const ctx = document.getElementById("monthly-chart");

  const monthNames = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
  ];

  if (monthlyChart) {
    monthlyChart.destroy();
  }

  monthlyChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map((item) => monthNames[item.month - 1]),
      datasets: [
        {
          label: "Receitas",
          data: data.map((item) => item.income)
        },
        {
          label: "Despesas",
          data: data.map((item) => item.expense)
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom"
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

async function loadReferenceData() {
  accountsCache = await Api.getAccounts();
  categoriesCache = await Api.getCategories();

const accountSelect = document.getElementById("transaction-account");
const categorySelect = document.getElementById("transaction-category");
const budgetCategorySelect = document.getElementById("budget-category");

accountSelect.innerHTML = "";
categorySelect.innerHTML = "";
budgetCategorySelect.innerHTML = "";

  accountsCache.forEach((account) => {
    const option = document.createElement("option");
    option.value = account.id;
    option.textContent = account.name;
    accountSelect.appendChild(option);
  });

  categoriesCache.forEach((category) => {
    const option = document.createElement("option");
    option.value = category.id;
    option.textContent = `${category.name} (${category.type})`;
    categorySelect.appendChild(option);
  });
}

categoriesCache
  .filter((category) => category.type === "expense")
  .forEach((category) => {
    const option = document.createElement("option");
    option.value = category.id;
    option.textContent = category.name;
    budgetCategorySelect.appendChild(option);
  });

async function loadTransactions() {
  const filters = getSelectedFilters();
  const transactions = await Api.getTransactions(filters);

  const table = document.getElementById("transactions-table");
  table.innerHTML = "";

  if (transactions.length === 0) {
    table.innerHTML = `
      <tr>
        <td colspan="7">Não existem transações para o período selecionado.</td>
      </tr>
    `;
    return;
  }

  transactions.forEach((transaction) => {
    const row = document.createElement("tr");

    const typeLabel = transaction.type === "income" ? "Receita" : "Despesa";

    row.innerHTML = `
      <td>${transaction.date}</td>
      <td>${transaction.description}</td>
      <td><span class="badge ${transaction.type}">${typeLabel}</span></td>
      <td>${getCategoryName(transaction.category_id)}</td>
      <td>${getAccountName(transaction.account_id)}</td>
      <td>${formatCurrency(transaction.amount)}</td>
      <td>
        <button class="delete-button" data-id="${transaction.id}">
          Remover
        </button>
      </td>
    `;

    table.appendChild(row);
  });

  document.querySelectorAll(".delete-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.dataset.id;

      if (!confirm("Tens a certeza que queres remover esta transação?")) {
        return;
      }

      await Api.deleteTransaction(id);
      await refreshAll();
    });
  });
}

async function handleTransactionSubmit(event) {
  event.preventDefault();

  const message = document.getElementById("form-message");

  const transaction = {
    description: document.getElementById("transaction-description").value,
    amount: Number(document.getElementById("transaction-amount").value),
    type: document.getElementById("transaction-type").value,
    date: document.getElementById("transaction-date").value,
    account_id: Number(document.getElementById("transaction-account").value),
    category_id: Number(document.getElementById("transaction-category").value)
  };

  try {
    await Api.createTransaction(transaction);

    message.textContent = "Transação adicionada com sucesso.";
    message.className = "form-message success";

    event.target.reset();
    document.getElementById("transaction-date").value = new Date().toISOString().slice(0, 10);

    await refreshAll();
  } catch (error) {
    message.textContent = error.message;
    message.className = "form-message error";
  }
}

async function refreshAll() {
  updateExportLink();
  await loadDashboard();
  await loadTransactions();
  await loadBudgetAnalysis();
  await loadAccountsManagement();
  await loadCategoriesManagement();
}

async function loadBudgetAnalysis() {
  const filters = getSelectedFilters();

  if (!filters.month) {
    const list = document.getElementById("budget-analysis-list");
    list.innerHTML = `
      <p>Seleciona um mês específico para ver a análise dos orçamentos.</p>
    `;
    return;
  }

  const analysis = await Api.getBudgetAnalysis(filters);
  const list = document.getElementById("budget-analysis-list");

  list.innerHTML = "";

  if (analysis.length === 0) {
    list.innerHTML = `
      <p>Não existem orçamentos definidos para este período.</p>
    `;
    return;
  }

  analysis.forEach((item) => {
    const card = document.createElement("div");
    card.className = "budget-item";

    card.innerHTML = `
      <div class="budget-top">
        <div>
          <strong>${item.category}</strong>
          <span>${formatCurrency(item.spent)} de ${formatCurrency(item.limit_amount)}</span>
        </div>
        <span class="budget-status ${item.status.toLowerCase().replaceAll(" ", "-")}">
          ${item.status}
        </span>
      </div>

      <div class="progress-bar">
        <div class="progress-fill" style="width: ${Math.min(item.percentage, 100)}%"></div>
      </div>

      <div class="budget-bottom">
        <span>${item.percentage}% usado</span>
        <span>Restante: ${formatCurrency(item.remaining)}</span>
      </div>

      <button class="delete-button budget-delete" data-id="${item.budget_id}">
        Remover orçamento
      </button>
    `;

    list.appendChild(card);
  });

  document.querySelectorAll(".budget-delete").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.dataset.id;

      if (!confirm("Tens a certeza que queres remover este orçamento?")) {
        return;
      }

      await Api.deleteBudget(id);
      await refreshAll();
    });
  });
}


async function handleBudgetSubmit(event) {
  event.preventDefault();

  const message = document.getElementById("budget-message");

  const budget = {
    category_id: Number(document.getElementById("budget-category").value),
    year: Number(document.getElementById("budget-year").value),
    month: Number(document.getElementById("budget-month").value),
    limit_amount: Number(document.getElementById("budget-limit").value)
  };

  try {
    await Api.createBudget(budget);

    message.textContent = "Orçamento adicionado com sucesso.";
    message.className = "form-message success";

    document.getElementById("budget-limit").value = "";

    await refreshAll();
  } catch (error) {
    message.textContent = error.message;
    message.className = "form-message error";
  }
}

function exportTransactionsCsv() {
  const filters = getSelectedFilters();
  const url = Api.getExportTransactionsUrl(filters);

  window.location.href = url;
}

function updateExportLink() {
  const filters = getSelectedFilters();
  const exportLink = document.getElementById("export-csv");

  if (!exportLink) {
    return;
  }

  exportLink.href = Api.getExportTransactionsUrl(filters);
}

async function loadAccountsManagement() {
  const accounts = await Api.getAccountBalances();
  const list = document.getElementById("accounts-list");

  list.innerHTML = "";

  if (accounts.length === 0) {
    list.innerHTML = "<p>Não existem contas registadas.</p>";
    return;
  }

  accounts.forEach((account) => {
    const item = document.createElement("div");
    item.className = "management-item";

    item.innerHTML = `
      <div>
        <strong>${account.name}</strong>
        <span>${account.type}</span>
        <small>
          Saldo inicial: ${formatCurrency(account.initial_balance)} ·
          Saldo atual: ${formatCurrency(account.current_balance)}
        </small>
      </div>

      <button class="delete-button account-delete" data-id="${account.id}">
        Remover
      </button>
    `;

    list.appendChild(item);
  });

  document.querySelectorAll(".account-delete").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.dataset.id;

      if (!confirm("Tens a certeza que queres remover esta conta?")) {
        return;
      }

      try {
        await Api.deleteAccount(id);
        await refreshAll();
      } catch (error) {
        alert(error.message);
      }
    });
  });
}


async function loadCategoriesManagement() {
  const categories = await Api.getCategories();
  const list = document.getElementById("categories-list");

  list.innerHTML = "";

  if (categories.length === 0) {
    list.innerHTML = "<p>Não existem categorias registadas.</p>";
    return;
  }

  categories.forEach((category) => {
    const item = document.createElement("div");
    item.className = "management-item";

    const typeLabel = category.type === "income" ? "Receita" : "Despesa";

    item.innerHTML = `
      <div>
        <strong>${category.name}</strong>
        <span>${typeLabel}</span>
      </div>

      <button class="delete-button category-delete" data-id="${category.id}">
        Remover
      </button>
    `;

    list.appendChild(item);
  });

  document.querySelectorAll(".category-delete").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.dataset.id;

      if (!confirm("Tens a certeza que queres remover esta categoria?")) {
        return;
      }

      try {
        await Api.deleteCategory(id);
        await refreshAll();
      } catch (error) {
        alert(error.message);
      }
    });
  });
}


async function handleAccountSubmit(event) {
  event.preventDefault();

  const message = document.getElementById("account-message");

  const account = {
    name: document.getElementById("account-name").value,
    type: document.getElementById("account-type").value,
    initial_balance: Number(document.getElementById("account-balance").value)
  };

  try {
    await Api.createAccount(account);

    message.textContent = "Conta adicionada com sucesso.";
    message.className = "form-message success";

    event.target.reset();
    document.getElementById("account-balance").value = 0;

    await loadReferenceData();
    await refreshAll();
  } catch (error) {
    message.textContent = error.message;
    message.className = "form-message error";
  }
}


async function handleCategorySubmit(event) {
  event.preventDefault();

  const message = document.getElementById("category-message");

  const category = {
    name: document.getElementById("category-name").value,
    type: document.getElementById("category-type").value
  };

  try {
    await Api.createCategory(category);

    message.textContent = "Categoria adicionada com sucesso.";
    message.className = "form-message success";

    event.target.reset();

    await loadReferenceData();
    await refreshAll();
  } catch (error) {
    message.textContent = error.message;
    message.className = "form-message error";
  }
}

async function initialiseDashboard() {
  document.getElementById("transaction-date").value = new Date().toISOString().slice(0, 10);

  await loadReferenceData();
  await refreshAll();

  document.getElementById("apply-filters").addEventListener("click", refreshAll);
  document.getElementById("transaction-form").addEventListener("submit", handleTransactionSubmit);
  document.getElementById("budget-form").addEventListener("submit", handleBudgetSubmit);
  document.getElementById("account-form").addEventListener("submit", handleAccountSubmit);
  document.getElementById("category-form").addEventListener("submit", handleCategorySubmit);
}
