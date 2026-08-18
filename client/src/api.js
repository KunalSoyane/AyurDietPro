const rawBaseUrl = (import.meta.env.VITE_API_URL || "").trim();

const PROD_FALLBACK_BASE = "https://ayurdiet-backend-cah4.onrender.com";

function toApiBase(raw) {
  try {
    const parsed = new URL(raw);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      let base = parsed.href.replace(/\/+$/, "");
      if (!/\/api$/i.test(base)) {
        base += "/api";
      }
      return base;
    }
  } catch {}
  return null;
}

function resolveBaseUrl() {
  if (rawBaseUrl) {
    const fromEnv = toApiBase(rawBaseUrl);
    if (fromEnv) {
      return fromEnv;
    }
  }
  if (import.meta.env.DEV) {
    return "/api";
  }
  return toApiBase(PROD_FALLBACK_BASE);
}

export const BASE_URL = resolveBaseUrl();

function isAbsoluteUrl(path) {
  return /^([a-z][a-z0-9+.-]*:)?\/\//i.test(path);
}

function buildUrl(path) {
  if (isAbsoluteUrl(path)) {
    return path;
  }
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${BASE_URL}${cleanPath}`;
}

function looksLikeHtml(text, contentType) {
  return contentType.includes("text/html") || /^</.test(text.trim());
}

async function request(path, options = {}) {
  const { suppressGlobalError, ...fetchOptions } = options;

  const token = localStorage.getItem("token");
  const headers = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(buildUrl(path), {
      ...fetchOptions,
      headers,
    });
  } catch {
    const message = navigator.onLine
      ? "Unable to reach the server. Please try again."
      : "No internet connection.";
    const error = new Error(message);
    error.status = 0;
    if (!suppressGlobalError) {
      window.dispatchEvent(
        new CustomEvent("api-error", {
          detail: { message, status: 0 },
        })
      );
    }
    throw error;
  }

  const bodyText = await response.text().catch(() => "");
  const contentType = response.headers.get("content-type") || "";

  let data = null;
  if (bodyText.trim()) {
    try {
      data = JSON.parse(bodyText);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    let message = "Request failed";

    if (data && Array.isArray(data.detail) && data.detail[0]?.msg) {
      const field = data.detail[0].loc?.[1] ? `[${data.detail[0].loc[1]}]: ` : "";
      message = `${field}${data.detail[0].msg}`;
    } else if (data && typeof data.detail === "string") {
      message = data.detail;
    } else if (data && data.message) {
      message = data.message;
    } else if (looksLikeHtml(bodyText, contentType)) {
      message =
        "The server returned an unexpected page instead of data. The API URL may be misconfigured.";
    } else if (!navigator.onLine) {
      message = "No internet connection.";
    } else if (bodyText.trim()) {
      message = "Request failed with an unexpected response.";
    }

    const error = new Error(message);
    error.status = response.status;

    if (!suppressGlobalError) {
      window.dispatchEvent(
        new CustomEvent("api-error", {
          detail: { message, status: response.status },
        })
      );
    }
    throw error;
  }

  if (response.status === 204 || response.status === 205 || !bodyText.trim()) {
    return null;
  }

  if (data === null) {
    const error = new Error(
      looksLikeHtml(bodyText, contentType)
        ? "The server returned an unexpected page instead of data. The API URL may be misconfigured."
        : "Received invalid or empty response from server"
    );
    error.status = response.status;
    throw error;
  }

  return data;
}

export const api = {
  // Auth
  login: (email, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      suppressGlobalError: true,
    }),
  register: (payload) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
      suppressGlobalError: true,
    }),

  // Patients
  patients: () => request("/patients"),
  createPatient: (payload) =>
    request("/patients", { method: "POST", body: JSON.stringify(payload) }),
  patient: (id) => request(`/patients/${id}`),
  updatePatient: (id, payload) =>
    request(`/patients/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deletePatient: (id) => request(`/patients/${id}`, { method: "DELETE" }),

  // Foods & Templates
  foods: (params = {}) => {
    const cleanParams = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
    );
    const q = new URLSearchParams(cleanParams).toString();
    return request(`/foods${q ? `?${q}` : ""}`);
  },
  foodCategories: () => request("/foods/categories"),
  templates: () => request("/templates"),

  // Diet Plans
  generatePlan: (payload) =>
    request("/diet-plans/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  dietPlans: () => request("/diet-plans"),
  getPlan: (id) => request(`/diet-plans/${id}`),
  patientPlans: (patientId) => request(`/diet-plans/patient/${patientId}`),
  updatePlan: (id, payload) =>
    request(`/diet-plans/${id}`, { method: "PUT", body: JSON.stringify(payload) }),

  // Reports
  getWeeklyReport: () => request("/reports/weekly"),
};
