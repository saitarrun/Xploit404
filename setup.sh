#!/bin/bash

################################################################################
# Striker Toolkit - Setup and Installation Script
#
# Actually installs everything the toolkit can use (not just check-and-warn):
#   - Python virtual environment + requirements.txt
#   - System packages via Homebrew (macOS) or apt (Linux)
#   - Go-based OSINT tools (assetfinder, subfinder, httpx, nuclei, gau, unfurl, puredns)
#   - Gophish (vendored binary + assets, since no brew/apt package exists)
#
# Tools that need a manual step no script should do unattended (Docker
# services, GB-sized downloads, licensed software) are reported at the end
# with the exact command to run.
#
# Safe to re-run: every step skips work that's already done.
################################################################################

set -uo pipefail  # NOT -e: one failed optional package must not abort the run

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
CONFIG_DIR="${SCRIPT_DIR}/config"
OUTPUT_DIR="${SCRIPT_DIR}/output"
LOG_FILE="${SCRIPT_DIR}/setup.log"
OS="$(uname -s)"

FAILED_STEPS=()

print_header() {
    echo -e "\n${BLUE}================================================================${NC}"
    echo -e "${BLUE}${NC} $1"
    echo -e "${BLUE}================================================================${NC}\n"
}
print_success() { echo -e "${GREEN}[+]${NC} $1"; }
print_error()   { echo -e "${RED}[-]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_info()    { echo -e "${BLUE}[*]${NC} $1"; }
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"; }

# ------------------------------------------------------------------------
check_python() {
    print_header "Checking Python Installation"
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.10+."
        exit 1
    fi
    print_success "Python $(python3 --version 2>&1 | awk '{print $2}') found"
}

setup_venv() {
    print_header "Setting Up Virtual Environment (.venv)"
    if [ -d "$VENV_DIR" ]; then
        # venv/bin/activate and pyvenv.cfg bake in the absolute project path at
        # creation time. If this folder was ever moved or renamed, pip/activate
        # silently point at a path that no longer exists - rebuild instead.
        if [ -f "$VENV_DIR/bin/activate" ] && ! grep -q "VIRTUAL_ENV='$VENV_DIR'" "$VENV_DIR/bin/activate" 2>/dev/null; then
            print_warning ".venv references a stale path (project folder was moved/renamed) - rebuilding"
            rm -rf "$VENV_DIR"
            python3 -m venv "$VENV_DIR"
            print_success "Virtual environment rebuilt at .venv"
        else
            print_info ".venv already exists"
        fi
    else
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created at .venv"
    fi
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
}

install_python_dependencies() {
    print_header "Installing Python Dependencies"
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        if pip install -r "$SCRIPT_DIR/requirements.txt"; then
            print_success "Python dependencies installed"
        else
            print_error "pip install -r requirements.txt failed"
            FAILED_STEPS+=("python-requirements")
        fi
    else
        print_warning "requirements.txt not found"
    fi
}

setup_directories() {
    print_header "Setting Up Directory Structure"
    for dir in "$CONFIG_DIR" "$OUTPUT_DIR" "${SCRIPT_DIR}/db"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created: ${dir#$SCRIPT_DIR/}"
        else
            print_info "Already exists: ${dir#$SCRIPT_DIR/}"
        fi
    done
}

setup_config() {
    print_header "Setting Up Configuration Files"
    if [ ! -f "$CONFIG_DIR/keys.env" ]; then
        cat > "$CONFIG_DIR/keys.env" << 'CONFIG_EOF'
# API Keys and Credentials Configuration
# DO NOT commit this file to version control!
#
# Every key below is actually read by the toolkit (via _load_keys() in
# modules/tools/phoneinfoga.py, reused by GitHub Dorks/CVE/Osintgram) -
# there are no placeholder-only entries here.

# NUMVERIFY_API_KEY: PhoneInfoga's numverify carrier/line-type lookup.
# NUMVERIFY_API_KEY=your_key_here

# NVD_API_KEY: raises the NVD CVE-lookup rate limit (modules/scanner/cve.py).
# NVD_API_KEY=your_key_here

# GH_TOKEN: GitHub Dorks - unauthenticated GitHub code search is heavily rate-limited.
# GH_TOKEN=your_token_here

# HIKERAPI_TOKEN: Osintgram's HikerAPI backend, used instead of an Instagram login.
# HIKERAPI_TOKEN=your_token_here
CONFIG_EOF
        print_success "Created: config/keys.env"
        print_warning "Add your API keys to config/keys.env"
    else
        print_info "config/keys.env already exists"
    fi

    if [ ! -f "$SCRIPT_DIR/.env.local" ]; then
        cat > "$SCRIPT_DIR/.env.local" << 'LOCAL_ENV'
# Gates `menu.py --intensive` / `striker.py --intensive`: without this set to
# 1, intensive-profile scans refuse to run non-interactively (see menu.main).
STRIKER_AUTHORIZED=0
LOCAL_ENV
        print_success "Created: .env.local"
    else
        print_info ".env.local already exists"
    fi
}

# ------------------------------------------------------------------------
# System packages: this is the part the old script only *checked*. It now
# actually installs, tool by tool, so one failure (deprecated cask, network
# block, etc.) doesn't stop the rest.
install_system_packages() {
    print_header "Installing System Packages"

    if [[ "$OS" == "Darwin" ]]; then
        if ! command -v brew &> /dev/null; then
            print_error "Homebrew not found. Install it from https://brew.sh then re-run this script."
            FAILED_STEPS+=("homebrew-missing")
            return
        fi

        local formulas=(nmap nikto sqlmap hydra john-jumbo hashcat aircrack-ng \
                        wireshark gobuster exiftool tor exploitdb proxychains-ng \
                        amass massdns go chisel)
        for f in "${formulas[@]}"; do
            if brew list --formula "$f" &>/dev/null; then
                print_info "$f already installed"
            elif brew install "$f" 2>&1 | tee -a "$LOG_FILE" | grep -q "already installed\|successfully installed\|Pouring"; then
                print_success "$f installed"
            else
                print_warning "$f failed to install (see setup.log) - continuing"
                FAILED_STEPS+=("brew:$f")
            fi
        done

        local casks=(bloodhound metasploit)
        for c in "${casks[@]}"; do
            if brew list --cask "$c" &>/dev/null; then
                print_info "$c already installed"
            elif brew install --cask "$c" 2>&1 | tee -a "$LOG_FILE" | grep -q "successfully installed\|Moving App"; then
                print_success "$c installed"
            else
                print_warning "$c failed to install - it may be blocked by network filtering on " \
                              "its download domain, or deprecated by Homebrew. See setup.log."
                FAILED_STEPS+=("cask:$c")
            fi
        done

    elif [[ "$OS" == "Linux" ]]; then
        print_info "Linux detected - using apt (best-effort; not all packages exist in every distro)"
        sudo apt update -y
        # build-essential is here for massdns (built from source below, since it
        # has no stock apt package either); the rest are the same one-line
        # apt-installable tools as the macOS formula list.
        local packages=(nmap nikto sqlmap hydra john hashcat aircrack-ng wireshark \
                        gobuster libimage-exiftool-perl tor proxychains4 golang-go \
                        build-essential git)
        for p in "${packages[@]}"; do
            if dpkg -s "$p" &>/dev/null; then
                print_info "$p already installed"
            elif sudo apt install -y "$p" 2>&1 | tee -a "$LOG_FILE" > /dev/null; then
                print_success "$p installed"
            else
                print_warning "$p failed to install - continuing"
                FAILED_STEPS+=("apt:$p")
            fi
        done
        print_warning "exploitdb, metasploit-framework, and bloodhound have no reliable " \
                      "stock-Debian/Ubuntu package - install from Kali repos or vendor upstream manually."
    else
        print_warning "Unrecognized OS '$OS' - skipping system package installation"
    fi
}

install_go_tools() {
    print_header "Installing Go-Based Tools"
    if ! command -v go &> /dev/null; then
        print_warning "Go not installed - skipping assetfinder/subfinder/httpx/nuclei/gau/unfurl/puredns/amass/chisel"
        FAILED_STEPS+=("go-missing")
        return
    fi

    # ~/.local/bin, not a project-local dir: matches how assetfinder/subfinder/
    # httpx/gau/unfurl are already installed and resolved via PATH elsewhere.
    local go_bin="$HOME/.local/bin"
    mkdir -p "$go_bin"

    if [ -x "$SCRIPT_DIR/scripts/install_go_tools.sh" ]; then
        bash "$SCRIPT_DIR/scripts/install_go_tools.sh" "$go_bin" \
            && print_success "Go OSINT tools installed to ~/.local/bin" \
            || { print_warning "install_go_tools.sh reported errors"; FAILED_STEPS+=("go-osint-tools"); }
    fi

    print_info "Installing puredns (needs massdns, installed above on macOS / by install_massdns_linux on Linux)..."
    if GOBIN="$go_bin" go install github.com/d3mondev/puredns/v2@latest 2>&1 | tee -a "$LOG_FILE" > /dev/null; then
        print_success "puredns installed to ~/.local/bin"
    else
        print_warning "puredns install failed - see setup.log"
        FAILED_STEPS+=("puredns")
    fi

    # Amass and Chisel are covered by the macOS brew formula list above, but
    # neither has a reliable stock Debian/Ubuntu apt package - both ship as
    # plain Go binaries, so install them the same way puredns is installed.
    if [[ "$OS" == "Linux" ]]; then
        print_info "Installing amass (no stock apt package)..."
        if GOBIN="$go_bin" go install -v github.com/owasp-amass/amass/v4/...@master 2>&1 | tee -a "$LOG_FILE" > /dev/null; then
            print_success "amass installed to ~/.local/bin"
        else
            print_warning "amass install failed - see setup.log"
            FAILED_STEPS+=("amass")
        fi

        print_info "Installing chisel (no stock apt package)..."
        if GOBIN="$go_bin" go install github.com/jpillora/chisel@latest 2>&1 | tee -a "$LOG_FILE" > /dev/null; then
            print_success "chisel installed to ~/.local/bin"
        else
            print_warning "chisel install failed - see setup.log"
            FAILED_STEPS+=("chisel")
        fi
    fi

    if [[ ":$PATH:" != *":$go_bin:"* ]]; then
        print_warning "~/.local/bin is not on PATH - add: export PATH=\"\$PATH:$go_bin\""
    fi
}

# ------------------------------------------------------------------------
# massdns has no stock apt package either (it's covered by the macOS brew
# formula list above); puredns needs it at runtime, so build it from source.
install_massdns_linux() {
    [[ "$OS" == "Linux" ]] || return
    print_header "Installing massdns (required by puredns)"
    if command -v massdns &> /dev/null; then
        print_info "massdns already installed"
        return
    fi

    local build_dir
    build_dir="$(mktemp -d)"
    if git clone --depth 1 https://github.com/blechschmidt/massdns.git "$build_dir/massdns" >> "$LOG_FILE" 2>&1 \
        && make -C "$build_dir/massdns" >> "$LOG_FILE" 2>&1 \
        && sudo install -m 0755 "$build_dir/massdns/bin/massdns" /usr/local/bin/massdns; then
        print_success "massdns built and installed to /usr/local/bin/massdns"
    else
        print_warning "massdns build failed - see setup.log (puredns needs it at runtime)"
        FAILED_STEPS+=("massdns")
    fi
    rm -rf "$build_dir"
}

# ------------------------------------------------------------------------
# Gophish has no brew/apt package; it ships as a platform zip with a
# binary + static assets that must live together. Vendor it the same way
# bin/phoneinfoga-* is vendored, matching modules/tools/gophish.py's lookup.
install_gophish() {
    print_header "Installing Gophish"
    local vendor_dir="$SCRIPT_DIR/thirdparty/gophish"

    if [ -f "$vendor_dir/gophish" ]; then
        print_info "Gophish already installed"
        return
    fi

    local platform_zip=""
    case "$OS" in
        Darwin) platform_zip="gophish-v0.12.1-osx-64bit.zip" ;;
        Linux)  platform_zip="gophish-v0.12.1-linux-64bit.zip" ;;
        *) print_warning "No Gophish build for OS '$OS' - skipping"; return ;;
    esac

    if [[ "$OS" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
        if ! /usr/bin/pgrep oahd &>/dev/null; then
            print_warning "Gophish's macOS build is x86_64-only; Rosetta 2 isn't running." \
                          " Install it with: softwareupdate --install-rosetta"
        fi
    fi

    print_info "Downloading $platform_zip..."
    mkdir -p "$vendor_dir"
    local tmp_zip
    tmp_zip="$(mktemp -t gophish.XXXXXX.zip)"
    if curl -sL -o "$tmp_zip" \
        "https://github.com/gophish/gophish/releases/download/v0.12.1/$platform_zip" \
        && unzip -q -o "$tmp_zip" -d "$vendor_dir"; then
        chmod +x "$vendor_dir/gophish"
        rm -f "$tmp_zip"
        print_success "Gophish installed to thirdparty/gophish"
    else
        print_warning "Gophish download/extract failed - see setup.log"
        FAILED_STEPS+=("gophish")
    fi
}

# Sliver's server binary is ~260MB (darwin-arm64) - opt-in only, since that's
# too large to vendor into the repo and not everyone needs a C2 framework.
install_sliver() {
    if [[ "${INSTALL_SLIVER:-0}" != "1" ]]; then
        print_info "Skipping Sliver C2 (260MB+ binary, not vendored in-repo)."
        print_info "  To install: INSTALL_SLIVER=1 ./setup.sh"
        print_info "  Or manually: https://github.com/BishopFox/sliver/releases"
        return
    fi

    print_header "Installing Sliver C2"
    local dest="$HOME/.local/bin"
    mkdir -p "$dest"
    local arch
    arch="$(uname -m)"
    [[ "$arch" == "x86_64" ]] && arch="amd64"
    local asset="sliver-server_$(echo "$OS" | tr '[:upper:]' '[:lower:]')-$arch"

    print_info "Downloading $asset (this is large, be patient)..."
    if curl -sL -o "$dest/sliver-server" \
        "https://github.com/BishopFox/sliver/releases/latest/download/$asset"; then
        chmod +x "$dest/sliver-server"
        print_success "Sliver server installed to ~/.local/bin/sliver-server"
    else
        print_warning "Sliver download failed"
        FAILED_STEPS+=("sliver")
    fi
}

verify_installation() {
    print_header "Verifying Installation"
    cd "$SCRIPT_DIR"
    python3 menu.py doctor 2>&1 | tee -a "$LOG_FILE"
}

print_completion_summary() {
    print_header "Setup Complete"

    echo "Next steps:"
    echo "  1. Add API keys to: config/keys.env"
    echo "  2. Activate the environment: source .venv/bin/activate"
    echo "  3. Start the toolkit: python3 menu.py"
    echo "  4. Check tool status any time: python3 menu.py doctor"
    echo ""
    echo "Tools that need a manual step (not automatable safely):"
    echo "  - Havoc C2:       git clone https://github.com/HavocFramework/Havoc && make"
    echo "  - Mythic C2:      git clone https://github.com/its-a-feature/Mythic && ./mythic-cli install  (needs Docker)"
    echo "  - MITRE CALDERA:  git clone --recursive https://github.com/mitre/caldera && docker compose up"
    echo "  - Atomic Red Team: git clone https://github.com/redcanaryco/atomic-red-team"
    echo "  - Sliver C2:      INSTALL_SLIVER=1 ./setup.sh  (or see github.com/BishopFox/sliver/releases)"
    echo ""

    if [ ${#FAILED_STEPS[@]} -gt 0 ]; then
        print_warning "Steps that failed or were skipped: ${FAILED_STEPS[*]}"
        print_info "Full log: setup.log"
    else
        print_success "All automated steps completed cleanly"
    fi
}

main() {
    print_header "Striker Toolkit - Setup"
    echo "Log file: $LOG_FILE"
    : > "$LOG_FILE"

    check_python
    setup_venv
    install_python_dependencies
    setup_directories
    setup_config
    install_system_packages
    install_massdns_linux
    install_go_tools
    install_gophish
    install_sliver
    verify_installation
    print_completion_summary
}

main "$@"
