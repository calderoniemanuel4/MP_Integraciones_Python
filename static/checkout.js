const API_BASE_URL = window.location.origin;
const UNIT_PRICE = 1500;
const quantityOutput = document.querySelector("#quantity");
const decreaseQuantityButton = document.querySelector("#decrease-quantity");
const increaseQuantityButton = document.querySelector("#increase-quantity");
const totalEl = document.querySelector("#total");
const statusEl = document.querySelector("#status");
const walletShell = document.querySelector("#wallet-shell");
let walletController;
let refreshTimer;
let initializationVersion = 0;
let quantity = 1;
const currencyFormatter = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS"
});

function selectedQuantity() {
  return quantity;
}

function updateTotal() {
  quantityOutput.textContent = String(quantity);
  decreaseQuantityButton.disabled = quantity === 1;
  increaseQuantityButton.disabled = quantity === 3;
  totalEl.textContent = currencyFormatter.format(UNIT_PRICE * quantity);
}

function showCheckoutError() {
  walletShell.classList.add("ready");
  walletShell.setAttribute("aria-busy", "false");
  statusEl.className = "error";
  statusEl.textContent = "No se pudo preparar Mercado Pago. Intentá nuevamente en unos instantes.";
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

async function initializeWalletBrick(version = ++initializationVersion) {
  const quantity = selectedQuantity();
  walletShell.classList.remove("ready");
  walletShell.setAttribute("aria-busy", "true");
  statusEl.className = "";
  statusEl.textContent = "Creando preferencia...";

  try {
    const config = await fetchJson(`${API_BASE_URL}/checkout/config`);
    if (typeof MercadoPago !== "function") {
      throw new Error("MercadoPago.js did not load");
    }

    const preference = await fetchJson(`${API_BASE_URL}/checkout/preference`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_code: "1001", quantity })
    });

    if (version !== initializationVersion) return;

    if (walletController) {
      await walletController.unmount();
      walletController = undefined;
    }
    if (version !== initializationVersion) return;

    const mercadoPago = new MercadoPago(config.public_key, { locale: "es-AR" });
    const bricksBuilder = mercadoPago.bricks();
    walletController = await bricksBuilder.create("wallet", "walletBrick_container", {
      initialization: {
        preferenceId: preference.preference_id,
        redirectMode: "self"
      },
      customization: {
        theme: "default",
        customStyle: {
          buttonHeight: "48px",
          borderRadius: "6px",
          valueProp: "security_safety"
        }
      },
      callbacks: {
        onReady: () => {
          if (version !== initializationVersion) return;
          walletShell.classList.add("ready");
          walletShell.setAttribute("aria-busy", "false");
          statusEl.textContent = "";
        },
        onSubmit: () => {
          statusEl.textContent = "Redirigiendo a Mercado Pago...";
        },
        onError: () => {
          showCheckoutError();
        }
      }
    });
  } catch (error) {
    if (version !== initializationVersion) return;
    console.error("Wallet Brick initialization failed", error);
    showCheckoutError();
  }
}

function refreshCheckout() {
  updateTotal();
  const version = ++initializationVersion;
  clearTimeout(refreshTimer);
  refreshTimer = setTimeout(() => initializeWalletBrick(version), 250);
}

function changeQuantity(change) {
  const nextQuantity = Math.min(3, Math.max(1, quantity + change));
  if (nextQuantity === quantity) return;
  quantity = nextQuantity;
  refreshCheckout();
}

decreaseQuantityButton.addEventListener("click", () => changeQuantity(-1));
increaseQuantityButton.addEventListener("click", () => changeQuantity(1));
updateTotal();
initializeWalletBrick();
