# Arquitectura y diseño de clases — Simulador Blockchain (local, educativo)

Fecha: 2025-10-27
Autor: diseño colaborativo (borrador para revisión)

Este documento describe la arquitectura propuesta para el simulador educativo de blockchain, las responsabilidades de los componentes y un diseño detallado de las clases principales (Transaction, Block, Blockchain, Miner). Está pensado para ser claro, crítico y didáctico: cada decisión importante incluye la razón técnica y posibles alternativas.

## Resumen ejecutivo

El simulador será una aplicación Python ejecutable localmente que ofrece:
- Lógica core de blockchain en Python (clases y tests).
- UI interactiva con Streamlit para crear transacciones, mostrar mempool, minar bloques con animación de nonce/hash en tiempo real, visualizar la cadena y demostrar manipulación de bloques.
- Contenerización opcional mediante Docker para facilitar ejecución en distintas máquinas.

Se prioriza la claridad pedagógica por sobre la escala o seguridad criptográfica real. No se implementarán firmas reales ni red P2P: el objetivo es enseñar los conceptos (hashing, PoW, encadenamiento, inmutabilidad) de forma transparente.

---

## Diagrama de alto nivel (texto)

- UI Streamlit (cliente) ↔ st.session_state (estado local en memoria)
- Core Python (simulator.core): Transaction, Block, Blockchain, Miner, Storage
- Tests (pytest)
- Opcional: API local (FastAPI) y frontend cliente-only (JS)

---

## Responsabilidades por componente

1) simulator.core.transaction (Transaction)
- Validar y serializar datos de una transacción.
- Campos: sender, recipient, amount, message.
- Responsable de mantener formato estable para hashing y visualización.

2) simulator.core.block (Block)
- Mantener metadatos del bloque: index, timestamp, prev_hash, nonce, hash y lista de transacciones.
- Calcular su propio hash (método `compute_hash`) usando SHA-256 sobre una representación JSON canonical del bloque (sin el campo `hash`).
- Proveer serialización (`to_dict`) y deserialización (`from_dict`).

3) simulator.core.chain (Blockchain)
- Mantener la lista de bloques en memoria (`chain`) y `mempool` de transacciones pendientes.
- Encapsular operaciones: crear genesis, agregar transacción, minar bloque, validar cadena, tamper (editar) bloque, export/import JSON.
- Proveer métodos que retornan suficiente detalle para la UI (por bloque: válido/invalidado, razón).

4) simulator.core.miner (Miner) — opcional pero recomendable
- Encapsular la rutina de proof-of-work (PoW) para separar UI del algoritmo.
- Estado de minado (nonce actual, iteraciones, last_hash) y hooks para callbacks en UI.
- Soporta param `stop_condition` y `update_callback` para integrarse con Streamlit sin bloquear.

5) simulator.core.storage (Storage)
- Serializar la cadena a JSON en disco y restaurarla.
- Mantener formato estable y documentado.

6) UI (app.py con Streamlit)
- Formularios para crear TXs, controles de minado (start/stop, mine one), vista mempool, panel de minado con actualización en tiempo real, visualización de bloques y acción "hackear" para editar bloques antiguos.
- Indicadores visuales para bloques válidos/invalidos.

---

## Diseño detallado de clases y firmas (Python)

A continuación el diseño propuesto con tipos y descripciones. Se incluyen argumentos, retornos y excepciones esperadas.

### Transaction

Firma (conceptual):

class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float, message: Optional[str] = None) -> None
    def to_dict(self) -> dict
    @classmethod
    def from_dict(cls, d: dict) -> "Transaction"

Responsabilidades:
- Validación en constructor: sender/recipient no vacíos, amount > 0.
- to_dict(): devolver {"sender":..., "recipient":..., "amount":..., "message":...} con `message` omitido si None.

Errores:
- ValueError si datos inválidos.

### Block

Firma (conceptual):

class Block:
    def __init__(self, index: int, timestamp: str, txs: List[dict], prev_hash: str, nonce: int = 0, hash: Optional[str] = None) -> None
    def compute_hash(self) -> str
    def to_dict(self, include_hash: bool = True) -> dict
    @classmethod
    def from_dict(cls, d: dict) -> "Block"

Notas técnicas:
- `compute_hash` debe serializar un diccionario sin la key `hash` usando `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)` para estabilidad entre ejecuciones.
- `timestamp` usar formato ISO 8601 UTC (ej: 2025-10-27T14:02:03.123456Z) para legibilidad y orden.

### Blockchain

Firma (conceptual):

class Blockchain:
    def __init__(self, difficulty: int = 4) -> None
    def create_genesis_block(self) -> Block
    def add_transaction(self, tx: Transaction) -> None
    def mine_block(self, miner_callback: Optional[Callable[[int,str],None]] = None, max_txs: Optional[int] = None) -> Block
    def validate_chain(self) -> Tuple[bool, List[dict]]
    def tamper_block(self, index: int, new_data: dict, recompute_hash: bool = False) -> None
    def export_to_json(self, path: str) -> None
    def import_from_json(self, path: str) -> None

Comportamiento:
- `mine_block` toma up to `max_txs` transacciones de mempool (si None, todas) y crea un bloque con `index = len(chain)` y `prev_hash = chain[-1].hash`.
- Durante minado, se incrementa `nonce` hasta que `block.compute_hash().startswith('0'*difficulty)`; cuando `miner_callback` es provisto, se llama periódicamente con (nonce, hash) para actualizar UI.
- Al minar con éxito: set block.hash y append a chain; remover txs incluidas de mempool.
- `validate_chain` devuelve (is_valid, details) donde details es lista por bloque: {index, valid: bool, reason: Optional[str]}.

Errores/edge:
- `tamper_block` si index fuera de rango -> IndexError.
- `add_transaction` valida Transaction o lanza ValueError.

### Miner (alternativa)

Firma (conceptual):

class Miner:
    def __init__(self, difficulty: int)
    def mine(self, block_template: Block, stop_condition: Optional[Callable[[], bool]] = None, update_callback: Optional[Callable[[int,str],None]] = None, step_sleep: float = 0.01) -> Tuple[Block, bool]

Descripción:
- `mine` retorna (block, success) donde success indica si encontró nonce que cumpla difficulty o fue abortado por stop_condition.
- `update_callback` se usa para refrescar UI con (nonce, hash).
- `step_sleep` introduce pausa breve para evitar bloquear UI (usar con cuidado).

---

## Flujos importantes (ejemplos)

1) Minar un bloque (flujo UI):
- Usuario presiona "Start Mining".
- UI crea un `Block` template con txs actuales de mempool.
- UI llama a `Blockchain.mine_block(miner_callback=ui_updater)`.
- miner_callback actualiza nonce/hash en pantalla cada N iteraciones.
- Cuando se encuentra un hash válido, `mine_block` añade el bloque a la cadena y notifica a UI.

2) Hackear un bloque (demo de inmutabilidad):
- Usuario selecciona bloque índice i y edita su contenido (por ejemplo amount de TX).
- UI llama `Blockchain.tamper_block(i, new_data, recompute_hash=False)`.
- UI ejecuta `validate_chain()`, que mostrará bloque i como inconsistente (compute_hash != stored hash) y mostrará que los bloques siguientes tienen `prev_hash` inválidos.
- Opcional: UI permite "re-minar" el bloque tampered (recompute_hash + minar) y/o re-minar todos los bloques siguientes (costoso), demostrando el coste de cambiar historia.

---

## Consideraciones críticas y trade-offs

1) Threading vs loop cooperativo
- Streamlit corre en un único hilo de ejecución por request; bloquear el hilo con minado intensivo congela la UI.
- Implementación simple: minado cooperativo con `time.sleep(0.01)` y callbacks periódicos; esto es suficiente para demos y simple de implementar.
- Implementación robusta: worker thread o proceso separado (ej. `concurrent.futures.ProcessPoolExecutor`) y polling desde la UI. Añade complejidad y sincronización de estado. Recomendado para producción, no necesario para demo.

2) Persistencia
- Guardar la cadena completa como JSON en disco es suficiente. No integrar DB para mantener simplicidad.

3) Seguridad
- No implementar firmas ni validación de identidad — podría confundir a alumnos sobre garantías reales.

---

## Plan de pruebas propuesto (prioridad)

1) Unit tests básicos (obligatorio): hashing, genesis block, add/mine, validate_chain, tamper detection.
2) Test de integración UI (manual): crear TXs, minar, tamper y observar UI.

---

## Próximos pasos sugeridos

- Confirmá si querés que implemente la versión con `Miner` separado o mantengamos minado dentro de `Blockchain.mine_block` con callback. Mi recomendación: empezar con la implementación dentro de `Blockchain.mine_block` (menos archivos, más simple). Si en el futuro querés optimizar, extraemos Miner.
- Con tu OK crearé los archivos iniciales y tests (Milestone 1). Haré commits en `dev` y te mostraré el resultado.

---

Fin del documento. Revisa y dime qué cambiar.
