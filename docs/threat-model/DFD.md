# Data Flow Diagram — Workout Tracking API

Нотация: узлы и хранилища с trust boundaries; потоки пронумерованы F1…F12.
Boundary уровни: **Client** / **Edge** / **Core** / **Data**.

## DFD — Контекст/Контур

```mermaid
flowchart LR
  %% Boundaries
  subgraph B1[Client / Untrusted Zone]
    U[User (Athlete)]
    A[Admin (Ops)]
  end

  subgraph B2[Edge / Semi-Trusted]
    RP[Reverse Proxy / API Gateway (TLS termination, rate-limit)]
  end

  subgraph B3[Core / Trusted App Zone]
    API[FastAPI Service<br/>/workouts,/auth,/metrics]
    BG[Background Worker (optional)]
    MET[Prometheus Client SDK]
  end

  subgraph B4[Data / Trusted Data Zone]
    PG[(PostgreSQL)]
    RD[(Redis Cache)]
  end

  %% External
  CI[GitHub Actions / CI]:::ext

  %% Classes
  classDef ext fill:#fff,border:2px dashed #999,color:#333;

  %% Flows (labeled)
  U -- F1: HTTPS JSON (Auth/Login, JWT) --> RP
  RP -- F2: mTLS HTTP/1.1 to Core --> API
  API -- F3: SQL (TLS) R/W --> PG
  API -- F4: Redis GET/SET --> RD
  API -- F5: Metrics /scrape --> MET
  CI -- F6: CI Webhook/Artifacts --> RP
  A -- F7: HTTPS Admin Ops --> RP
  RP -- F8: to Core (admin) --> API
  API -- F9: Events/Tasks --> BG
  BG -- F10: SQL (TLS) --> PG
  BG -- F11: Redis --> RD
  MET -- F12: Pull by Prometheus ---> |/metrics| ExtPrometheus

  %% Notes
  note right of RP: TLS 1.2+, HSTS, Rate limiting, CORS
  note right of API: JWT auth, schema validation, RFC7807 errors
  note right of PG: At-rest encryption, least-privilege user
