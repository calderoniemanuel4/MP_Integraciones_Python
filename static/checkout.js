const API_BASE_URL = window.location.origin;
const UNIT_PRICE = 1500;
const quantityInput = document.querySelector("#quantity");
const totalEl = document.querySelector("#total");
const statusEl = document.querySelector("#status");
const walletShell = document.querySelector("#wallet-shell");
const currencyFormatter = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS"
});

function selectedQuantity() {
  return 1;
}

function updateTotal() {
  const quantity = selectedQuantity();
  quantityInput.value = quantity;
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

async function initializeWalletBrick() {
  updateTotal();
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
      body: JSON.stringify({ product_code: "1001", quantity: selectedQuantity() })
    });

    const mercadoPago = new MercadoPago(config.public_key, { locale: "es-AR" });
    const bricksBuilder = mercadoPago.bricks();
    await bricksBuilder.create("wallet", "walletBrick_container", {
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
    console.error("Wallet Brick initialization failed", error);
    showCheckoutError();
  }
}

quantityInput.addEventListener("change", updateTotal);
initializeWalletBrick();
