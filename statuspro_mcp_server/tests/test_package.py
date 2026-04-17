"""Tests for statuspro_mcp package structure and imports."""


def test_package_import():
    """Test that the main package can be imported."""
    import statuspro_mcp

    # Version is dynamically updated by semantic-release, just check format
    assert statuspro_mcp.__version__  # Not empty
    assert "." in statuspro_mcp.__version__  # Has version separators


def test_submodule_imports():
    """Test that submodules can be imported."""
    from statuspro_mcp import prompts, resources, tools

    assert tools is not None
    assert resources is not None
    assert prompts is not None


def test_package_metadata():
    """Test that package metadata is available."""
    import statuspro_mcp

    assert hasattr(statuspro_mcp, "__version__")
    assert isinstance(statuspro_mcp.__version__, str)
    assert len(statuspro_mcp.__version__) > 0


def test_tool_module_imports():
    """Verify all tool modules import without errors."""
    from statuspro_mcp.tools import orders, statuses

    assert orders is not None
    assert statuses is not None


def test_package_docstring():
    """Test that the package has documentation."""
    import statuspro_mcp

    assert statuspro_mcp.__doc__ is not None
    assert (
        "MCP Server" in statuspro_mcp.__doc__ or "MCP server" in statuspro_mcp.__doc__
    )
    assert "StatusPro" in statuspro_mcp.__doc__
