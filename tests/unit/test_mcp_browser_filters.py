from aidev.models import MCPServerRegistry
from aidev.tui_mcp_browser import filter_registry_entries


def make_entry(name: str, tags: list[str], description: str = "", author: str = "dev") -> MCPServerRegistry:
    return MCPServerRegistry(
        name=name,
        description=description or name,
        author=author,
        repository="https://example.com",
        version="1.0.0",
        install={"type": "npm", "command": f"npm install -g {name}"},
        configuration={},
        tags=tags,
        compatible_profiles=[],
    )


def test_filter_by_query_matches_name_and_description():
    entries = [
        make_entry("redis", tags=["db"], description="In-memory cache"),
        make_entry("k8s", tags=["infra"], description="Kubernetes manager"),
    ]
    filtered = filter_registry_entries(entries, query="kube")
    assert [e.name for e in filtered] == ["k8s"]


def test_filter_by_tag_and_query():
    entries = [
        make_entry("stripe", tags=["payments", "http"]),
        make_entry("paypal", tags=["payments"]),
        make_entry("github", tags=["devtools"]),
    ]
    filtered = filter_registry_entries(entries, query="pay", tag="payments")
    assert {e.name for e in filtered} == {"paypal", "stripe"}


def test_filter_tag_excludes_non_matching():
    entries = [
        make_entry("logger", tags=["tools"]),
        make_entry("docker", tags=["infra"]),
    ]
    filtered = filter_registry_entries(entries, query="", tag="infra")
    assert [e.name for e in filtered] == ["docker"]
