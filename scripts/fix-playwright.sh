#!/bin/bash
# Fix Playwright Browser Version Mismatch
# This script creates symlinks to fix the "Executable doesn't exist" error

set -e

PLAYWRIGHT_CACHE="$HOME/.cache/ms-playwright"

echo "🎭 Fixing Playwright Browser Symlinks..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Playwright cache exists
if [ ! -d "$PLAYWRIGHT_CACHE" ]; then
    echo "❌ Playwright cache directory not found: $PLAYWRIGHT_CACHE"
    echo "📦 Installing Playwright browsers..."
    python3 -m playwright install chromium
    exit 0
fi

cd "$PLAYWRIGHT_CACHE"

# Function to find all missing symlinks and create them
create_missing_symlinks() {
    local pattern=$1
    local browser_name=$2

    echo ""
    echo "🔍 Checking $browser_name..."

    # Find the latest installed version (exclude symlinks, only real directories)
    latest=$(find . -maxdepth 1 -type d -name "${pattern}-*" 2>/dev/null | sort -V | tail -1 | sed 's|^\./||' || true)

    if [ -z "$latest" ]; then
        echo "⚠️  No $browser_name installation found (searching for ${pattern}-*)"
        return
    fi

    latest_version=$(basename "$latest")
    echo "✅ Latest installed: $latest_version"

    # Find all version references in error messages (common versions: 1179, 1187, 1193, etc.)
    # We'll create symlinks for a range of common version numbers
    for version in 1179 1180 1187 1190 1193 1195 1200; do
        target="${pattern}-${version}"

        # Skip if it's the actual directory
        if [ -d "$target" ] && [ ! -L "$target" ]; then
            continue
        fi

        # Create symlink if it doesn't exist or is broken
        if [ ! -e "$target" ]; then
            echo "🔗 Creating symlink: $target -> $latest_version"
            ln -sf "$latest_version" "$target"
        fi
    done

    echo "✅ $browser_name symlinks ready"
}

# Create symlinks for chromium and chromium_headless_shell
create_missing_symlinks "chromium" "Chromium"
create_missing_symlinks "chromium_headless_shell" "Chromium Headless Shell"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Playwright fix complete!"
echo ""
echo "Current browser installations:"
ls -la "$PLAYWRIGHT_CACHE" | grep -E "chromium|webkit|firefox" | grep -v ".links"

cd - > /dev/null

echo ""
echo "🎯 Playwright should now work correctly!"
echo "💡 Tip: Run this script anytime you see the 'Executable doesn't exist' error"
