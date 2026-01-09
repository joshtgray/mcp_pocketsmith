"""Budgeting and analysis MCP tools."""

import json

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.budgeting")


def register_budgeting_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register budgeting-related MCP tools."""

    @mcp.tool()
    async def get_budget(
        user_id: int,
        roll_up: bool = False,
    ) -> str:
        """
        Get the user's budget configuration.

        Returns the budget events and configuration for the user,
        including category budgets and recurring budget events.

        Args:
            user_id: The PocketSmith user ID
            roll_up: Whether to roll up child category budgets to parents

        Returns:
            JSON object with budget configuration
        """
        try:
            params = {"roll_up": 1 if roll_up else 0}
            result = await client.get(f"/users/{user_id}/budget", params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_budget failed: {e}")
            raise ValueError(f"Failed to get budget: {e}")

    @mcp.tool()
    async def get_budget_summary(
        user_id: int,
        start_date: str,
        end_date: str,
        period: str | None = None,
        interval: int | None = None,
        categories: str | None = None,
        scenarios: str | None = None,
        roll_up: bool = False,
    ) -> str:
        """
        Get budget analysis summary with actual vs forecast comparison.

        Analyzes spending against budget for the specified period,
        showing over/under budget amounts per category.

        Args:
            user_id: The PocketSmith user ID
            start_date: Analysis start date (YYYY-MM-DD)
            end_date: Analysis end date (YYYY-MM-DD)
            period: Period grouping (weeks, months)
            interval: Period interval (e.g., 2 for bi-weekly)
            categories: Comma-separated category IDs to include
            scenarios: Comma-separated scenario IDs to include
            roll_up: Roll up child categories to parents

        Returns:
            JSON object with budget analysis including actual amounts,
            forecast amounts, and over/under by category
        """
        try:
            params = {
                "start_date": start_date,
                "end_date": end_date,
                "roll_up": 1 if roll_up else 0,
            }
            if period:
                params["period"] = period
            if interval:
                params["interval"] = interval
            if categories:
                params["categories"] = categories
            if scenarios:
                params["scenarios"] = scenarios

            result = await client.get(f"/users/{user_id}/budget_summary", params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_budget_summary failed: {e}")
            raise ValueError(f"Failed to get budget summary: {e}")

    @mcp.tool()
    async def get_trend_analysis(
        user_id: int,
        start_date: str,
        end_date: str,
        period: str | None = None,
        interval: int | None = None,
        categories: str | None = None,
        scenarios: str | None = None,
        roll_up: bool = False,
    ) -> str:
        """
        Get spending trend analysis over time.

        Analyzes spending patterns and trends across the specified
        time period, useful for understanding spending habits.

        Args:
            user_id: The PocketSmith user ID
            start_date: Analysis start date (YYYY-MM-DD)
            end_date: Analysis end date (YYYY-MM-DD)
            period: Period grouping (weeks, months)
            interval: Period interval
            categories: Comma-separated category IDs to include
            scenarios: Comma-separated scenario IDs to include
            roll_up: Roll up child categories to parents

        Returns:
            JSON object with trend analysis data including period-by-period
            spending breakdown
        """
        try:
            params = {
                "start_date": start_date,
                "end_date": end_date,
                "roll_up": 1 if roll_up else 0,
            }
            if period:
                params["period"] = period
            if interval:
                params["interval"] = interval
            if categories:
                params["categories"] = categories
            if scenarios:
                params["scenarios"] = scenarios

            result = await client.get(f"/users/{user_id}/trend_analysis", params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_trend_analysis failed: {e}")
            raise ValueError(f"Failed to get trend analysis: {e}")

    @mcp.tool()
    async def clear_forecast_cache(user_id: int) -> str:
        """
        Clear the user's forecast cache.

        Forces a recalculation of the forecast on next access.
        Useful when you've made significant changes to budget
        events or scenarios.

        Args:
            user_id: The PocketSmith user ID

        Returns:
            Confirmation message
        """
        try:
            await client.delete(f"/users/{user_id}/forecast_cache")
            return json.dumps({
                "success": True,
                "message": "Forecast cache cleared. Forecast will be recalculated on next access."
            })
        except Exception as e:
            logger.error(f"clear_forecast_cache failed: {e}")
            raise ValueError(f"Failed to clear forecast cache: {e}")
