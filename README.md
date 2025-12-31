# WedPlan

Wedding seating optimization service using OR-Tools CP-SAT solver.

## Features

- **Optimal Seating**: Finds seating arrangements that maximize guest affinity scores
- **Partner Adjacency**: Partners are automatically seated adjacent to each other
- **Same-Table Constraints**: Force specific groups to share a table
- **Circular Tables**: Properly handles circular adjacency for round tables
- **Strict Validation**: Pydantic v2 strict mode for type-safe request/response handling

## Tech Stack

- **Python 3.12+**
- **FastAPI** - Modern async web framework
- **Pydantic v2** - Data validation with strict mode
- **OR-Tools CP-SAT** - Constraint programming solver
- **uv** - Fast Python package manager

## Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/wedplan.git
cd wedplan

# Install dependencies
uv sync
```

## Running the Service

### Development Server

```bash
uv run fastapi dev backend/wedplan/api/main.py
```

The API will be available at `http://localhost:8000`.

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "ok", "version": "0.1.0"}
```

### Optimize Seating

```bash
curl -X POST http://localhost:8000/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "tables": [
      {"id": "table1", "capacity": 6},
      {"id": "table2", "capacity": 6}
    ],
    "guests": [
      {"id": "alice", "name": "Alice", "partner_id": "bob"},
      {"id": "bob", "name": "Bob", "partner_id": "alice"},
      {"id": "carol", "name": "Carol"},
      {"id": "dave", "name": "Dave"},
      {"id": "eve", "name": "Eve"},
      {"id": "frank", "name": "Frank"}
    ],
    "affinities": [
      {"a": "alice", "b": "carol", "score": 80},
      {"a": "bob", "b": "dave", "score": 70},
      {"a": "carol", "b": "eve", "score": 90},
      {"a": "dave", "b": "frank", "score": 60}
    ],
    "options": {
      "time_limit_seconds": 5.0,
      "allow_empty_seats": true
    }
  }'
```

Response:
```json
{
  "status": "OPTIMAL",
  "objective_value": 240,
  "tables": [
    {
      "table_id": "table1",
      "seats": [
        {"seat_index": 0, "guest_id": "alice", "guest_name": "Alice"},
        {"seat_index": 1, "guest_id": "bob", "guest_name": "Bob"},
        {"seat_index": 2, "guest_id": "carol", "guest_name": "Carol"},
        {"seat_index": 3, "guest_id": null, "guest_name": null},
        {"seat_index": 4, "guest_id": null, "guest_name": null},
        {"seat_index": 5, "guest_id": null, "guest_name": null}
      ]
    },
    {
      "table_id": "table2",
      "seats": [
        {"seat_index": 0, "guest_id": "dave", "guest_name": "Dave"},
        {"seat_index": 1, "guest_id": "eve", "guest_name": "Eve"},
        {"seat_index": 2, "guest_id": "frank", "guest_name": "Frank"},
        {"seat_index": 3, "guest_id": null, "guest_name": null},
        {"seat_index": 4, "guest_id": null, "guest_name": null},
        {"seat_index": 5, "guest_id": null, "guest_name": null}
      ]
    }
  ],
  "solver_stats": {
    "conflicts": 0,
    "branches": 12,
    "wall_time_seconds": 0.023
  }
}
```

## Development

### Run Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run mypy backend
```

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

## Project Structure

```
backend/wedplan/
├── api/                 # FastAPI application
│   ├── main.py          # App factory
│   ├── routes.py        # Router registration
│   └── v1/              # API v1 endpoints
│       ├── health.py
│       └── optimize.py
├── core/                # Configuration
│   ├── config.py
│   └── logging.py
├── domain/              # Domain models
│   ├── models.py        # Pydantic models
│   └── errors.py        # Exception types
└── solver/              # OR-Tools CP-SAT solver
    ├── cp_sat.py        # Main solver
    ├── mapping.py       # ID mappings
    ├── constraints.py   # Constraint builders
    ├── objective.py     # Objective function
    └── extract.py       # Solution extraction
```

## Constraint Model

The solver uses CP-SAT boolean variables:

- `x[g, t, s]`: Guest `g` sits at table `t` seat `s`
- `y[g, t]`: Guest `g` sits at table `t` (any seat)

### Constraints

1. **Assignment**: Each guest assigned exactly one seat
2. **Capacity**: Each seat has at most one guest
3. **Partner Adjacency**: Partners must be at adjacent seats
4. **Same-Table**: Specified groups must share a table

### Objective

Maximize total affinity score for guests at the same table,
with optional adjacency bonus for neighboring seats.

## License

MIT
