"""Scenario MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger
from pocketsmith_mcp.user_context import UserContext

logger = get_logger("tools.scenarios")


def register_scenario_tools(mcp: FastMCP, client: PocketSmithClient, user_ctx: UserContext) -> None:
    """Register scenario-related MCP tools."""

    @mcp.tool()
    async def list_scenarios() -> str:
        """
        List all scenarios across all accounts.

        Scenarios are used for budgeting and forecasting. They are associated
        with accounts and required when creating events — use the scenario_id
        from this tool with create_event.

        PocketSmith does not have a standalone /scenarios endpoint. Scenarios
        are embedded in account responses. This tool fetches all accounts and
        extracts their scenarios for convenience.

        Returns:
            JSON array of scenarios, each with id, title, type, account_id,
            and account_name
        """
        try:
            accounts = await client.get(f"/users/{user_ctx.user_id}/accounts")

            seen_ids: set[int] = set()
            scenarios: list[dict[str, Any]] = []

            for account in (accounts if isinstance(accounts, list) else []):
                account_id = account.get("id")
                account_name = account.get("title")

                for scenario in account.get("scenarios", []) or []:
                    scenario_id = scenario.get("id")
                    if scenario_id is None or scenario_id in seen_ids:
                        continue
                    seen_ids.add(scenario_id)
                    scenarios.append({
                        "id": scenario_id,
                        "title": scenario.get("title"),
                        "type": scenario.get("type"),
                        "account_id": account_id,
                        "account_name": account_name,
                    })

                primary = account.get("primary_scenario")
                if primary:
                    primary_id = primary.get("id")
                    if primary_id is not None and primary_id not in seen_ids:
                        seen_ids.add(primary_id)
                        scenarios.append({
                            "id": primary_id,
                            "title": primary.get("title"),
                            "type": primary.get("type"),
                            "account_id": account_id,
                            "account_name": account_name,
                        })

            return json.dumps(scenarios, indent=2)
        except Exception as e:
            logger.error(f"list_scenarios failed: {e}")
            raise ValueError(f"Failed to list scenarios: {e}")
