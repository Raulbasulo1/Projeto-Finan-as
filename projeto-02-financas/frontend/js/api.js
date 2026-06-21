const API_BASE_URL = "http://localhost:8001";

async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: "Erro desconhecido."
    }));

    throw new Error(error.detail || "Erro ao comunicar com a API.");
  }

  return response.json();
}

const Api = {
  health: () => apiRequest("/health"),

  getAccounts: () => apiRequest("/accounts"),
    createAccount: (account) => {
    return apiRequest("/accounts", {
      method: "POST",
      body: JSON.stringify(account)
    });
  },

  deleteAccount: (id) => {
    return apiRequest(`/accounts/${id}`, {
      method: "DELETE"
    });
  },

  getAccountBalances: () => apiRequest("/dashboard/accounts"),

  getCategories: (type = "") => {
    const query = type ? `?type=${type}` : "";
    return apiRequest(`/categories${query}`);
  },

  createCategory: (category) => {
    return apiRequest("/categories", {
      method: "POST",
      body: JSON.stringify(category)
    });
  },

  deleteCategory: (id) => {
    return apiRequest(`/categories/${id}`, {
    });
  },

  getTransactions: (filters = {}) => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        params.append(key, value);
      }
    });

    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest(`/transactions${query}`);
  },

  createTransaction: (transaction) => {
    return apiRequest("/transactions", {
      method: "POST",
      body: JSON.stringify(transaction)
    });
  },

  deleteTransaction: (id) => {
    return apiRequest(`/transactions/${id}`, {
      method: "DELETE"
    });
  },

  getDashboardSummary: (filters = {}) => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        params.append(key, value);
      }
    });

    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest(`/dashboard/summary${query}`);
  },

  getDashboardCategories: (filters = {}) => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        params.append(key, value);
      }
    });

    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest(`/dashboard/categories${query}`);
  },

  getDashboardMonthly: (year = 2026) => {
    return apiRequest(`/dashboard/monthly?year=${year}`);
  },

  getDashboardHealth: (filters = {}) => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        params.append(key, value);
      }
    });

    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest(`/dashboard/health${query}`);
  },

  getBudgets: (filters = {}) => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        params.append(key, value);
      }
    });

    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest(`/budgets${query}`);
  },

  createBudget: (budget) => {
    return apiRequest("/budgets", {
      method: "POST",
      body: JSON.stringify(budget)
    });
  },

  deleteBudget: (id) => {
    return apiRequest(`/budgets/${id}`, {
      method: "DELETE"
    });
  },

  getBudgetAnalysis: (filters = {}) => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        params.append(key, value);
      }
    });

    const query = params.toString() ? `?${params.toString()}` : "";
    return apiRequest(`/dashboard/budgets-analysis${query}`);
  },

  getExportTransactionsUrl: (filters = {}) => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        params.append(key, value);
      }
    });

    const query = params.toString() ? `?${params.toString()}` : "";
    return `${API_BASE_URL}/export/transactions.csv${query}`;
  }
};
