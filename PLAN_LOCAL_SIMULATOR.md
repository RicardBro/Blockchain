# Plan de trabajo (adaptado a ejecución 100% local)
Versión: borrador  
Fecha: 2025-10-27  
Autor: Copilot (borrador para revisión por RicardBro)

## Objetivo
Crear un simulador de blockchain con UI interactiva y herramientas auxiliares, diseñado para ejecutarse íntegramente de forma local (sin servicios en la nube, sin llamadas externas). Se prioriza: arquitectura limpia, código modular y facilidad de uso para demostraciones educativas.

## Restricciones y decisiones clave (local-only)
- No habrá backend hospedado en la nube. Todo debe poder ejecutarse en la máquina del usuario.
- La UI debe poder correr en el navegador local (apertura directa de archivos o servidor HTTP local).
- Opcionalmente el backend (Python) podrá ejecutarse localmente como servicio (FastAPI) para desarrollo avanzado, pero nunca desplegaremos nada en la nube por este plan.
- Registro (logging) amplio y configurable para fines educativos.
- No conexiones externas, no telemetría, no subida automática de datos.
- Entorno recomendado: Python 3.11 (estable), Node.js (para frontend) solo si se elige frontend React; ambos pueden ejecutarse localmente.

## Resultado esperado
- Paquete Python modular (simulator/core) con clases: Block, Chain, Miner (separadas en archivos).
- CLI para interactuar con el simulador (crear tx, minar, ver cadena).
- UI interactiva que se ejecuta en el navegador sin necesidad de backend (simulación en cliente) — alternativa: UI que consume un backend local si se quiere.
- Tests automatizados (pytest).
- Dockerfile(s) y docker-compose para correr todo localmente si se prefiere contenerización.
- Documentación de uso local paso a paso.

## Arquitectura propuesta (local)
- Core (Python): lógica de la blockchain (block, chain, consensus/miner, utils).
- CLI (Python): interfaz de línea de comandos para demos.
- API (opcional, Python FastAPI): servicio local para exponer simulador por HTTP (solo para quienes quieran correr backend local).
- Frontend (opcional): app React + Vite o app HTML/JS simple que corre la simulación directamente en el navegador y/o consume la API local.
- Tests: pytest.
- Dev tooling: black, flake8, isort; precommit opcionales.

Diagrama (texto):
- Usuario -> (CLI) -> simulator.core -> almacén local (JSON)  
- Usuario -> (Navegador) -> frontend (JS) -> simula internamente OR -> frontend -> (HTTP) -> backend local (FastAPI) -> simulator.core

## Estrategia de implementación por iteraciones (milestones locales)
Milestone 1 — Core local y tests (entrega inicial)
- Implementar clases separadas: Block, Chain, Miner.
- API de persistencia simple: export/import de cadena a JSON en disco.
- Tests unitarios básicos (block integrity, chain append, mining).
- README con instrucciones para ejecutar localmente.
- Branch: `dev` (primer PR hacia `main` cuando autorices).

Milestone 2 — CLI y docs
- CLI usando Click para operaciones: crear tx, ver chain, minar, exportar/importar, ajustar difficulty, ver logs.
- Ejemplos de uso (comandos) en README.
- Configuración de logging (archivo + consola, niveles DEBUG/INFO/WARN/ERROR).

Milestone 3 — UI interactiva local (cliente)
- Frontend que corre en el navegador y contiene una implementación JS/TS del simulador (o puede comunicarse con backend local cuando esté activo).
- Opción preferida: frontend que simula todo en cliente (no requiere backend) — ideal para demos y GitHub Pages si luego se quisiera.
- Alternativa: frontend que consume un backend local (FastAPI) para mostrar cómo sería una arquitectura cliente/servidor, pero este backend solo se usa localmente.

Milestone 4 — Contenerización y ejemplos de despliegue local
- Dockerfile para backend (si existe) y para servir frontend estático.
- docker-compose.yml para levantar todo localmente (no en la nube).
- Scripts para crear imágenes y ejecutar contenedores en la máquina local.

## Stack recomendado (local)
- Python >=3.11
- Click (CLI)
- pytest (tests)
- black, flake8, isort (formato/lint)
- logging (módulo estándar) + RotatingFileHandler
- Opcional: FastAPI + uvicorn (si querés API local)
- Frontend opcional: React + Vite (TypeScript) o una app JS mínima (vanilla) que lee/escribe JSON y usa localStorage

## Layout de proyecto sugerido
- simulator/                  # paquete Python
  - core/
    - block.py
    - chain.py
    - miner.py
    - storage.py   # export/import JSON
    - __init__.py
  - cli/
    - cli.py       # Click CLI
  - api/
    - app.py       # FastAPI app (opcional)
  - __init__.py
- web/                       # frontend (opcional)
  - public/
  - src/
  - package.json
- tests/
  - test_block.py
  - test_chain.py
- Dockerfile
- docker-compose.yml
- requirements.txt
- README.md
- PLAN_LOCAL_SIMULATOR.md   # este documento
- .flake8, pyproject.toml, .pre-commit-config.yaml (opcionales)

## Configuración e instrucciones locales (pasos detallados)

Requisitos (instalar localmente):
- Python 3.11
- pip (o pipx)
- Docker (opcional, si vas a usar contenedores)
- Node.js + npm (solo si usarás frontend React)

1) Clonar repo y crear branch de trabajo
- git clone <repo_url>
- cd Blockchain
- git checkout -b dev

2) Entorno Python y dependencias
- python3.11 -m venv .venv
- source .venv/bin/activate    (Windows: .venv\Scripts\activate)
- pip install -r requirements.txt

requirements.txt (ejemplo mínimo)
- click
- pytest
- black
- flake8
- isort
- (opcional) fastapi
- (opcional) uvicorn[standard]

3) Ejecutar tests localmente
- pytest -q
- coverage run -m pytest && coverage report -m

4) Ejecutar CLI localmente (ejemplos)
- python -m simulator.cli.cli init --output chain.json
- python -m simulator.cli.cli mine --difficulty 3 --chain chain.json
- python -m simulator.cli.cli show --chain chain.json

5) Ejecutar API local (opcional)
- uvicorn simulator.api.app:app --reload --port 8000
- Luego abrir http://localhost:8000/docs para ver endpoints (solo local)

6) Ejecutar frontend local (opcional cliente-only)
Opción simple (sin Node): abrir web/index.html en el navegador (file://) si está diseñado para correr sin servidor.
Con Node (React/Vite):
- cd web
- npm install
- npm run dev  (o build + serve estático)

7) Usar Docker local (opcional)
- docker build -t simulator-backend .
- docker run --rm -p 8000:8000 simulator-backend
Con docker-compose:
- docker-compose up --build
Esto levanta servicios solo en tu máquina local.

## Logging y persistencia local
- Logging: usar logging.getLogger + RotatingFileHandler (archivo `simulator.log`) y consola.
- Nivel por defecto: DEBUG para demos; variable de entorno o flag CLI para ajustar.
- Persistencia: export/import cadena a JSON (`storage.py`) en disco; alternativa para UI: usar localStorage en navegador.

## Seguridad y privacidad
- No se debe permitir envio de datos a servicios externos.
- No incluir claves/credenciales.
- El almacenamiento local (JSON o localStorage) es suficiente para demostraciones.

## Tests y calidad
- Tests unitarios con pytest para clases core.
- Cobertura objetivo >= 80% (configurable).
- Formateo automático con black; linting con flake8.
- Pre-commit hooks opcionales para aplicar formato antes de commits.

## Flujo de trabajo (local PRs / ramas)
- Branch principal de desarrollo: `dev`.
- Hacer PRs pequeños desde ramas temáticas (ej.: `feat/core-block`, `feat/cli`).
- Revisar y mergear a `main` solo cuando estén listos para release local.

## Qué voy a hacer (cuando des el OK)
- Crear la rama `dev` y commitear la Milestone 1: core modular + tests + README mínimo + requirements.txt + Dockerfile básico.
- No subiré nada a la nube ni activaré despliegues automáticos.
- Te mostraré cada archivo antes de commitearlo si querés revisarlo.

## Preguntas para confirmar antes de implementar
- ¿Querés que la UI sea cliente-only (recomendada) o preferís desde el principio soporte para un backend local con FastAPI? (Recomendado: cliente-only para demos).
- ¿Querés que deje los archivos de configuración de linters/formatters por defecto o los omitimos y los agregamos más adelante?
- ¿Querés que incluya docker-compose ya en la Milestone 1 o lo dejamos para Milestone 4?

---

Fin del borrador. Por favor indicame los cambios o confirmá si lo dejo tal cual para crear el archivo PLAN_LOCAL_SIMULATOR.md y empezar a implementar la Milestone 1 en la rama `dev`.