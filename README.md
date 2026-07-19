# Bedreflyt Runtime Stack

This directory contains the runnable Bedreflyt software stack. The canonical entry point is `compose.yml`, which assembles the database, ontology, APIs, solver, frontend, and synthetic-data services required to execute the digital twin.

---

## Contents

- [Bedreflyt Runtime Stack](#bedreflyt-runtime-stack)
  - [Contents](#contents)
  - [Description](#description)
  - [Architecture Mapping](#architecture-mapping)
  - [Runtime Structure](#runtime-structure)
  - [Services and Ports](#services-and-ports)
  - [Prerequisites](#prerequisites)
    - [Required for the standard execution path](#required-for-the-standard-execution-path)
    - [Required only for local development outside containers](#required-only-for-local-development-outside-containers)
  - [Setup and Execution](#setup-and-execution)
    - [1. Start the full stack](#1-start-the-full-stack)
    - [2. Confirm the main interfaces](#2-confirm-the-main-interfaces)
    - [3. Stop the stack](#3-stop-the-stack)
    - [4. Rebuild only one service after a code change](#4-rebuild-only-one-service-after-a-code-change)
  - [Warm-Up and Verification](#warm-up-and-verification)
  - [Local Development](#local-development)
  - [Troubleshooting](#troubleshooting)

---

## Description

The Bedreflyt runtime stack is intended for artefact evaluation and reproducible execution. It uses Docker Compose to provide a stable multi-service deployment across operating systems while preserving the individual source trees for service-local development.

At runtime, the stack combines:

- PostgreSQL for operational patient data
- Redis for caching repeated API lookups
- Apache Jena Fuseki for ontology-backed hospital knowledge
- A Kotlin/Spring Boot API for domain data, allocation, and simulation operations
- A Kotlin/Spring Boot lifecycle manager for coordination and decision flow
- A FastAPI + Z3 solver service for allocation decisions
- A React frontend served through Nginx
- A synthetic-data generator for scenario production

---

## Architecture Mapping

The paper describes several architectural components whose relationship to the Docker services may not be immediately obvious. The table below provides a direct mapping:

| Paper Component | Docker Service | Container | Port | Key Responsibility |
|---|---|---|---|---|
| **Orchestrator** | `bf-api` | `bf-api` | `8090` | Receives patient data, coordinates allocation workflow, invokes SMOL engine, lifecycle manager, and solver |
| **SMOL Engine** | Bundled in `bf-api` | `bf-api` | `8090` | Executes 15 SMOL models for semantic reasoning and ontology reconfiguration |
| **Lifecycle Manager** | `bf-lm` | `bf-lm` | `8091` | MAPE-K Execute step: evaluates ward capacity thresholds, decides room opening/closing |
| **Z3 Solver** | `bf-solver` | `bf-solver` | `8000` | SMT constraint optimization for patient-room assignment and room opening decisions |
| **Triplestore** | `bf-fuseki` | `bf-fuseki` | `3030` | Apache Jena Fuseki with OWL Full reasoning, hosts the hospital knowledge graph |
| **Frontend** | `bf-app` | `bf-app` | `80` | React dashboard for hospital staff |
| **Database** | `bf-postgres` | `bf-postgres` | `5432` | Operational data: patients, allocations, trajectories |
| **Cache** | `bf-redis` | `bf-redis` | `6379` | Redis cache for repeated triplestore queries |

---

## Runtime Structure

| Path | Purpose |
| --- | --- |
| `compose.yml` | Main deployment entry point |
| `.env` | Environment variables consumed by the Compose stack |
| `endpoint-calls.py` | Warm-up helper for status checks and cache priming |
| `patient_202512040830.sql` | Seed patient data mounted into PostgreSQL on initialization |
| `bedreflyt-app/` | Frontend application |
| `bedreflyt-dt-api/` | Main REST API |
| `bedreflyt-dt-lifecycle-manager/` | Lifecycle-management API |
| `bedreflyt-synthetic-data-generator/` | Synthetic event and scenario generation |
| `ontology/` | Fuseki packaging and ontology assets |
| `z3/` | Solver service |
| `output/` | Generated output mounted from the synthetic-data generator |

---

## Services and Ports

| Service | Container | Port | Role |
| --- | --- | --- | --- |
| PostgreSQL | `bf-postgres` | `5432` | Primary relational data store |
| Redis | `bf-redis` | `6379` | Cache for API lookups |
| Fuseki | `bf-fuseki` | `3030` | Triplestore and ontology endpoint |
| Main API | `bf-api` | `8090` | Patient, allocation, simulation, and triplestore REST API |
| Lifecycle Manager | `bf-lm` | `8091` | Coordination and lifecycle-related API |
| Solver | `bf-solver` | `8000` | FastAPI-based Z3 optimization service |
| Frontend | `bf-app` | `80` | Web UI |
| Synthetic Generator | `bf-synth-gen` | none exposed | Writes generated outputs to `output/` |

---

## Prerequisites

### Required for the standard execution path

- Docker Engine or Docker Desktop with Docker Compose v2
- An available host port set for `80`, `5432`, `6379`, `8000`, `8090`, `8091`, and `3030`

### Required only for local development outside containers

- Java 21 for `bedreflyt-dt-api/` and `bedreflyt-dt-lifecycle-manager/`
- Node.js 18 and npm for `bedreflyt-app/`
- Python 3.11 or newer for `z3/`, `endpoint-calls.py`, and `bedreflyt-synthetic-data-generator/`

---

## Setup and Execution

All commands below are run from this directory.

### 1. Start the full stack

```bash
docker compose up --build -d
```

### 2. Confirm the main interfaces

- Frontend: `http://localhost:80`
- Main API Swagger UI: `http://localhost:8090/swagger-ui.html`
- Main API OpenAPI spec: `http://localhost:8090/api-docs`
- Lifecycle Manager Swagger UI: `http://localhost:8091/swagger-ui.html`
- Lifecycle Manager OpenAPI spec: `http://localhost:8091/api-docs`
- Fuseki UI: `http://localhost:3030`
- Solver root: `http://localhost:8000`

### 3. Stop the stack

```bash
docker compose down
```

To also remove persistent volumes:

```bash
docker compose down -v
```

### 4. Rebuild only one service after a code change

```bash
docker compose up --build -d <service-name>
```

Example service names include `bf-api`, `bf-lm`, `bf-app`, `bf-solver`, and `bf-synth-gen`.

---

## Warm-Up and Verification

The stack can need a short stabilization period after startup because the API depends on PostgreSQL, Fuseki, and Redis, and the frontend can be queried before the cached endpoints are primed.

Use the included helper script to wait for readiness and then hit the key ontology-backed endpoints:

```bash
python endpoint-calls.py
```

Note that the script may take a few minutes to complete. It checks the health of the main API and lifecycle manager, then performs a series of status calls to warm up the cache.

The script checks:

- `http://localhost:8090/api/v1/status`

and then warms these API routes:

- `/api/v1/fuseki/rooms`
- `/api/v1/fuseki/diagnosis`
- `/api/v1/fuseki/treatments`
- `/api/v1/fuseki/wards`
- `/api/v1/fuseki/`

---

## Local Development

Compose is the recommended path for artefact evaluation. Run components locally only when you need service-specific iteration.

| Component | Local stack |
| --- | --- |
| `bedreflyt-dt-api/` | Gradle + Java 21 + Kotlin |
| `bedreflyt-dt-lifecycle-manager/` | Gradle + Java 21 + Kotlin |
| `bedreflyt-app/` | Node.js 18 + npm |
| `z3/` | Python + FastAPI + z3-solver |
| `bedreflyt-synthetic-data-generator/` | Python package installable with `pip install -e .` |

Use the service-local README files for build, run, and dependency details.

---

## Troubleshooting

**A container fails to start because a published port is unavailable**  
Change the corresponding port mapping in `compose.yml` and restart the stack.

**The frontend loads but some data-backed views are incomplete**  
Wait for the services to settle and then run `python endpoint-calls.py` to warm the API-backed cache paths.

**The API or lifecycle manager is reachable but missing documentation endpoints**  
Use `/swagger-ui.html` for the UI and `/api-docs` for the OpenAPI document on ports `8090` and `8091` respectively.

**You changed a single service and do not want to restart everything**  
Run `docker compose up --build -d <service-name>` from this directory.

**Caching issues with the frontend**
If the frontend is not reflecting recent changes, clear the browser cache or use a private/incognito window to bypass cached assets.
In case, delete the Local Storage for the frontend domain in your browser's developer tools to reset any stored state that may be causing inconsistencies.
