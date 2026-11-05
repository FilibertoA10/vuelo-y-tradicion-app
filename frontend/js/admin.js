// Panel de administración: login, CRUD de piezas y talleres, subida de fotos.
(function () {
  const { esc, money, assetUrl, api, PLACEHOLDER } = window.VYT;
  const TOKEN_KEY = "vyt_admin_token";
  const $ = (id) => document.getElementById(id);

  const state = { token: readToken(), products: [], artisans: [], productFilter: "" };

  function readToken() { try { return sessionStorage.getItem(TOKEN_KEY); } catch (_) { return null; } }
  function writeToken(t) {
    state.token = t;
    try { t ? sessionStorage.setItem(TOKEN_KEY, t) : sessionStorage.removeItem(TOKEN_KEY); } catch (_) { /* sin storage */ }
  }

  // Llamada autenticada: si el token venció, regresa al login.
  async function call(path, opts = {}) {
    try {
      return await api(path, { ...opts, token: state.token });
    } catch (err) {
      if (err.status === 401) { logout("Tu sesión expiró. Entra de nuevo."); }
      throw err;
    }
  }

  /* ---------- Sesión ---------- */
  function showLogin(message) {
    $("loginView").hidden = false; $("dashView").hidden = true; $("logoutBtn").hidden = true;
    const err = $("loginError");
    err.hidden = !message; err.textContent = message || "";
  }
  function showDash() {
    $("loginView").hidden = true; $("dashView").hidden = false; $("logoutBtn").hidden = false;
  }
  function logout(message) { writeToken(null); showLogin(message); }

  $("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = $("loginError"); err.hidden = true;
    try {
      const data = await api("/auth/login", { method: "POST", body: { email: $("loginEmail").value.trim(), password: $("loginPassword").value } });
      writeToken(data.access_token);
      $("loginPassword").value = "";
      await enter();
    } catch (ex) {
      err.textContent = ex.network ? ex.message : ex.message || "No se pudo iniciar sesión.";
      err.hidden = false;
    }
  });
  $("logoutBtn").addEventListener("click", () => logout());

  async function enter() {
    try {
      const me = await call("/auth/me");
      if (me.role !== "admin") return logout("Esta cuenta no es de administrador.");
      showDash();
      await Promise.all([loadArtisans(), loadProducts()]);
    } catch (err) {
      if (err.status !== 401) showLogin(err.message);
    }
  }

  /* ---------- Utilidades UI ---------- */
  let flashTimer;
  function flash(msg) {
    const f = $("flash"); f.textContent = msg; f.hidden = false;
    clearTimeout(flashTimer); flashTimer = setTimeout(() => (f.hidden = true), 4000);
  }
  function showFormError(id, msg) { const p = $(id); p.textContent = msg; p.hidden = !msg; }

  document.querySelectorAll(".tab").forEach((tab) =>
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => { t.classList.toggle("active", t === tab); t.setAttribute("aria-selected", t === tab); });
      $("tab-products").hidden = tab.dataset.tab !== "products";
      $("tab-artisans").hidden = tab.dataset.tab !== "artisans";
    })
  );

  // Subida de foto: guarda la ruta devuelta en un input oculto y muestra vista previa.
  function wirePhoto(fileId, hiddenId, previewId, errorId) {
    $(fileId).addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      showFormError(errorId, "");
      const form = new FormData(); form.append("file", file);
      try {
        const data = await call("/admin/uploads", { method: "POST", form });
        setPhoto(hiddenId, previewId, data.url);
      } catch (err) { showFormError(errorId, err.message); e.target.value = ""; }
    });
  }
  function setPhoto(hiddenId, previewId, url) {
    $(hiddenId).value = url || "";
    const img = $(previewId);
    img.hidden = !url;
    if (url) { img.src = assetUrl(url); img.onerror = () => { img.onerror = null; img.src = PLACEHOLDER; }; }
  }
  wirePhoto("pFile", "pImage", "pPreview", "productError");
  wirePhoto("aFile", "aImage", "aPreview", "artisanError");

  /* ---------- Talleres ---------- */
  async function loadArtisans() {
    state.artisans = await call("/artisans");
    $("artisanRows").innerHTML = state.artisans.map((a) => `
      <tr>
        <td><img class="thumb" src="${esc(assetUrl(a.profile_image_url))}" alt="" data-fallback></td>
        <td><strong>${esc(a.workshop_name)}</strong></td>
        <td>${esc(a.full_name)}</td>
        <td>${esc(a.community)}</td>
        <td>${esc(a.phone_whatsapp)}</td>
        <td>${a.product_count}</td>
        <td class="row-actions">
          <button class="btn-link" type="button" data-edit-artisan="${a.id}">Editar</button>
          <button class="btn-link danger" type="button" data-del-artisan="${a.id}">Eliminar</button>
        </td>
      </tr>`).join("") || `<tr><td colspan="7" class="muted">Aún no hay talleres.</td></tr>`;
    $("pArtisan").innerHTML = state.artisans.map((a) => `<option value="${a.id}">${esc(a.workshop_name)}</option>`).join("");
  }

  function openArtisanForm(a) {
    $("artisanForm").hidden = false;
    $("artisanFormTitle").textContent = a ? "Editar taller" : "Nuevo taller";
    $("aId").value = a ? a.id : "";
    $("aFullName").value = a ? a.full_name : "";
    $("aWorkshop").value = a ? a.workshop_name : "";
    $("aCommunity").value = a ? a.community : "";
    $("aPhone").value = a ? a.phone_whatsapp : "";
    $("aBio").value = a ? a.bio || "" : "";
    $("aFile").value = "";
    setPhoto("aImage", "aPreview", a ? a.profile_image_url : "");
    showFormError("artisanError", "");
    $("artisanForm").scrollIntoView({ behavior: "smooth", block: "nearest" });
    $("aFullName").focus();
  }

  $("newArtisanBtn").addEventListener("click", () => openArtisanForm(null));
  $("artisanRows").addEventListener("click", async (e) => {
    const edit = e.target.closest("[data-edit-artisan]");
    const del = e.target.closest("[data-del-artisan]");
    if (edit) openArtisanForm(state.artisans.find((a) => a.id === Number(edit.dataset.editArtisan)));
    if (del) {
      const a = state.artisans.find((x) => x.id === Number(del.dataset.delArtisan));
      if (!confirm(`¿Eliminar el taller «${a.workshop_name}» y TODAS sus piezas? Esta acción no se puede deshacer.`)) return;
      try { await call(`/artisans/${a.id}`, { method: "DELETE" }); flash("Taller eliminado."); await Promise.all([loadArtisans(), loadProducts()]); }
      catch (err) { flash(err.message); }
    }
  });

  $("artisanForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = $("aId").value;
    const body = {
      full_name: $("aFullName").value.trim(),
      workshop_name: $("aWorkshop").value.trim(),
      community: $("aCommunity").value.trim(),
      phone_whatsapp: $("aPhone").value.trim(),
      bio: $("aBio").value.trim() || null,
      profile_image_url: $("aImage").value || null,
    };
    try {
      await call(id ? `/artisans/${id}` : "/artisans", { method: id ? "PUT" : "POST", body });
      $("artisanForm").hidden = true;
      flash(id ? "Taller actualizado." : "Taller creado.");
      await loadArtisans();
    } catch (err) { showFormError("artisanError", err.message); }
  });

  /* ---------- Inventario ---------- */
  async function loadProducts() {
    state.products = await call("/admin/products");
    renderProducts();
  }

  function renderProducts() {
    const q = state.productFilter.toLowerCase();
    const rows = state.products.filter((p) =>
      !q || [p.title, p.category, p.artisan.workshop_name].some((v) => v.toLowerCase().includes(q)));
    $("productRows").innerHTML = rows.map((p) => `
      <tr>
        <td><img class="thumb" src="${esc(assetUrl(p.image_url))}" alt="" data-fallback></td>
        <td><strong>${esc(p.title)}</strong><br><span class="muted">${esc(p.category)}</span></td>
        <td>${esc(p.artisan.workshop_name)}</td>
        <td>${money(p.price)}</td>
        <td>${p.stock}</td>
        <td><span class="badge ${p.is_active ? "on" : "off"}">${p.is_active ? "Visible" : "Oculta"}</span></td>
        <td class="row-actions">
          <button class="btn-link" type="button" data-edit-product="${p.id}">Editar</button>
          <button class="btn-link danger" type="button" data-del-product="${p.id}">Eliminar</button>
        </td>
      </tr>`).join("") || `<tr><td colspan="7" class="muted">No hay piezas que mostrar.</td></tr>`;
  }

  function openProductForm(p) {
    if (!state.artisans.length) return flash("Primero crea al menos un taller.");
    $("productForm").hidden = false;
    $("productFormTitle").textContent = p ? "Editar pieza" : "Nueva pieza";
    $("pId").value = p ? p.id : "";
    $("pArtisan").value = p ? p.artisan_id : state.artisans[0].id;
    $("pTitle").value = p ? p.title : "";
    $("pCategory").value = p ? p.category : "";
    $("pPrice").value = p ? p.price : "";
    $("pStock").value = p ? p.stock : 1;
    $("pActive").checked = p ? p.is_active : true;
    $("pDesc").value = p ? p.description : "";
    $("pFile").value = "";
    setPhoto("pImage", "pPreview", p ? p.image_url : "");
    showFormError("productError", "");
    $("productForm").scrollIntoView({ behavior: "smooth", block: "nearest" });
    $("pTitle").focus();
  }

  $("newProductBtn").addEventListener("click", () => openProductForm(null));
  $("productFilter").addEventListener("input", (e) => { state.productFilter = e.target.value.trim(); renderProducts(); });
  $("productRows").addEventListener("click", async (e) => {
    const edit = e.target.closest("[data-edit-product]");
    const del = e.target.closest("[data-del-product]");
    if (edit) openProductForm(state.products.find((p) => p.id === Number(edit.dataset.editProduct)));
    if (del) {
      const p = state.products.find((x) => x.id === Number(del.dataset.delProduct));
      if (!confirm(`¿Eliminar «${p.title}»? Si solo quieres ocultarla, edítala y desmarca "Visible".`)) return;
      try { await call(`/products/${p.id}`, { method: "DELETE" }); flash("Pieza eliminada."); await loadProducts(); }
      catch (err) { flash(err.message); }
    }
  });

  $("productForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = $("pId").value;
    if (!$("pImage").value) return showFormError("productError", "Sube una fotografía de la pieza.");
    const body = {
      artisan_id: Number($("pArtisan").value),
      title: $("pTitle").value.trim(),
      category: $("pCategory").value.trim(),
      price: Number($("pPrice").value),
      stock: Number($("pStock").value),
      is_active: $("pActive").checked,
      description: $("pDesc").value.trim(),
      image_url: $("pImage").value,
    };
    try {
      await call(id ? `/products/${id}` : "/products", { method: id ? "PUT" : "POST", body });
      $("productForm").hidden = true;
      flash(id ? "Pieza actualizada." : "Pieza creada.");
      await Promise.all([loadProducts(), loadArtisans()]);
    } catch (err) { showFormError("productError", err.message); }
  });

  document.querySelectorAll("[data-cancel]").forEach((b) =>
    b.addEventListener("click", () => { $(b.dataset.cancel + "Form").hidden = true; }));

  document.addEventListener("error", (e) => {
    const img = e.target;
    if (img.tagName === "IMG" && img.hasAttribute("data-fallback") && img.src !== PLACEHOLDER) img.src = PLACEHOLDER;
  }, true);

  /* ---------- Inicio ---------- */
  if (state.token) enter(); else showLogin();
})();
