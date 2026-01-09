<p align="center">
  <h1 align="center">PocketSmith MCP Server</h1>
  <p align="center">
    <strong>A production-ready MCP server for the PocketSmith personal finance API</strong>
  </p>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://pypi.org/project/pocketsmith-mcp/"><img src="https://img.shields.io/pypi/v/pocketsmith-mcp.svg" alt="PyPI"></a>
  <a href="https://github.com/your-repo/pocketsmith-mcp/actions"><img src="https://img.shields.io/github/actions/workflow/status/your-repo/pocketsmith-mcp/test.yml?label=tests" alt="Tests"></a>
  <a href="https://codecov.io/gh/your-repo/pocketsmith-mcp"><img src="https://img.shields.io/codecov/c/github/your-repo/pocketsmith-mcp" alt="Coverage"></a>
</p>

<p align="center">
  <a href="#features">Features</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#available-tools">Tools</a> &bull;
  <a href="#testing">Testing</a> &bull;
  <a href="#development">Development</a>
</p>

---

## Features

- **43 MCP Tools** - Complete coverage of PocketSmith API v2 endpoints
- **Production Ready** - Rate limiting, retry with exponential backoff, circuit breaker
- **Universal Compatibility** - Works with Claude Desktop, Cursor, and any MCP-compatible client
- **Type Safe** - Pydantic models for all API entities

---

## Quick Start

### Installation

```bash
# Run directly with uvx (recommended)
uvx pocketsmith-mcp

# Or install with pip
pip install pocketsmith-mcp
```

### Configuration

1. **Get your API key** from [PocketSmith Settings](https://my.pocketsmith.com/settings/api)

2. **Set your environment variable:**

```bash
export POCKETSMITH_API_KEY=your_api_key_here
```

3. **Run the server:**

```bash
uvx pocketsmith-mcp
```

---

## Claude Desktop Integration

Add to your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pocketsmith": {
      "command": "uvx",
      "args": ["pocketsmith-mcp"],
      "env": {
        "POCKETSMITH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

---

## Available Tools

<details>
<summary><strong>User Management</strong></summary>

| Tool | Description |
|------|-------------|
| `get_current_user` | Get authenticated user info |
| `get_user` | Get user by ID |
| `update_user` | Update user settings |

</details>

<details>
<summary><strong>Account Management</strong></summary>

| Tool | Description |
|------|-------------|
| `list_accounts` | List all accounts |
| `get_account` | Get account details |
| `update_account` | Update account |
| `delete_account` | Delete account |

</details>

<details>
<summary><strong>Transaction Accounts</strong></summary>

| Tool | Description |
|------|-------------|
| `list_transaction_accounts` | List transaction accounts |
| `get_transaction_account` | Get transaction account details |
| `update_transaction_account` | Update transaction account |

</details>

<details>
<summary><strong>Transactions</strong></summary>

| Tool | Description |
|------|-------------|
| `list_transactions` | List transactions with filters |
| `get_transaction` | Get transaction details |
| `create_transaction` | Create new transaction |
| `update_transaction` | Update transaction |
| `delete_transaction` | Delete transaction |

</details>

<details>
<summary><strong>Categories</strong></summary>

| Tool | Description |
|------|-------------|
| `list_categories` | List all categories |
| `get_category` | Get category details |
| `create_category` | Create new category |
| `update_category` | Update category |
| `delete_category` | Delete category |

</details>

<details>
<summary><strong>Budgeting</strong></summary>

| Tool | Description |
|------|-------------|
| `get_budget` | Get budget data |
| `get_budget_summary` | Get budget summary |
| `get_trend_analysis` | Get spending trends |
| `clear_forecast_cache` | Clear forecast cache |

</details>

<details>
<summary><strong>Institutions</strong></summary>

| Tool | Description |
|------|-------------|
| `list_institutions` | List financial institutions |
| `get_institution` | Get institution details |
| `create_institution` | Create institution |
| `update_institution` | Update institution |
| `delete_institution` | Delete institution |

</details>

<details>
<summary><strong>Events (Budget Calendar)</strong></summary>

| Tool | Description |
|------|-------------|
| `list_events` | List budget events |
| `get_event` | Get event details |
| `create_event` | Create budget event |
| `update_event` | Update event |
| `delete_event` | Delete event |

</details>

<details>
<summary><strong>Attachments</strong></summary>

| Tool | Description |
|------|-------------|
| `list_attachments` | List attachments |
| `get_attachment` | Get attachment details |
| `create_attachment` | Upload attachment |
| `update_attachment` | Update attachment |
| `delete_attachment` | Delete attachment |

</details>

<details>
<summary><strong>Labels & Searches</strong></summary>

| Tool | Description |
|------|-------------|
| `list_labels` | List all labels |
| `list_saved_searches` | List saved searches |

</details>

<details>
<summary><strong>Utilities</strong></summary>

| Tool | Description |
|------|-------------|
| `list_currencies` | List supported currencies |
| `list_time_zones` | List supported time zones |

</details>

---

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/pocketsmith_mcp --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/tools/test_transactions.py

# Run tests by marker
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
uv run pytest -m e2e           # End-to-end tests (requires API key)
```

### Test Structure

```
tests/
├── unit/                 # Fast, isolated tests with mocked API
│   ├── test_api_client.py
│   ├── test_rate_limiter.py
│   ├── test_circuit_breaker.py
│   └── tools/            # Tool-specific unit tests
├── integration/          # Tests with mocked HTTP responses
│   ├── test_server.py
│   └── test_tools.py
└── conftest.py           # Shared fixtures
```

### Coverage

The project maintains a **70% coverage threshold**. Coverage reports are generated automatically:

```bash
uv run pytest --cov=src/pocketsmith_mcp --cov-report=html
open htmlcov/index.html
```

---

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/pocketsmith-mcp.git
cd pocketsmith-mcp

# Install dependencies (including dev)
uv sync --dev

# Copy environment template
cp .env.example .env
# Edit .env and add your API key
```

### Architecture

```
pocketsmith-mcp/
├── src/pocketsmith_mcp/
│   ├── __main__.py       # Entry point
│   ├── server.py         # FastMCP server setup
│   ├── config.py         # Environment configuration
│   ├── client/           # API client with resilience patterns
│   │   ├── api_client.py     # HTTP client wrapper
│   │   ├── rate_limiter.py   # Token bucket algorithm
│   │   ├── circuit_breaker.py # Fault tolerance
│   │   └── retry.py          # Exponential backoff
│   ├── models/           # Pydantic data models
│   └── tools/            # MCP tool implementations
└── tests/                # Unit and integration tests
```

### API Resilience

The client includes production-grade resilience:

- **Rate Limiting** - Token bucket algorithm (60 req/min default)
- **Retry Logic** - Exponential backoff with jitter for transient failures
- **Circuit Breaker** - Prevents cascade failures during outages

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POCKETSMITH_API_KEY` | Yes | - | Your PocketSmith API key |
| `DEBUG` | No | `false` | Enable debug logging |
| `API_TIMEOUT` | No | `30` | Request timeout (seconds) |
| `MAX_RETRIES` | No | `3` | Retry attempts for failed requests |
| `RATE_LIMIT_PER_MINUTE` | No | `60` | API rate limit |

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with Python and FastMCP
</p>
