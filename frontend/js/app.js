// Tienda pública: directorio de talleres, catálogo con filtros y pedido por WhatsApp.
(function () {
  const { esc, money, assetUrl, api, PLACEHOLDER } = window.VYT;
  const CART_KEY = "vyt_cart_v1";

  const state = {
    products: [],
    artisans: [],
    filters: { search: "", category: "", artisanId: null },
    cart: loadCart(),
  };

  const $ = (id) => document.getElementById(id);
  const el = {
    productGrid: $("productGrid"), artisanGrid: $("artisanGrid"), activeFilters: $("activeFilters"),
    searchInput: $("searchInput"), categoryFilter: $("categoryFilter"), searchForm: $("searchForm"),
    cartBtn: $("cartFloatBtn"), cartCount: $("cartCount"), contactBtn: $("contactFloatBtn"),
    modal: $("cartModal"), closeBtn: $("closeModalBtn"),
    cartView: $("cartView"), resultView: $("resultView"), resultOrders: $("resultOrders"),
    items: $("cartItemsList"), total: $("cartTotalDisplay"),
    form: $("checkoutForm"), buyer: $("buyerName"), notes: $("orderNotes"),
    error: $("checkoutError"), send: $("btnSendWhatsapp"), clear: $("btnClearCart"), back: $("btnBackToShop"),
  };

  /* ---------- Carrito persistente ---------- */
  function loadCart() {
    try {
      const data = JSON.parse(localStorage.getItem(CART_KEY) || "[]");
      return Array.isArray(data) ? data.filter((i) => i && Number.isInteger(i.product_id) && i.quantity > 0) : [];
    } catch (_) { return []; }
  }
  function saveCart() {
    try { localStorage.setItem(CART_KEY, JSON.stringify(state.cart)); } catch (_) { /* modo privado */ }
  }

  /* ---------- Datos ---------- */
  async function loadArtisans() {
    try {
      state.artisans = await api("/artisans");
      renderArtisans();
    } catch (err) {
      el.artisanGrid.innerHTML = `<div class="empty-state">${esc(connectionMessage(err))}</div>`;
    }
  }

  async function loadCategories() {
    try {
      const cats = await api("/categories");
      el.categoryFilter.innerHTML =
        `<option value="">Todas las categorías</option>` +
        cats.map((c) => `<option value="${esc(c)}">${esc(c)}</option>`).join("");
      el.categoryFilter.value = state.filters.category;
    } catch (_) { /* el filtro queda solo con "Todas" */ }
  }

  async function loadProducts() {
    const { search, category, artisanId } = state.filters;
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (category) params.set("category", category);
    if (artisanId) params.set("artisan_id", artisanId);
    try {
      state.products = await api(`/products?${params}`);
      renderProducts();
    } catch (err) {
      el.productGrid.innerHTML = `<div class="empty-state">${esc(connectionMessage(err))}</div>`;
    }
    renderActiveFilters();
  }

  function connectionMessage(err) {
    return err.network
      ? "No fue posible conectar con el servidor. Verifica que la API esté encendida."
      : err.message;
  }

  /* ---------- Render ---------- */
  function renderArtisans() {
    if (!state.artisans.length) {
      el.artisanGrid.innerHTML = `<div class="empty-state">Pronto conocerás a los talleres participantes.</div>`;
      return;
    }
    el.artisanGrid.innerHTML = state.artisans.map((a) => {
      const wa = `https://wa.me/${encodeURIComponent(a.phone_whatsapp)}?text=${encodeURIComponent("Hola, vi su taller en Vuelo y Tradición y quisiera más información.")}`;
      const n = a.product_count;
      return `
        <article class="artisan-card">
          <img src="${esc(assetUrl(a.profile_image_url))}" alt="Retrato de ${esc(a.full_name)}" loading="lazy" data-fallback="${esc(PLACEHOLDER)}">
          <div class="artisan-body">
            <span class="artisan-community">${esc(a.community)}</span>
            <h3>${esc(a.workshop_name)}</h3>
            <p class="artisan-name">${esc(a.full_name)}</p>
            <p class="artisan-bio">${esc(a.bio || "")}</p>
            <div class="artisan-actions">
              <button type="button" class="btn-add" data-artisan="${a.id}" ${n ? "" : "disabled"}>
                ${n ? `Ver ${n} pieza${n === 1 ? "" : "s"}` : "Sin piezas por ahora"}
              </button>
              <a class="btn-outline" href="${esc(wa)}" target="_blank" rel="noopener noreferrer">Escribir</a>
            </div>
          </div>
        </article>`;
    }).join("");
  }

  function renderProducts() {
    if (!state.products.length) {
      el.productGrid.innerHTML = `<div class="empty-state">No se encontraron artesanías con los filtros seleccionados.</div>`;
      return;
    }
    el.productGrid.innerHTML = state.products.map((p) => {
      const out = p.stock < 1;
      return `
        <article class="product-card">
          <img src="${esc(assetUrl(p.image_url))}" alt="${esc(p.title)}" loading="lazy" data-fallback="${esc(PLACEHOLDER)}">
          <div class="card-body">
            <span class="artisan-tag">${esc(p.artisan.workshop_name)} · ${esc(p.artisan.community)}</span>
            <h3 class="card-title">${esc(p.title)}</h3>
            <p class="card-desc">${esc(p.description)}</p>
            <div class="card-footer">
              <span class="price">${money(p.price)}</span>
              <button type="button" class="btn-add" data-add="${p.id}" ${out ? "disabled" : ""}>
                ${out ? "Agotado" : "+ Agregar"}
              </button>
            </div>
            ${!out && p.stock <= 3 ? `<span class="stock-note">¡Solo quedan ${p.stock}!</span>` : ""}
          </div>
        </article>`;
    }).join("");
  }

  function renderActiveFilters() {
    const { artisanId } = state.filters;
    if (!artisanId) { el.activeFilters.hidden = true; el.activeFilters.innerHTML = ""; return; }
    const a = state.artisans.find((x) => x.id === Number(artisanId));
    el.activeFilters.hidden = false;
    el.activeFilters.innerHTML =
      `<span class="chip">Taller: ${esc(a ? a.workshop_name : "#" + artisanId)}
         <button type="button" data-clear-artisan aria-label="Quitar filtro de taller">&times;</button></span>`;
  }

  /* ---------- Carrito ---------- */
  function addToCart(productId) {
    const p = state.products.find((x) => x.id === productId);
    if (!p || p.stock < 1) return;
    const item = state.cart.find((i) => i.product_id === productId);
    if (item) {
      if (item.quantity >= p.stock) { flashCount(); return; }
      item.quantity += 1;
      item.stock = p.stock;
    } else {
      state.cart.push({ product_id: p.id, title: p.title, price: p.price, quantity: 1, stock: p.stock, workshop: p.artisan.workshop_name });
    }
    saveCart(); updateBadge();
  }

  function updateBadge() {
    el.cartCount.textContent = state.cart.reduce((n, i) => n + i.quantity, 0);
  }
  function flashCount() {
    el.cartCount.classList.add("bump");
    setTimeout(() => el.cartCount.classList.remove("bump"), 300);
  }

  function cartTotal() {
    return state.cart.reduce((sum, i) => sum + i.price * i.quantity, 0);
  }

  function renderCart() {
    if (!state.cart.length) {
      el.items.innerHTML = `<p class="empty-cart">Tu canasta está vacía. Agrega piezas del catálogo.</p>`;
      el.total.textContent = money(0);
      el.send.disabled = true; el.clear.hidden = true;
      return;
    }
    el.send.disabled = false; el.clear.hidden = false;
    el.items.innerHTML = state.cart.map((i) => `
      <div class="cart-row">
        <div class="cart-row-info">
          <strong>${esc(i.title)}</strong>
          <span class="cart-row-sub">${esc(i.workshop || "")} · ${money(i.price)} c/u</span>
        </div>
        <div class="qty" role="group" aria-label="Cantidad de ${esc(i.title)}">
          <button type="button" data-qty="dec" data-id="${i.product_id}" aria-label="Quitar uno">−</button>
          <span>${i.quantity}</span>
          <button type="button" data-qty="inc" data-id="${i.product_id}" aria-label="Agregar uno" ${i.quantity >= (i.stock || 99) ? "disabled" : ""}>+</button>
        </div>
        <span class="cart-row-total">${money(i.price * i.quantity)}</span>
        <button type="button" class="remove-btn" data-qty="rm" data-id="${i.product_id}" aria-label="Eliminar ${esc(i.title)}">🗑</button>
      </div>`).join("");
    el.total.textContent = money(cartTotal());
  }

  function changeQty(id, action) {
    const idx = state.cart.findIndex((i) => i.product_id === id);
    if (idx < 0) return;
    const item = state.cart[idx];
    if (action === "inc" && item.quantity < (item.stock || 99)) item.quantity += 1;
    if (action === "dec") item.quantity -= 1;
    if (action === "rm" || item.quantity <= 0) state.cart.splice(idx, 1);
    saveCart(); updateBadge(); renderCart();
  }

  /* ---------- Modal ---------- */
  let lastFocus = null;
  function openModal() {
    lastFocus = document.activeElement;
    showCartView();
    el.modal.classList.remove("hidden");
    document.body.classList.add("no-scroll");
    el.closeBtn.focus();
  }
  function closeModal() {
    el.modal.classList.add("hidden");
    document.body.classList.remove("no-scroll");
    if (lastFocus) lastFocus.focus();
  }
  function showCartView() {
    el.cartView.hidden = false; el.resultView.hidden = true;
    el.error.hidden = true;
    renderCart();
  }

  /* ---------- Checkout ---------- */
  async function checkout(e) {
    e.preventDefault();
    el.error.hidden = true;
    const name = el.buyer.value.trim();
    if (name.length < 2) return showError("Escribe tu nombre para que el artesano sepa quién eres.");
    if (!state.cart.length) return showError("Tu canasta está vacía.");

    el.send.disabled = true;
    el.send.textContent = "Generando pedido…";
    try {
      const data = await api("/checkout/whatsapp", {
        method: "POST",
        body: {
          customer_name: name,
          notes: el.notes.value.trim() || null,
          items: state.cart.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
        },
      });
      showResult(data);
      state.cart = []; saveCart(); updateBadge();
    } catch (err) {
      showError(connectionMessage(err));
    } finally {
      el.send.disabled = !state.cart.length;
      el.send.textContent = "Completar pedido por WhatsApp";
    }
  }

  function showError(msg) {
    el.error.textContent = msg;
    el.error.hidden = false;
  }

  function showResult(data) {
    const safe = data.orders.filter((o) => typeof o.whatsapp_url === "string" && o.whatsapp_url.startsWith("https://wa.me/"));
    el.resultOrders.innerHTML = safe.map((o) => `
      <div class="result-order">
        <div>
          <strong>${esc(o.workshop)}</strong>
          <span class="cart-row-sub">${o.items.map((i) => `${i.quantity}× ${esc(i.title)}`).join(", ")}</span>
          <span class="result-total">Total: ${money(o.total)}</span>
        </div>
        <a class="btn-whatsapp-link" href="${esc(o.whatsapp_url)}" target="_blank" rel="noopener noreferrer">Abrir WhatsApp</a>
      </div>`).join("");
    el.cartView.hidden = true; el.resultView.hidden = false;
    if (safe.length === 1) window.open(safe[0].whatsapp_url, "_blank", "noopener");
    loadProducts(); // refresca disponibilidad
  }

  /* ---------- Eventos ---------- */
  document.addEventListener("error", (e) => {
    const img = e.target;
    if (img.tagName === "IMG" && img.dataset.fallback && img.src !== img.dataset.fallback) img.src = img.dataset.fallback;
  }, true);

  el.productGrid.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-add]");
    if (btn) addToCart(Number(btn.dataset.add));
  });

  el.artisanGrid.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-artisan]");
    if (!btn) return;
    state.filters.artisanId = Number(btn.dataset.artisan);
    loadProducts();
    document.getElementById("catalogo").scrollIntoView({ behavior: "smooth" });
  });

  el.activeFilters.addEventListener("click", (e) => {
    if (e.target.closest("[data-clear-artisan]")) { state.filters.artisanId = null; loadProducts(); }
  });

  el.items.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-qty]");
    if (btn) changeQty(Number(btn.dataset.id), btn.dataset.qty);
  });

  el.cartBtn.addEventListener("click", openModal);
  el.closeBtn.addEventListener("click", closeModal);
  el.back.addEventListener("click", closeModal);
  el.modal.addEventListener("click", (e) => { if (e.target === el.modal) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !el.modal.classList.contains("hidden")) closeModal(); });
  el.form.addEventListener("submit", checkout);
  el.clear.addEventListener("click", () => { state.cart = []; saveCart(); updateBadge(); renderCart(); });

  let timer;
  el.searchInput.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => { state.filters.search = el.searchInput.value.trim(); loadProducts(); }, 350);
  });
  el.searchForm.addEventListener("submit", (e) => e.preventDefault());
  el.categoryFilter.addEventListener("change", () => { state.filters.category = el.categoryFilter.value; loadProducts(); });

  /* ---------- Inicio ---------- */
  if (window.VYT.CONTACT_WHATSAPP) {
    const text = encodeURIComponent("Hola, quisiera información sobre Vuelo y Tradición.");
    el.contactBtn.href = `https://wa.me/${encodeURIComponent(window.VYT.CONTACT_WHATSAPP)}?text=${text}`;
    el.contactBtn.hidden = false;
  }
  updateBadge();
  loadArtisans().then(loadProducts);
  loadCategories();
})();
