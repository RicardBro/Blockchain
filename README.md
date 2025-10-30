# Blockchain Local Simulator

Quick developer guide to build and run the local simulator (API, UI, miner) with Docker Compose.

Prerequisites:
- Docker (or Docker Desktop with WSL integration)
- WSL (if using Windows) or a Linux host

Common commands (from repo root):

Build images and start the stack:

```sh
make up
```

Stop the stack:

```sh
make down
```

Clean Docker artifacts (prune volumes and images):

```sh
make clean
```

Run unit tests (uses local venv if present):

```sh
make test
```

Notes to avoid rebuild churn:
- Use the provided `.dockerignore` to reduce build contexts.
- Dockerfiles copy only the minimal set of files required for each service.
- Avoid `--no-cache` unless you intentionally want a full rebuild.
- Consider adding a CI job (see `.github/workflows/ci.yml`) that runs tests and builds images in the cloud to keep local rebuilds minimal.
# Blockchain
Este repositorio es con fines educativos. Se genera un prototipo de blockchain para entender su funcionamiento y mostrarlo en presentaciones de estudio.

## Job TTL (JOB_TTL)

The API implements a simple job-claim mechanism for miners that uses files in `./data/` as claims. To make demo behavior responsive, the claim Time-To-Live is configurable via the `JOB_TTL` environment variable (seconds). A claim older than `JOB_TTL` can be "stolen" by another miner.

By default (in the provided `docker-compose.yml`) `JOB_TTL` is set to `30` seconds. Reduce it for faster claim turnover during demos, or increase it if miners should have longer exclusive time to finish work.

