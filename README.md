# Striker

A terminal-based penetration testing toolkit. `menu.py` is a single interactive
launcher that wraps 52 recon, OSINT, exploitation, and red-team tools -
bundled originals plus thin wrappers around standard security tools already
on your system - behind one consistent menu, with a session target
(domain/username) shared across whichever tool you pick.

Categories: Domain & Network, Identity & Social, Search & Dorks, Vulnerability
& Analysis, Dark Web, Exploitation & Frameworks, Web Application Testing,
Credential Testing, Wireless & Network, Cryptography & Cipher Tools, Advanced
Reconnaissance, Initial Access & Delivery, C2 & Command Control,
Post-Exploitation, and Continuous Security Testing.

Run `python3 menu.py list` for the full, always-current tool list, and
`python3 menu.py doctor` to see what's installed and ready on your machine
right now - both read from the live tool registry, so they never go stale
the way a hardcoded list in this file would.

> **Authorized use only.** Every tool here is meant for systems and networks
> you own or are explicitly authorized to test (labs, CTFs, engagements you
> have signed off on). `--intensive` mode requires an explicit opt-in (see
> Configuration below) for exactly this reason.

## Requirements

- Python 3.10+ (theHarvester specifically needs 3.12+; it's vendored with its
  own venv on first use, so it doesn't constrain the rest of the toolkit)
- macOS or Linux (Debian/Ubuntu-style `apt`). Windows works for the pure-Python
  tools but `setup.sh` and most system-package tools target macOS/Linux.
- [Homebrew](https://brew.sh) (macOS) or `apt` (Linux) for system packages
- [Go](https://go.dev) 1.16+ for the Go-based recon tools (installed
  automatically by `setup.sh` on macOS; install it yourself first on Linux,
  or let `setup.sh` install it via `apt install golang-go`)

## Quick setup

```bash
git clone <this-repo>
cd Xploit404
./setup.sh
```

`setup.sh` is safe to re-run - every step skips work that's already done. It:

1. Creates and activates a Python virtualenv at `.venv`, and installs
   `requirements.txt` into it
2. Creates `config/` and `output/` directories, and generates
   `config/keys.env` / `.env.local` templates (see Configuration below)
3. Installs system packages: on macOS via Homebrew (`nmap`, `nikto`, `sqlmap`,
   `hydra`, `john-jumbo`, `hashcat`, `aircrack-ng`, `wireshark`, `gobuster`,
   `exiftool`, `tor`, `exploitdb`, `proxychains-ng`, `amass`, `massdns`,
   `chisel`, `go`, plus the `bloodhound`/`metasploit` casks); on Linux via
   `apt` (the same tools where a stock package exists, plus `build-essential`
   for the one tool built from source below)
4. Builds `massdns` from source on Linux (no stock apt package exists, and
   `puredns` needs it at runtime)
5. Installs the Go-binary tools - `assetfinder`, `subfinder`, `httpx`,
   `nuclei`, `gau`, `unfurl`, `puredns`, and (Linux only, since macOS gets them
   from Homebrew above) `amass` and `chisel` - to `~/.local/bin`
6. Vendors Gophish (no brew/apt package exists for it)
7. Runs `python3 menu.py doctor` at the end so you can see exactly what's
   ready and what still needs a manual step

Failures in any one step are logged to `setup.log` and don't stop the rest of
the run; `setup.sh` prints a summary of anything that failed or was skipped.

After it finishes:

```bash
source .venv/bin/activate
python3 menu.py
```

## Tools that need a manual step

A few tools are intentionally **not** automated - Docker-based stacks,
GB-sized downloads, or licensed software aren't something a setup script
should install unattended:

- **Sliver C2** - `INSTALL_SLIVER=1 ./setup.sh` (opt-in: the server binary is
  260MB+), or see [releases](https://github.com/BishopFox/sliver/releases)
- **Havoc C2** - `git clone https://github.com/HavocFramework/Havoc && make`
- **Mythic C2** - `git clone https://github.com/its-a-feature/Mythic && ./mythic-cli install` (needs Docker)
- **MITRE CALDERA** - `git clone --recursive https://github.com/mitre/caldera && docker compose up`
- **Atomic Red Team** - `git clone https://github.com/redcanaryco/atomic-red-team`
- **Metasploit, SearchSploit (exploitdb), BloodHound** - covered by `setup.sh`
  on macOS; on Linux, none has a reliable stock Debian/Ubuntu package - install
  from Kali repos or vendor upstream manually

Run `python3 menu.py doctor` any time to check what's still missing.

## Configuration

**`config/keys.env`** - optional API keys, one `KEY=VALUE` per line. It's
git-ignored; a real environment variable of the same name always takes
precedence over the file. Every key it supports is actually read by the
toolkit:

| Key | Used by | Get one at |
|---|---|---|
| `NUMVERIFY_API_KEY` | PhoneInfoga (carrier/line-type lookup) | https://numverify.com |
| `NVD_API_KEY` | CVE lookups (raises the NVD rate limit) | https://nvd.nist.gov/developers/request-an-api-key |
| `GH_TOKEN` | GitHub Dorks (avoids strict search rate limits) | https://github.com/settings/tokens (`public_repo` scope) |
| `HIKERAPI_TOKEN` | Osintgram, instead of an Instagram login | https://hikerapi.com |

**`.env.local`** - loaded automatically at startup (also git-ignored). Today
it only sets `STRIKER_AUTHORIZED=0`, which gates `menu.py --intensive` /
`striker.py --intensive`: intensive-profile scans (broader active checks,
still rate-bounded) refuse to run non-interactively unless you set this to
`1`, so a scripted/CI run can't silently opt into a more aggressive profile.
The interactive menu's own `profile` command asks for a typed `AUTHORIZED`
confirmation instead.

## Running it

```bash
python3 menu.py                    # interactive menu
python3 menu.py <tool> [args...]   # jump straight to a tool, e.g.:
python3 menu.py nmap example.com
python3 menu.py doctor             # readiness check for every tool
python3 menu.py list               # list all tools by number/category
python3 menu.py help               # usage help
```

`python3 striker.py` is an identical entry point - both call the same `main()`.

## Development

```bash
python3 -m unittest discover -s tests
```
