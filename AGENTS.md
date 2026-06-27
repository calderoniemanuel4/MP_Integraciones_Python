# Reglas para agentes

- Mantener tipado, Pydantic y separación router -> service -> repository -> Firestore.
- No usar SQL, SQLite, SQLAlchemy, SQLModel ni bases relacionales.
- No hardcodear secretos ni commitear credenciales Google.
- Usar Firestore Emulator para tests que escriben datos; nunca tests contra producción.
- Usar IDs determinísticos para órdenes, pagos, webhooks y alertas.
- Mantener idempotencia de webhooks, pagos, órdenes y alertas.
- Usar unidades mínimas para dinero y no persistir importes como float.
- No hacer llamadas HTTP dentro de transacciones Firestore.
- Agregar tests a nuevas funcionalidades.
- Consultar siempre el pago real en Mercado Pago.
- No confiar en datos del frontend, webhooks o back URLs como única fuente de verdad.
- No revertir estados sin validación.
- Preservar compatibilidad con FastAPI Cloud.
- Versionar índices y bloquear acceso directo frontend a Firestore.

