#!/bin/bash
# Install Go-based OSINT tools used by the toolkit
# Requires Go 1.16+ to be installed

set -e

BIN_DIR="${1:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"

echo "[*] Installing Go OSINT tools to $BIN_DIR"

tools=(
    "github.com/tomnomnom/assetfinder@latest"
    "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
    "github.com/projectdiscovery/httpx/cmd/httpx@latest"
    "github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest"
    "github.com/lc/gau/v2/cmd/gau@latest"
    "github.com/tomnomnom/unfurl@latest"
)

for tool in "${tools[@]}"; do
    tool_name=$(echo "$tool" | rev | cut -d'/' -f1 | rev | cut -d'@' -f1)
    echo "[+] Installing $tool_name..."
    GOBIN="$BIN_DIR" go install "$tool" 2>&1 | grep -v "go: " || true
done

echo "[✓] Go tools installed to $BIN_DIR"
echo "    Add this to your PATH: export PATH=\"\$PATH:$BIN_DIR\""
