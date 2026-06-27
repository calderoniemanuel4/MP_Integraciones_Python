# Mercado Pago Checkout Pro + FastAPI + Firestore

Proyecto funcional de prueba para integrar Mercado Pago Checkout Pro usando Python 3.12+, FastAPI y Cloud Firestore en Native Mode como única base de datos. No usa SQL, SQLite, SQLAlchemy ni bases relacionales.

## Arquitectura

Flujo principal:

1. `static/checkout.html` corre localmente en `http://localhost:5500`.
2. El HTML llama a `POST /checkout/preference` en la API pública.
3. FastAPI crea `orders/{order_id}` en Firestore.
4. FastAPI crea una preferencia en Mercado Pago.
5. El comprador es redirigido a Checkout Pro.
6. Mercado Pago notifica `POST /webhooks/mercadopago`.
7. La API valida firma, consulta el pago real y concilia orden, pago y alertas.
8. Las back URLs `success`, `failure` y `pending` también consultan el pago real antes de mostrar resultado.

Capas:

- `routers`: HTTP y serialización.
- `services`: reglas de negocio, Mercado Pago, dinero, conciliación e idempotencia.
- `repositories`: acceso a Firestore.
- `models` y `schemas`: Pydantic.

## Firestore

Colecciones:

- `orders/{order_id}`
- `payments/{mercado_pago_payment_id}`
- `webhook_events/{event_key}`
- `payment_alerts/{alert_id}`

Los IDs son determinísticos. `external_reference` siempre coincide con `order_id`. Las alertas de conciliación usan `{type}_{order_id}_{payment_id}` para evitar duplicados.

Las reglas bloquean acceso directo desde clientes web:

```text
allow read, write: if false;
```

El SDK servidor usa IAM/Application Default Credentials y no depende de reglas cliente.

## Dinero

Los importes persistidos usan unidades mínimas:

- `Decimal("1500.00")` ARS -> `150000`
- `150000` ARS -> `Decimal("1500.00")`

No se guardan floats en Firestore. La API de Mercado Pago recibe el precio en el formato que exige su contrato.

## Variables de Entorno

Copiar `.env.example` a `.env` y completar:

```bash
cp .env.example .env
```

Nunca commitear tokens, secretos ni JSON de service account.

Variables mínimas:

- `MP_ACCESS_TOKEN`
- `MP_PUBLIC_KEY`
- `MP_WEBHOOK_SECRET`
- `BASE_URL`
- `MP_SUCCESS_URL`
- `MP_FAILURE_URL`
- `MP_PENDING_URL`
- `MP_WEBHOOK_URL`
- `GOOGLE_CLOUD_PROJECT`
- `LOCAL_FRONTEND_ORIGIN`
- `FIRESTORE_EMULATOR_HOST`

## Google Cloud

Desarrollo contra Firestore real:

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=mi-proyecto-gcp
```

Desarrollo/tests con emulador:

```bash
export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080
export GOOGLE_CLOUD_PROJECT=mp-checkout-pro-test
firebase emulators:start --only firestore
```

Producción en Google Cloud debe usar Service Account e IAM. Producción fuera de Google Cloud debe inyectar credenciales como secretos del proveedor, no como archivos versionados.

## Instalación

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Ejecución

API:

```bash
./scripts/run_local.sh
```

HTML local:

```bash
python -m http.server 5500 --directory static
```

Editar `API_BASE_URL` en `static/checkout.html` para apuntar a tu dominio público de FastAPI Cloud.

## Mercado Pago

Configurar en la app de prueba:

- Webhook: `https://mi-app.fastapicloud.com/webhooks/mercadopago`
- Success: `https://mi-app.fastapicloud.com/checkout/success`
- Failure: `https://mi-app.fastapicloud.com/checkout/failure`
- Pending: `https://mi-app.fastapicloud.com/checkout/pending`

`init_point` es la URL de Checkout Pro para credenciales productivas. `sandbox_init_point` es la URL de prueba. Con credenciales TEST normalmente usarás la sandbox.

No confiar en `?status=approved` de la back URL. La app siempre consulta `GET /v1/payments/{payment_id}`.

## Comandos Útiles

```bash
curl http://localhost:8000/health
./scripts/test_checkout.sh
./scripts/test_webhook.sh
curl http://localhost:8000/orders/{order_id}
curl http://localhost:8000/payments/{payment_id}
curl http://localhost:8000/alerts
```

## Tests y Calidad

```bash
ruff check .
ruff format .
pytest -v
```

Los tests que escriban Firestore deben exigir `FIRESTORE_EMULATOR_HOST`. Las pruebas incluidas mockean Mercado Pago y cubren salud, dinero, creación de preferencia, error de preferencia, webhooks, duplicados, alertas e invalidación de transiciones.

## Índices

`firestore.indexes.json` versiona índices para:

- órdenes por `internal_status + created_at`
- pagos por `status + date_approved`
- webhooks por `processing_status + received_at`
- alertas por `resolved + severity + created_at`

## Deploy en FastAPI Cloud

Configurar las variables de entorno en FastAPI Cloud y apuntar Mercado Pago al dominio público. No subir `.env` ni credenciales JSON. El webhook requiere HTTPS público para recibir notificaciones reales.

## Problemas Frecuentes

- `401` en webhook: revisar `MP_WEBHOOK_SECRET`, `x-signature`, `x-request-id` y `data.id`.
- No aparece la orden: verificar `GOOGLE_CLOUD_PROJECT` y si se está usando emulador.
- Checkout no inicia: revisar CORS y que `static/checkout.html` apunte a `BASE_URL` público.
- Resultado aprobado incorrecto: recordar que la UI solo debe creer en el pago verificado por API.

## Próximos Pasos

La estructura deja puntos claros para incorporar OAuth Partner, múltiples vendedores, reportes financieros, movimientos de billetera, Google Sheets, Looker Studio, Cloud Tasks, Pub/Sub y automatizaciones sin mezclar responsabilidades.

