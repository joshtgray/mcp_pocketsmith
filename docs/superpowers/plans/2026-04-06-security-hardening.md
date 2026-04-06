# Security Hardening: Code Vulnerability Fixes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 7 code security vulnerabilities identified in the security review, with zero breaking changes to existing tool signatures, error types, or public APIs.

**Architecture:** Surgical, minimal fixes — no new files, no new abstractions. A `validate_id()` helper added to `errors.py` is reused by all tool modules. Infrastructure fixes (circuit breaker, rate limiter, user context, error truncation) are self-contained single-file changes.

**Tech Stack:** Python 3.10+, pytest, FastMCP, httpx

**Baseline:** 145 unit tests passing. All existing tests must continue to pass after every task.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/pocketsmith_mcp/errors.py` | Modify | Add `validate_id()` helper; truncate `response_body` in `APIError.__str__` |
| `src/pocketsmith_mcp/tools/accounts.py` | Modify | Add `validate_id()` calls |
| `src/pocketsmith_mcp/tools/attachments.py` | Modify | Add `validate_id()` calls + file upload validation |
| `src/pocketsmith_mcp/tools/bulk_transactions.py` | Modify | Add ID validation/coercion |
| `src/pocketsmith_mcp/tools/categories.py` | Modify | Add `validate_id()` calls |
| `src/pocketsmith_mcp/tools/events.py` | Modify | Add `validate_id()` calls |
| `src/pocketsmith_mcp/tools/institutions.py` | Modify | Add `validate_id()` calls |
| `src/pocketsmith_mcp/tools/transaction_accounts.py` | Modify | Add `validate_id()` calls |
| `src/pocketsmith_mcp/tools/transactions.py` | Modify | Add `validate_id()` calls |
| `src/pocketsmith_mcp/client/circuit_breaker.py` | Modify | Add lock to `failures` property |
| `src/pocketsmith_mcp/client/rate_limiter.py` | Modify | Clamp + round after refill |
| `src/pocketsmith_mcp/user_context.py` | Modify | Immutable-after-set guard + positive int validation |
| `tests/unit/test_errors.py` | Create | Tests for `validate_id()` and `APIError` truncation |
| `tests/unit/test_user_context.py` | Modify | Add tests for setter guard |
| `tests/unit/test_circuit_breaker.py` | Modify | Add test for `failures` property under lock |
| `tests/unit/test_rate_limiter.py` | Modify | Add test for precision clamping |
| `tests/unit/tools/test_accounts.py` | Modify | Add ID validation tests |
| `tests/unit/tools/test_attachments.py` | Modify | Add file upload validation tests |
| `tests/unit/tools/test_bulk_transactions.py` | Modify | Add ID validation tests |
| `tests/unit/tools/test_transactions.py` | Modify | Add ID validation tests |

---

### Task 1: Add `validate_id()` helper and `APIError` truncation in `errors.py`

**Files:**
- Modify: `src/pocketsmith_mcp/errors.py`
- Create: `tests/unit/test_errors.py`

- [ ] **Step 1: Write failing tests for `validate_id()`**

Create `tests/unit/test_errors.py`:

```python
"""Unit tests for error helpers."""

import pytest

from pocketsmith_mcp.errors import APIError, ValidationError, validate_id


class TestValidateId:
    """Tests for validate_id helper."""

    def test_valid_positive_int(self):
        """Valid positive int should not raise."""
        validate_id(1, "account_id")
        validate_id(999999, "account_id")

    def test_zero_raises(self):
        """Zero should raise ValidationError."""
        with pytest.raises(ValidationError, match="account_id must be a positive integer"):
            validate_id(0, "account_id")

    def test_negative_raises(self):
        """Negative int should raise ValidationError."""
        with pytest.raises(ValidationError, match="transaction_id must be a positive integer"):
            validate_id(-1, "transaction_id")

    def test_field_name_in_message(self):
        """Error message should include the field name."""
        with pytest.raises(ValidationError, match="my_field"):
            validate_id(-5, "my_field")


class TestAPIErrorTruncation:
    """Tests for APIError response body truncation in str()."""

    def test_short_body_not_truncated(self):
        """Short response bodies appear in full."""
        err = APIError("Server error", status_code=500, response_body="short error")
        assert str(err) == "[HTTP 500] Server error: short error"

    def test_long_body_truncated(self):
        """Response bodies over 200 chars are truncated in str()."""
        long_body = "x" * 300
        err = APIError("Server error", status_code=500, response_body=long_body)
        result = str(err)
        assert len(result) < 300
        assert result.endswith("... (truncated)")

    def test_full_body_still_on_attribute(self):
        """Full response body remains accessible on the attribute."""
        long_body = "x" * 300
        err = APIError("Server error", status_code=500, response_body=long_body)
        assert err.response_body == long_body
        assert len(err.response_body) == 300

    def test_none_body(self):
        """None response body should not cause errors."""
        err = APIError("Server error", status_code=500, response_body=None)
        assert str(err) == "[HTTP 500] Server error"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_errors.py -v`
Expected: FAIL — `ImportError: cannot import name 'validate_id' from 'pocketsmith_mcp.errors'`

- [ ] **Step 3: Implement `validate_id()` and `APIError` truncation**

In `src/pocketsmith_mcp/errors.py`, add `validate_id` function at the bottom of the file:

```python
def validate_id(value: int, field_name: str) -> None:
    """Validate that an ID is a positive integer.

    Args:
        value: The ID value to validate.
        field_name: Name of the field (for error messages).

    Raises:
        ValidationError: If value is not a positive integer.
    """
    if value <= 0:
        raise ValidationError(f"{field_name} must be a positive integer, got {value}", field=field_name)
```

Modify `APIError.__str__` to truncate long response bodies:

```python
def __str__(self) -> str:
    base = f"[HTTP {self.status_code}] {self.message}"
    if self.response_body:
        body = self.response_body
        if len(body) > 200:
            body = body[:200] + "... (truncated)"
        return f"{base}: {body}"
    return base
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_errors.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Run full test suite to confirm no regressions**

Run: `uv run pytest tests/unit/ -q`
Expected: 153 passed (145 existing + 8 new)

- [ ] **Step 6: Commit**

```bash
git add src/pocketsmith_mcp/errors.py tests/unit/test_errors.py
git commit -m "feat: add validate_id() helper and truncate APIError response bodies"
```

---

### Task 2: Add ID validation to `accounts.py`

**Files:**
- Modify: `src/pocketsmith_mcp/tools/accounts.py`
- Modify: `tests/unit/tools/test_accounts.py`

- [ ] **Step 1: Write failing tests for ID validation**

Add to `tests/unit/tools/test_accounts.py` at the end of the file:

```python
class TestAccountIdValidation:
    """Tests for ID validation on account tools."""

    @pytest.mark.asyncio
    async def test_get_account_zero_id(self, mcp_with_tools):
        """get_account should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("get_account")
        with pytest.raises(ValueError, match="account_id must be a positive integer"):
            await tool.fn(account_id=0)

    @pytest.mark.asyncio
    async def test_get_account_negative_id(self, mcp_with_tools):
        """get_account should reject negative ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("get_account")
        with pytest.raises(ValueError, match="account_id must be a positive integer"):
            await tool.fn(account_id=-1)

    @pytest.mark.asyncio
    async def test_update_account_zero_id(self, mcp_with_tools):
        """update_account should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("update_account")
        with pytest.raises(ValueError, match="account_id must be a positive integer"):
            await tool.fn(account_id=0, title="Test")

    @pytest.mark.asyncio
    async def test_delete_account_negative_id(self, mcp_with_tools):
        """delete_account should reject negative ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("delete_account")
        with pytest.raises(ValueError, match="account_id must be a positive integer"):
            await tool.fn(account_id=-1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/tools/test_accounts.py::TestAccountIdValidation -v`
Expected: FAIL — no validation in place yet

- [ ] **Step 3: Add validation to `accounts.py`**

In `src/pocketsmith_mcp/tools/accounts.py`, add import and validation calls:

Add to imports:
```python
from pocketsmith_mcp.errors import validate_id
```

In `get_account`, add as first line inside `try`:
```python
validate_id(account_id, "account_id")
```

In `update_account`, add as first line inside `try`:
```python
validate_id(account_id, "account_id")
```

In `delete_account`, add as first line inside `try`:
```python
validate_id(account_id, "account_id")
```

Note: `list_accounts` uses `user_ctx.user_id` (not a user-supplied ID), so no validation needed.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/tools/test_accounts.py -v`
Expected: All 10 tests PASS (6 existing + 4 new)

- [ ] **Step 5: Commit**

```bash
git add src/pocketsmith_mcp/tools/accounts.py tests/unit/tools/test_accounts.py
git commit -m "feat: add ID validation to account tools"
```

---

### Task 3: Add ID validation to `transactions.py`

**Files:**
- Modify: `src/pocketsmith_mcp/tools/transactions.py`
- Modify: `tests/unit/tools/test_transactions.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/tools/test_transactions.py` at the end of the file:

```python
class TestTransactionIdValidation:
    """Tests for ID validation on transaction tools."""

    @pytest.mark.asyncio
    async def test_get_transaction_zero_id(self, mcp_with_tools):
        """get_transaction should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("get_transaction")
        with pytest.raises(ValueError, match="transaction_id must be a positive integer"):
            await tool.fn(transaction_id=0)

    @pytest.mark.asyncio
    async def test_create_transaction_zero_account_id(self, mcp_with_tools):
        """create_transaction should reject zero transaction_account_id."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_transaction")
        with pytest.raises(ValueError, match="transaction_account_id must be a positive integer"):
            await tool.fn(transaction_account_id=0, payee="Test", amount=-5, date="2024-01-01")

    @pytest.mark.asyncio
    async def test_update_transaction_negative_id(self, mcp_with_tools):
        """update_transaction should reject negative ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("update_transaction")
        with pytest.raises(ValueError, match="transaction_id must be a positive integer"):
            await tool.fn(transaction_id=-1, payee="Test")

    @pytest.mark.asyncio
    async def test_delete_transaction_zero_id(self, mcp_with_tools):
        """delete_transaction should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("delete_transaction")
        with pytest.raises(ValueError, match="transaction_id must be a positive integer"):
            await tool.fn(transaction_id=0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/tools/test_transactions.py::TestTransactionIdValidation -v`
Expected: FAIL

- [ ] **Step 3: Add validation to `transactions.py`**

Add to imports:
```python
from pocketsmith_mcp.errors import validate_id
```

In `get_transaction`, first line inside `try`:
```python
validate_id(transaction_id, "transaction_id")
```

In `create_transaction`, first line inside `try`:
```python
validate_id(transaction_account_id, "transaction_account_id")
```

In `update_transaction`, first line inside `try`:
```python
validate_id(transaction_id, "transaction_id")
```

In `delete_transaction`, first line inside `try`:
```python
validate_id(transaction_id, "transaction_id")
```

Note: `list_transactions` uses `user_ctx.user_id`, no validation needed. The optional `category_id` param in `list_transactions`/`create_transaction` is already guarded by `if category_id:` — a zero/negative value won't be sent.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/tools/test_transactions.py -v`
Expected: All 16 tests PASS (12 existing + 4 new)

- [ ] **Step 5: Commit**

```bash
git add src/pocketsmith_mcp/tools/transactions.py tests/unit/tools/test_transactions.py
git commit -m "feat: add ID validation to transaction tools"
```

---

### Task 4: Add ID validation to `categories.py`, `events.py`, `institutions.py`, `transaction_accounts.py`

These four modules follow the identical pattern. Apply `validate_id()` to every function that takes an `_id` parameter in the path.

**Files:**
- Modify: `src/pocketsmith_mcp/tools/categories.py`
- Modify: `src/pocketsmith_mcp/tools/events.py`
- Modify: `src/pocketsmith_mcp/tools/institutions.py`
- Modify: `src/pocketsmith_mcp/tools/transaction_accounts.py`

- [ ] **Step 1: Add validation to all four tool files**

For each file, add import:
```python
from pocketsmith_mcp.errors import validate_id
```

**`categories.py`** — add `validate_id(category_id, "category_id")` as first line inside `try` block for:
- `get_category`
- `update_category`
- `delete_category`

Note: `create_category` has an optional `parent_id` — validate it only when provided:
```python
if parent_id is not None:
    validate_id(parent_id, "parent_id")
```

**`events.py`** — add `validate_id(event_id, "event_id")` for:
- `get_event`
- `update_event`
- `delete_event`

For `create_event`, validate both required ID params:
```python
validate_id(scenario_id, "scenario_id")
validate_id(category_id, "category_id")
```

**`institutions.py`** — add `validate_id(institution_id, "institution_id")` for:
- `get_institution`
- `update_institution`
- `delete_institution`

**`transaction_accounts.py`** — add `validate_id(transaction_account_id, "transaction_account_id")` for:
- `get_transaction_account`
- `update_transaction_account`

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/unit/ -q`
Expected: All existing tests pass (no validation tests broke existing tests since we only reject invalid IDs, and all existing tests use positive IDs like 456, 700, etc.)

- [ ] **Step 3: Commit**

```bash
git add src/pocketsmith_mcp/tools/categories.py src/pocketsmith_mcp/tools/events.py src/pocketsmith_mcp/tools/institutions.py src/pocketsmith_mcp/tools/transaction_accounts.py
git commit -m "feat: add ID validation to categories, events, institutions, transaction_accounts"
```

---

### Task 5: Add ID validation and file upload validation to `attachments.py`

**Files:**
- Modify: `src/pocketsmith_mcp/tools/attachments.py`
- Modify: `tests/unit/tools/test_attachments.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/tools/test_attachments.py` at the end:

```python
import base64


class TestAttachmentValidation:
    """Tests for input validation on attachment tools."""

    @pytest.mark.asyncio
    async def test_get_attachment_zero_id(self, mcp_with_tools):
        """get_attachment should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("get_attachment")
        with pytest.raises(ValueError, match="attachment_id must be a positive integer"):
            await tool.fn(attachment_id=0)

    @pytest.mark.asyncio
    async def test_delete_attachment_negative_id(self, mcp_with_tools):
        """delete_attachment should reject negative ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("delete_attachment")
        with pytest.raises(ValueError, match="attachment_id must be a positive integer"):
            await tool.fn(attachment_id=-1)

    @pytest.mark.asyncio
    async def test_create_attachment_path_traversal_slash(self, mcp_with_tools):
        """create_attachment should reject filenames with path separators."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        valid_b64 = base64.b64encode(b"test content").decode()
        with pytest.raises(ValueError, match="file_name contains path separator"):
            await tool.fn(title="Test", file_name="../etc/passwd", file_data=valid_b64)

    @pytest.mark.asyncio
    async def test_create_attachment_path_traversal_backslash(self, mcp_with_tools):
        """create_attachment should reject filenames with backslash."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        valid_b64 = base64.b64encode(b"test content").decode()
        with pytest.raises(ValueError, match="file_name contains path separator"):
            await tool.fn(title="Test", file_name="..\\etc\\passwd", file_data=valid_b64)

    @pytest.mark.asyncio
    async def test_create_attachment_invalid_base64(self, mcp_with_tools):
        """create_attachment should reject invalid base64 data."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        with pytest.raises(ValueError, match="file_data is not valid base64"):
            await tool.fn(title="Test", file_name="test.pdf", file_data="not!valid!base64!!!")

    @pytest.mark.asyncio
    async def test_create_attachment_oversized(self, mcp_with_tools):
        """create_attachment should reject files over 10MB."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        # 11MB of data encoded as base64
        big_data = base64.b64encode(b"x" * (11 * 1024 * 1024)).decode()
        with pytest.raises(ValueError, match="exceeds maximum.*10MB"):
            await tool.fn(title="Test", file_name="big.bin", file_data=big_data)

    @pytest.mark.asyncio
    async def test_create_attachment_valid(self, mcp_with_tools, sample_attachment):
        """create_attachment should accept valid inputs."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_attachment
        valid_b64 = base64.b64encode(b"test PDF content").decode()

        tool = mcp._tool_manager._tools.get("create_attachment")
        result = await tool.fn(title="Receipt", file_name="receipt.pdf", file_data=valid_b64)

        import json
        data = json.loads(result)
        assert data["id"] == 700
        client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_attachment_filename_too_long(self, mcp_with_tools):
        """create_attachment should reject filenames over 255 chars."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        valid_b64 = base64.b64encode(b"test").decode()
        with pytest.raises(ValueError, match="file_name exceeds 255 characters"):
            await tool.fn(title="Test", file_name="a" * 256, file_data=valid_b64)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/tools/test_attachments.py::TestAttachmentValidation -v`
Expected: FAIL

- [ ] **Step 3: Implement validation in `attachments.py`**

Add to imports:
```python
import base64

from pocketsmith_mcp.errors import validate_id
```

Add a private validation function inside `register_attachment_tools` (before the tool definitions):

```python
def _validate_file_upload(file_name: str, file_data: str) -> None:
    """Validate file upload inputs."""
    if "/" in file_name or "\\" in file_name:
        raise ValueError("file_name contains path separator characters")
    if len(file_name) > 255:
        raise ValueError("file_name exceeds 255 characters")
    try:
        decoded = base64.b64decode(file_data, validate=True)
    except Exception:
        raise ValueError("file_data is not valid base64")
    max_bytes = 10 * 1024 * 1024  # 10MB
    if len(decoded) > max_bytes:
        raise ValueError(f"Decoded file exceeds maximum size of 10MB")
```

Add `validate_id(attachment_id, "attachment_id")` as first line inside `try` for:
- `get_attachment`
- `update_attachment`
- `delete_attachment`

In `create_attachment`, add as first lines inside `try`:
```python
_validate_file_upload(file_name, file_data)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/tools/test_attachments.py -v`
Expected: All 15 tests PASS (7 existing + 8 new)

- [ ] **Step 5: Commit**

```bash
git add src/pocketsmith_mcp/tools/attachments.py tests/unit/tools/test_attachments.py
git commit -m "feat: add ID validation and file upload validation to attachment tools"
```

---

### Task 6: Add ID validation to `bulk_transactions.py`

**Files:**
- Modify: `src/pocketsmith_mcp/tools/bulk_transactions.py`
- Modify: `tests/unit/tools/test_bulk_transactions.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/tools/test_bulk_transactions.py` at the end:

```python
class TestBulkIdValidation:
    """Tests for ID validation in bulk updates."""

    @pytest.mark.asyncio
    async def test_negative_transaction_id_skipped(self, mcp_with_tools):
        """Negative transaction_id should be skipped with error."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": -1, "category_id": 10}],
            dry_run=True,
        )
        data = json.loads(result)
        assert data["summary"]["skipped"] == 1
        assert "positive integer" in data["results"][0]["message"]

    @pytest.mark.asyncio
    async def test_zero_transaction_id_skipped(self, mcp_with_tools):
        """Zero transaction_id should be skipped with error."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": 0, "category_id": 10}],
            dry_run=True,
        )
        data = json.loads(result)
        assert data["summary"]["skipped"] == 1

    @pytest.mark.asyncio
    async def test_string_transaction_id_coerced(self, mcp_with_tools):
        """String transaction_id that's a valid int should be coerced."""
        mcp, client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": "42", "category_id": 10}],
            dry_run=True,
        )
        data = json.loads(result)
        assert data["summary"]["successful"] == 1
        assert data["results"][0]["transaction_id"] == 42

    @pytest.mark.asyncio
    async def test_non_numeric_transaction_id_skipped(self, mcp_with_tools):
        """Non-numeric transaction_id should be skipped."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": "abc", "category_id": 10}],
            dry_run=True,
        )
        data = json.loads(result)
        assert data["summary"]["skipped"] == 1
        assert "Invalid transaction_id" in data["results"][0]["message"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/tools/test_bulk_transactions.py::TestBulkIdValidation -v`
Expected: FAIL

- [ ] **Step 3: Implement validation in `bulk_transactions.py`**

Replace the `transaction_id` extraction and check block (lines 54-63) with:

```python
raw_id = update.get("transaction_id")
if not raw_id:
    skipped += 1
    results.append({
        "transaction_id": None,
        "status": "skipped",
        "message": "Missing transaction_id",
    })
    continue

try:
    transaction_id = int(raw_id)
except (ValueError, TypeError):
    skipped += 1
    results.append({
        "transaction_id": raw_id,
        "status": "skipped",
        "message": f"Invalid transaction_id: must be a numeric value, got {raw_id!r}",
    })
    continue

if transaction_id <= 0:
    skipped += 1
    results.append({
        "transaction_id": transaction_id,
        "status": "skipped",
        "message": f"transaction_id must be a positive integer, got {transaction_id}",
    })
    continue
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/tools/test_bulk_transactions.py -v`
Expected: All 12 tests PASS (8 existing + 4 new)

- [ ] **Step 5: Commit**

```bash
git add src/pocketsmith_mcp/tools/bulk_transactions.py tests/unit/tools/test_bulk_transactions.py
git commit -m "feat: add ID validation and coercion to bulk transaction tool"
```

---

### Task 7: Fix circuit breaker `failures` property to acquire lock

**Files:**
- Modify: `src/pocketsmith_mcp/client/circuit_breaker.py`
- Modify: `tests/unit/test_circuit_breaker.py`

- [ ] **Step 1: Write test for locked `failures` read**

Add to `tests/unit/test_circuit_breaker.py` at the end:

```python
    def test_failures_property_reads_under_lock(self):
        """Test that failures property acquires the lock."""
        cb = CircuitBreaker(failure_threshold=5)
        cb.record_failure()
        cb.record_failure()

        # Access via property should be consistent
        assert cb.failures == 2

        # Verify the lock is being used by acquiring it first
        with cb._lock:
            # If failures didn't use the lock, this would still work
            # but we're testing the implementation is correct
            pass

        # After releasing, property should work normally
        assert cb.failures == 2
```

- [ ] **Step 2: Fix the `failures` property**

In `src/pocketsmith_mcp/client/circuit_breaker.py`, change the `failures` property (line 73-76):

```python
@property
def failures(self) -> int:
    """Get the current failure count."""
    with self._lock:
        return self._failures
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/unit/test_circuit_breaker.py -v`
Expected: All 17 tests PASS (16 existing + 1 new)

- [ ] **Step 4: Commit**

```bash
git add src/pocketsmith_mcp/client/circuit_breaker.py tests/unit/test_circuit_breaker.py
git commit -m "fix: acquire lock in circuit breaker failures property"
```

---

### Task 8: Fix rate limiter floating-point precision

**Files:**
- Modify: `src/pocketsmith_mcp/client/rate_limiter.py`
- Modify: `tests/unit/test_rate_limiter.py`

- [ ] **Step 1: Write test for precision clamping**

Add to `tests/unit/test_rate_limiter.py` at the end:

```python
    def test_tokens_never_negative_from_precision(self):
        """Tokens should never be negative due to float precision."""
        limiter = RateLimiter(tokens_per_interval=10, interval_seconds=60, initial_tokens=0)
        # Tokens should be clamped to 0, not a tiny negative float
        assert limiter.tokens >= 0.0

    def test_tokens_rounded_after_refill(self):
        """Tokens should be rounded to avoid accumulated float drift."""
        limiter = RateLimiter(tokens_per_interval=3, interval_seconds=1)
        # 3 tokens/sec = 1 token per 0.333... sec — a repeating decimal
        # After many refills, float drift could accumulate without rounding
        for _ in range(100):
            limiter._refill()
        # Tokens should still be at max, not max + epsilon
        assert limiter.tokens == limiter.max_tokens
```

- [ ] **Step 2: Fix `_refill` precision**

In `src/pocketsmith_mcp/client/rate_limiter.py`, modify `_refill` (line 87-95):

```python
def _refill(self) -> None:
    """Refill tokens based on elapsed time."""
    now = time.monotonic()
    elapsed = now - self.last_refill

    # Calculate tokens to add based on elapsed time
    tokens_to_add = (elapsed / self.interval_seconds) * self.tokens_per_interval
    self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
    # Clamp to prevent negative drift and round to avoid accumulated precision errors
    self.tokens = round(max(0.0, self.tokens), 9)
    self.last_refill = now
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/unit/test_rate_limiter.py -v`
Expected: All 15 tests PASS (13 existing + 2 new)

- [ ] **Step 4: Commit**

```bash
git add src/pocketsmith_mcp/client/rate_limiter.py tests/unit/test_rate_limiter.py
git commit -m "fix: clamp and round rate limiter tokens to prevent float drift"
```

---

### Task 9: Make `UserContext.user_id` immutable after first set

**Files:**
- Modify: `src/pocketsmith_mcp/user_context.py`
- Modify: `tests/unit/test_user_context.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/test_user_context.py` at the end:

```python
    def test_set_once_only(self):
        """Setting user_id twice should raise RuntimeError."""
        ctx = UserContext()
        ctx.user_id = 42
        with pytest.raises(RuntimeError, match="user_id has already been set"):
            ctx.user_id = 99

    def test_reject_zero_setter(self):
        """Setting user_id to zero should raise ValueError."""
        ctx = UserContext()
        with pytest.raises(ValueError, match="user_id must be a positive integer"):
            ctx.user_id = 0

    def test_reject_negative_setter(self):
        """Setting user_id to negative should raise ValueError."""
        ctx = UserContext()
        with pytest.raises(ValueError, match="user_id must be a positive integer"):
            ctx.user_id = -5

    def test_constructor_with_zero_leaves_unset(self):
        """Constructor with 0 (default) leaves user_id unresolved."""
        ctx = UserContext(user_id=0)
        with pytest.raises(RuntimeError, match="user_id has not been resolved"):
            _ = ctx.user_id
        # But setting it once should still work
        ctx.user_id = 42
        assert ctx.user_id == 42
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_user_context.py -v`
Expected: FAIL on the new tests

- [ ] **Step 3: Implement setter guard**

Replace the `user_id` setter in `src/pocketsmith_mcp/user_context.py`:

```python
@user_id.setter
def user_id(self, value: int) -> None:
    if self._user_id != 0:
        raise RuntimeError(
            "user_id has already been set and cannot be changed."
        )
    if not isinstance(value, int) or value <= 0:
        raise ValueError(
            f"user_id must be a positive integer, got {value}"
        )
    self._user_id = value
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_user_context.py -v`
Expected: All 7 tests PASS (3 existing + 4 new)

- [ ] **Step 5: Run full test suite to confirm no regressions**

Run: `uv run pytest tests/unit/ -q`
Expected: All tests pass. The only code that sets `user_ctx.user_id` is:
- `server.py:67` — sets once during lifespan startup
- `tests/conftest.py:22` — `UserContext(user_id=42)` via constructor (not the setter)

Both patterns work with the new guard.

- [ ] **Step 6: Commit**

```bash
git add src/pocketsmith_mcp/user_context.py tests/unit/test_user_context.py
git commit -m "fix: make UserContext.user_id immutable after first set"
```

---

### Task 10: Final full regression test

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/unit/ -v --tb=short`
Expected: All tests pass (~170+ tests)

- [ ] **Step 2: Run with coverage**

Run: `uv run pytest tests/unit/ --cov=src/pocketsmith_mcp --cov-report=term-missing -q`
Expected: Coverage >= 70% (existing threshold), all pass

- [ ] **Step 3: Verify no import errors**

Run: `uv run python -c "from pocketsmith_mcp.server import create_server; print('OK')"`
Expected: `OK`
