// Utilidades compartidas por la tienda (app.js) y el panel (admin.js).
(function () {
  const cfg = window.APP_CONFIG || {};
  const API_ORIGIN = (cfg.API_ORIGIN || "http://localhost:8000").replace(/\/$/, "");
  const PLACEHOLDER = "https://placehold.co/400x300?text=Pieza+Artesanal";

  const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

  window.VYT = {
    API_ORIGIN,
    API_BASE: API_ORIGIN + "/api",
    CONTACT_WHATSAPP: cfg.CONTACT_WHATSAPP || "",
    PLACEHOLDER,

    // Escapa texto antes de insertarlo con innerHTML (evita XSS).
    esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, (c) => ESC[c]);
    },

    // Rutas "/uploads/..." viven en la API; solo se permiten http(s) o rutas propias.
    assetUrl(url) {
      if (!url) return PLACEHOLDER;
      if (url.startsWith("/")) return API_ORIGIN + url;
      return /^https?:\/\//i.test(url) ? url : PLACEHOLDER;
    },

    money(n) {
      return new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(Number(n) || 0);
    },

    // fetch con manejo de errores legibles. `token` es opcional (admin).
    async api(path, { method = "GET", body, token, form } = {}) {
      const headers = {};
      if (token) headers.Authorization = `Bearer ${token}`;
      let payload;
      if (form) payload = form;
      else if (body !== undefined) {
        headers["Content-Type"] = "application/json";
        payload = JSON.stringify(body);
      }
      let res;
      try {
        res = await fetch(API_BASE_FOR(path), { method, headers, body: payload });
      } catch (e) {
        const err = new Error("No se pudo conectar con el servidor.");
        err.network = true;
        throw err;
      }
      if (res.status === 204) return null;
      let data = null;
      try { data = await res.json(); } catch (_) { /* sin cuerpo JSON */ }
      if (!res.ok) {
        let msg = `Error ${res.status}`;
        if (data && typeof data.detail === "string") msg = data.detail;
        else if (data && Array.isArray(data.detail)) {
          msg = data.detail.map((d) => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`).join(" · ");
        }
        const err = new Error(msg);
        err.status = res.status;
        throw err;
      }
      return data;
    },
  };

  function API_BASE_FOR(path) {
    return API_ORIGIN + "/api" + path;
  }
})();
