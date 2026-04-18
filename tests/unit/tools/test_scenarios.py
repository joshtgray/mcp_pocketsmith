"""Unit tests for scenario MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.scenarios import register_scenario_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client, user_ctx):
    """Create FastMCP instance with scenario tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_scenario_tools(mcp, mock_client, user_ctx)
    return mcp, mock_client


@pytest.fixture
def sample_account_with_scenarios():
    """Sample account with multiple scenarios."""
    return {
        "id": 10,
        "title": "Savings Account",
        "currency_code": "AUD",
        "scenarios": [
            {"id": 101, "title": "Primary", "type": "savings"},
            {"id": 102, "title": "Emergency Fund", "type": "savings"},
        ],
        "primary_scenario": {"id": 101, "title": "Primary", "type": "savings"},
    }


@pytest.fixture
def sample_account_no_scenarios():
    """Sample account with no scenarios."""
    return {
        "id": 20,
        "title": "Credit Card",
        "currency_code": "AUD",
        "scenarios": [],
        "primary_scenario": None,
    }


class TestListScenarios:
    """Tests for list_scenarios tool."""

    @pytest.mark.asyncio
    async def test_list_scenarios_extracts_from_accounts(
        self, mcp_with_tools, sample_account_with_scenarios, sample_account_no_scenarios
    ):
        """list_scenarios extracts scenario data from account responses."""
        mcp, client = mcp_with_tools
        client.get.return_value = [
            sample_account_with_scenarios,
            sample_account_no_scenarios,
        ]

        tool = mcp._tool_manager._tools.get("list_scenarios")
        result = await tool.fn()
        data = json.loads(result)

        client.get.assert_called_once_with("/users/42/accounts")
        assert len(data) == 2
        ids = {s["id"] for s in data}
        assert ids == {101, 102}

    @pytest.mark.asyncio
    async def test_list_scenarios_includes_account_context(
        self, mcp_with_tools, sample_account_with_scenarios
    ):
        """Each scenario includes account_id and account_name."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_account_with_scenarios]

        tool = mcp._tool_manager._tools.get("list_scenarios")
        result = await tool.fn()
        data = json.loads(result)

        for scenario in data:
            assert "account_id" in scenario
            assert "account_name" in scenario
            assert scenario["account_id"] == 10
            assert scenario["account_name"] == "Savings Account"

    @pytest.mark.asyncio
    async def test_list_scenarios_includes_required_fields(
        self, mcp_with_tools, sample_account_with_scenarios
    ):
        """Each scenario includes id, title, type."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_account_with_scenarios]

        tool = mcp._tool_manager._tools.get("list_scenarios")
        result = await tool.fn()
        data = json.loads(result)

        first = data[0]
        assert "id" in first
        assert "title" in first
        assert "type" in first

    @pytest.mark.asyncio
    async def test_list_scenarios_deduplicates(self, mcp_with_tools):
        """Scenarios appearing in multiple accounts are deduplicated by ID."""
        mcp, client = mcp_with_tools
        shared_scenario = {"id": 55, "title": "Shared", "type": "savings"}
        client.get.return_value = [
            {"id": 1, "title": "Acc A", "scenarios": [shared_scenario], "primary_scenario": None},
            {"id": 2, "title": "Acc B", "scenarios": [shared_scenario], "primary_scenario": None},
        ]

        tool = mcp._tool_manager._tools.get("list_scenarios")
        result = await tool.fn()
        data = json.loads(result)

        assert len(data) == 1
        assert data[0]["id"] == 55

    @pytest.mark.asyncio
    async def test_list_scenarios_no_scenarios(self, mcp_with_tools, sample_account_no_scenarios):
        """Returns empty list when accounts have no scenarios."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_account_no_scenarios]

        tool = mcp._tool_manager._tools.get("list_scenarios")
        result = await tool.fn()
        data = json.loads(result)

        assert data == []

    @pytest.mark.asyncio
    async def test_list_scenarios_empty_accounts(self, mcp_with_tools):
        """Returns empty list when there are no accounts."""
        mcp, client = mcp_with_tools
        client.get.return_value = []

        tool = mcp._tool_manager._tools.get("list_scenarios")
        result = await tool.fn()
        data = json.loads(result)

        assert data == []

    @pytest.mark.asyncio
    async def test_list_scenarios_handles_missing_fields(self, mcp_with_tools):
        """Handles accounts where scenario fields are absent (graceful .get access)."""
        mcp, client = mcp_with_tools
        client.get.return_value = [
            {
                "id": 99,
                "title": "Minimal Account",
                # No 'scenarios' key, no 'primary_scenario' key
            }
        ]

        tool = mcp._tool_manager._tools.get("list_scenarios")
        result = await tool.fn()
        data = json.loads(result)

        assert data == []

    @pytest.mark.asyncio
    async def test_list_scenarios_primary_scenario_fallback(self, mcp_with_tools):
        """primary_scenario is included when not already in the scenarios list."""
        mcp, client = mcp_with_tools
        client.get.return_value = [
            {
                "id": 30,
                "title": "Loan",
                "scenarios": [],
                "primary_scenario": {"id": 77, "title": "Loan Scenario", "type": "debt"},
            }
        ]

        tool = mcp._tool_manager._tools.get("list_scenarios")
        result = await tool.fn()
        data = json.loads(result)

        assert len(data) == 1
        assert data[0]["id"] == 77
        assert data[0]["title"] == "Loan Scenario"
        assert data[0]["account_id"] == 30
