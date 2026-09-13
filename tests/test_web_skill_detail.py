"""Routed skill page API: detail, history, enhance status, and skill-scoped jobs."""
# ruff: noqa: F811 -- imported pytest fixture shares its injection parameter name

from tests.test_web_api import _mk_skill, workspace  # noqa: F401


def test_context_is_wired_and_routes_registered(workspace):
    _, client = workspace
    paths = {route.path for route in client.app.routes}
    assert "/api/skills/{skill_id}/detail" in paths
