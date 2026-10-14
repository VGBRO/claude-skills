#!/bin/bash
#
# Fix Node.js Module Path Resolution for @agentscript/cli
#
# Problem: @agentscript/cli tries to resolve its dependencies from:
#   node_modules/@agentscript/cli/node_modules/@agentscript/*
#
# But npm installs them at:
#   node_modules/@agentscript/*
#
# Solution: Create symlinks in the expected location pointing to actual packages.
#
# This script is idempotent - it can be run multiple times safely.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$PROJECT_ROOT"

echo "Fixing Node.js path resolution for @agentscript/cli..."
echo ""

# Check if @agentscript/cli is installed
if [ ! -d "node_modules/@agentscript/cli" ]; then
    echo "❌ @agentscript/cli is not installed."
    echo "   Run: npm install --legacy-peer-deps --ignore-scripts"
    exit 1
fi

# Create the nested node_modules directory if it doesn't exist
TARGET_DIR="node_modules/@agentscript/cli/node_modules/@agentscript"
mkdir -p "$TARGET_DIR"

# List of packages to symlink
PACKAGES=(
    "agentforce-dialect"
    "compiler"
    "parser"
    "language"
    "types"
    "agentforce"
    "agentscript-dialect"
    "agentfabric-dialect"
)

echo "Creating symlinks in: $TARGET_DIR"
echo ""

CREATED=0
EXISTED=0
MISSING=0

for package in "${PACKAGES[@]}"; do
    SOURCE="$PROJECT_ROOT/node_modules/@agentscript/$package"
    LINK="$TARGET_DIR/$package"

    if [ ! -d "$SOURCE" ]; then
        echo "⚠️  Skipping $package (source not found)"
        MISSING=$((MISSING + 1))
        continue
    fi

    if [ -L "$LINK" ]; then
        # Symlink already exists
        CURRENT_TARGET=$(readlink "$LINK")
        if [ "$CURRENT_TARGET" = "$SOURCE" ]; then
            echo "✓  $package (already linked)"
            EXISTED=$((EXISTED + 1))
        else
            echo "⚠️  $package (re-linking)"
            rm "$LINK"
            ln -s "$SOURCE" "$LINK"
            CREATED=$((CREATED + 1))
        fi
    elif [ -d "$LINK" ]; then
        # Directory exists but is not a symlink - replace with symlink
        echo "⚠️  $package (replacing directory with symlink)"
        rm -rf "$LINK"
        ln -s "$SOURCE" "$LINK"
        CREATED=$((CREATED + 1))
    else
        # Create new symlink
        echo "✓  $package (creating symlink)"
        ln -s "$SOURCE" "$LINK"
        CREATED=$((CREATED + 1))
    fi
done

echo ""
echo "Summary:"
echo "  Created: $CREATED"
echo "  Already existed: $EXISTED"
echo "  Missing sources: $MISSING"
echo ""

if [ $MISSING -gt 0 ]; then
    echo "⚠️  Some packages are missing. You may need to run:"
    echo "   npm install --legacy-peer-deps --ignore-scripts"
    exit 1
fi

echo "✅ Path resolution fix complete!"
echo ""
echo "You can now run the compiler:"
echo "  python3 .claude/skills/00-verify-prerequisites/scripts/compile_agentscript_nexus_ts.py <agent-file>"
