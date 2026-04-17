#!/bin/bash
# This script runs after container creation to finalize setup
set -e

echo "🚀 Finalizing development environment setup..."

# Ensure uv is in PATH (it should already be installed via onCreate)
export PATH="$HOME/.cargo/bin:$PATH"

# Verify uv is available
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

uv --version

# Sync dependencies (should be fast due to prebuild cache)
echo "📚 Syncing dependencies (using prebuild cache)..."
uv sync --all-extras

# Create .env template if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
# StatusPro API Configuration
# Get your API key from: https://app.orderstatuspro.com/settings/api
STATUSPRO_API_KEY=your-api-key-here
STATUSPRO_BASE_URL=https://app.orderstatuspro.com/api/v1
EOF
    echo "⚠️  Don't forget to add your STATUSPRO_API_KEY to .env!"
fi

# Run quick validation (skip to speed up startup)
echo "✅ Environment validated. Run 'uv run poe check' to verify everything."

# Print next steps
echo ""
echo "✨ Development environment ready!"
echo ""
echo "📋 Next steps:"
echo "   1. Add your STATUSPRO_API_KEY to .env file"
echo "   2. Run tests: uv run poe test"
echo "   3. See available tasks: uv run poe help"
echo ""
echo "📖 Key resources:"
echo "   - MCP v0.1.0 Plan: docs/mcp-server/MCP_V0.1.0_IMPLEMENTATION_PLAN.md"
echo "   - MCP Architecture: docs/mcp-server/MCP_ARCHITECTURE_DESIGN.md"
echo "   - ADR-010: docs/adr/0010-statuspro-mcp-server.md"
echo ""
echo "🎯 Ready to start working on MCP server issues!"
echo "   View milestone: https://github.com/dougborg/statuspro-openapi-client/milestone/1"
