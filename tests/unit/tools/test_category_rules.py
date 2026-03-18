"""Unit tests for category rules MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.category_rules import register_category_rules_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with category rules tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_category_rules_tools(mcp, mock_client)
    return mcp, mock_client


class TestListCategoryRules:
    """Tests for list_category_rules tool."""

    @pytest.mark.asyncio
    async def test_list_category_rules_returns_all_rules(
        self, mcp_with_tools, sample_category_rule
    ):
        """Test successful listing of category rules."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_category_rule, sample_category_rule]

        tool = mcp._tool_manager._tools.get("list_category_rules")
        result = await tool.fn(user_id=192054)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/192054/category_rules")
        assert len(result_data) == 2
        assert result_data[0]["id"] == sample_category_rule["id"]
        assert result_data[0]["payee_matches"] == sample_category_rule["payee_matches"]

    @pytest.mark.asyncio
    async def test_list_category_rules_empty(self, mcp_with_tools):
        """Test listing category rules when none exist."""
        mcp, client = mcp_with_tools
        client.get.return_value = []

        tool = mcp._tool_manager._tools.get("list_category_rules")
        result = await tool.fn(user_id=192054)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/192054/category_rules")
        assert result_data == []


class TestCreateCategoryRule:
    """Tests for create_category_rule tool."""

    @pytest.mark.asyncio
    async def test_create_category_rule_with_payee_matches(
        self, mcp_with_tools, sample_category_rule
    ):
        """Test creating a category rule with payee_matches."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_category_rule

        tool = mcp._tool_manager._tools.get("create_category_rule")
        result = await tool.fn(category_id=10, payee_matches="GROCERY STORE")
        result_data = json.loads(result)

        client.post.assert_called_once_with(
            "/categories/10/category_rules",
            json_data={"payee_matches": "GROCERY STORE"},
        )
        assert result_data["id"] == sample_category_rule["id"]
        assert result_data["payee_matches"] == sample_category_rule["payee_matches"]

    @pytest.mark.asyncio
    async def test_create_category_rule_with_apply_to_uncategorised(
        self, mcp_with_tools, sample_category_rule
    ):
        """Test creating a category rule with apply_to_uncategorised flag."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_category_rule

        tool = mcp._tool_manager._tools.get("create_category_rule")
        result = await tool.fn(
            category_id=10,
            payee_matches="GROCERY STORE",
            apply_to_uncategorised=True,
        )
        result_data = json.loads(result)

        client.post.assert_called_once_with(
            "/categories/10/category_rules",
            json_data={
                "payee_matches": "GROCERY STORE",
                "apply_to_uncategorised": True,
            },
        )
        assert result_data["id"] == sample_category_rule["id"]

    @pytest.mark.asyncio
    async def test_create_category_rule_with_apply_to_all(
        self, mcp_with_tools, sample_category_rule
    ):
        """Test creating a category rule with apply_to_all flag."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_category_rule

        tool = mcp._tool_manager._tools.get("create_category_rule")
        result = await tool.fn(
            category_id=10,
            payee_matches="GROCERY STORE",
            apply_to_all=True,
        )
        result_data = json.loads(result)

        client.post.assert_called_once_with(
            "/categories/10/category_rules",
            json_data={
                "payee_matches": "GROCERY STORE",
                "apply_to_all": True,
            },
        )
        assert result_data["id"] == sample_category_rule["id"]

    @pytest.mark.asyncio
    async def test_list_category_rules_error(self, mcp_with_tools):
        """Test error handling for listing category rules."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("list_category_rules")

        with pytest.raises(ValueError, match="Failed to list category rules"):
            await tool.fn(user_id=192054)

    @pytest.mark.asyncio
    async def test_create_category_rule_error(self, mcp_with_tools):
        """Test error handling for creating a category rule."""
        mcp, client = mcp_with_tools
        client.post.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("create_category_rule")

        with pytest.raises(ValueError, match="Failed to create category rule"):
            await tool.fn(category_id=10, payee_matches="GROCERY STORE")
