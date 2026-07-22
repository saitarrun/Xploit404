# Comprehensive Exploitation & Penetration Testing Tools Guide

This document describes all 12 newly integrated penetration testing tools in the Striker toolkit.

## Quick Reference Table

| Key | Tool | Category | Aliases | Installation |
|-----|------|----------|---------|--------------|
| 26  | Metasploit | Exploitation & Frameworks | metasploit, msf | apt install metasploit-framework |
| 27  | SearchSploit | Exploitation & Frameworks | searchsploit, exploit-db | apt install exploitdb |
| 28  | Burp Suite | Web Application Testing | burpsuite, burp | Download or apt install burpsuite |
| 29  | SQLmap | Web Application Testing | sqlmap, sqli | git clone sqlmap repo |
| 30  | Nikto | Web Application Testing | nikto, webserver | apt install nikto |
| 31  | Gobuster | Web Application Testing | gobuster, fuzz, dir | go install or apt install gobuster |
| 32  | Hydra | Credential Testing | hydra, brute, bruteforce | apt install hydra |
| 33  | John the Ripper | Credential Testing | john, crack, password | apt install john |
| 34  | Hashcat | Credential Testing | hashcat, gpu-crack | Download from hashcat.net |
| 35  | Aircrack-ng | Wireless & Network | aircrack, wireless, wifi | apt install aircrack-ng |
| 36  | Wireshark | Wireless & Network | wireshark, tshark, pcap | apt install wireshark |
| 37  | Mimikatz | Windows Post-Exploitation | mimikatz, credentials, lsass | Download (Windows only) |

## Detailed Tool Descriptions

### EXPLOITATION & FRAMEWORKS

#### [26] Metasploit Framework

The world's most used penetration testing framework. Develop and execute exploit payloads, run post-exploitation modules.

**Install:**
```bash
sudo apt install metasploit-framework        # Linux
brew install metasploit                      # macOS
# or https://docs.metasploit.com/docs/using-metasploit/getting-started.html
```

**Usage:**
```bash
python menu.py 26                            # Interactive mode
python menu.py metasploit search wordpress   # Search exploits
```

**Features:**
- Interactive msfconsole launcher
- Exploit database search
- Payload generation & module execution
- Profile-aware rate limiting

---

#### [27] SearchSploit / Exploit-DB

Offline search of Exploit-DB database for CVEs, exploits, and vulnerability codes.

**Install:**
```bash
sudo apt install exploitdb                   # Linux
brew install exploitdb                       # macOS
pip install exploitdb                        # Python
```

**Usage:**
```bash
python menu.py 27                            # Interactive search
python menu.py searchsploit CVE-2024-1234    # Search CVE
python menu.py searchsploit wordpress        # Search app
```

**Features:**
- Offline exploit research
- CVE lookups
- JSON output support
- Database update capability

---

### WEB APPLICATION TESTING

#### [28] Burp Suite

Industry-leading web application security testing platform. GUI-based testing for vulnerability identification.

**Install:**
```bash
# Download from https://portswigger.net/burp/community-download
# or: apt install burpsuite
```

**Usage:**
```bash
python menu.py 28              # Launch GUI
python menu.py burpsuite       # By name
```

**Features:**
- Interactive web testing UI
- Proxy/spidering/scanning
- Custom payloads
- Headless mode support

---

#### [29] SQLmap

Automatic SQL injection detection and database exploitation tool.

**Install:**
```bash
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap
```

**Usage:**
```bash
python menu.py 29                           # Interactive mode
python menu.py sqlmap "http://target.com?id=1" B   # Boolean attack
```

**Features:**
- Automatic SQL injection detection
- Multi-technique support (Boolean, Error, Union, etc)
- Database extraction
- Custom injection points

---

#### [30] Nikto

Web server vulnerability scanner with 6700+ checks for outdated versions, misconfigurations, and security issues.

**Install:**
```bash
sudo apt install nikto                      # Linux
brew install nikto                          # macOS
```

**Usage:**
```bash
python menu.py 30                           # Interactive mode
python menu.py nikto example.com 80         # Scan host:port
```

**Features:**
- 6700+ security checks
- Plugin-based scanning
- Multiple output formats
- SSL/TLS support

---

#### [31] Gobuster

Fast brute force tool for URIs, DNS subdomains, and VHOST names.

**Install:**
```bash
go install github.com/OJ/gobuster/v3@latest    # Go
sudo apt install gobuster                       # Linux
```

**Usage:**
```bash
python menu.py 31                               # Interactive (dir/dns)
python menu.py gobuster dir https://target.com # Directory brute force
python menu.py gobuster dns example.com        # Subdomain enumeration
```

**Features:**
- Directory/file brute forcing
- DNS subdomain enumeration
- VHOST discovery
- Custom wordlist support

---

### CREDENTIAL TESTING

#### [32] Hydra

Fast network logon cracker supporting SSH, FTP, HTTP, MySQL, HTTPS, LDAP, and many more protocols.

**Install:**
```bash
sudo apt install hydra                      # Linux
brew install hydra                          # macOS
```

**Usage:**
```bash
python menu.py 32                                           # Interactive mode
python menu.py hydra target.com:22 ssh username password   # SSH brute force
```

**Features:**
- Multi-protocol support
- Parallel attack threads
- Wordlist/dictionary attacks
- Proxy support

---

#### [33] John the Ripper

Fast password cracking tool supporting multiple hash types.

**Install:**
```bash
sudo apt install john                       # Linux
brew install john-jumbo                     # macOS
```

**Usage:**
```bash
python menu.py 33                                    # Interactive mode
python menu.py john hashes.txt dictionary.txt sha512  # Crack with dictionary
```

**Features:**
- 300+ hash formats
- Dictionary attacks
- Incremental mode (brute force)
- Jumbo edition: GPU support

---

#### [34] Hashcat

GPU-accelerated password recovery supporting 300+ hash types.

**Install:**
```bash
# Download from https://hashcat.net/download/
# Linux: apt install hashcat (may be outdated)
```

**Usage:**
```bash
python menu.py 34                              # Interactive mode
python menu.py hashcat hashes.txt 0 dictionary.txt  # MD5 + dictionary
```

**Features:**
- GPU acceleration (NVIDIA/AMD/Intel)
- 300+ hash algorithms
- Multiple attack modes
- Wordlist + rules + masks

---

### WIRELESS & NETWORK

#### [35] Aircrack-ng

Wireless network security auditing toolkit for WiFi penetration testing.

**Install:**
```bash
sudo apt install aircrack-ng                # Linux
brew install aircrack-ng                    # macOS
```

**Usage:**
```bash
python menu.py 35                               # Interactive mode
python menu.py aircrack capture.cap rockyou.txt # Crack handshake
```

**Features:**
- WPA/WPA2 handshake cracking
- Wireless packet capture (airodump-ng)
- Monitoring mode detection
- Dictionary attacks

---

#### [36] Wireshark / tshark

Network protocol analyzer for packet capture and deep packet inspection.

**Install:**
```bash
sudo apt install wireshark                  # Linux
brew install wireshark                      # macOS
```

**Usage:**
```bash
python menu.py 36                                      # Interactive (GUI/capture/read)
python menu.py wireshark capture eth0 100             # Capture 100 packets
python menu.py wireshark read capture.pcap            # Read PCAP file
```

**Features:**
- Live packet capture
- PCAP file analysis
- Display filters
- Protocol dissection
- JSON/CSV export

---

### WINDOWS POST-EXPLOITATION

#### [37] Mimikatz

Windows credential extraction and impersonation tool. Dumps plaintext passwords, hashes, and Kerberos tickets.

**Install:**
```bash
# Download from https://github.com/gentilkiwi/mimikatz/releases
# Windows only
```

**Usage:**
```bash
python menu.py 37                      # Interactive (requires admin)
python menu.py mimikatz extract        # Extract credentials
python menu.py mimikatz sam            # Dump SAM database
python menu.py mimikatz lsass          # Dump LSASS process
```

**Features:**
- Credential extraction from memory
- SAM database dumping
- LSASS memory dumping
- Kerberos ticket manipulation
- Windows admin required

---

## Usage Workflows

### Complete Web Application Assessment

```bash
# 1. Enumerate web server
python menu.py nikto example.com 80

# 2. Find directories/files
python menu.py 31                              # Gobuster
# or: python menu.py gobuster dir http://example.com

# 3. Test for SQL injection
python menu.py 29                              # SQLmap
# or: python menu.py sqlmap "http://example.com?id=1"

# 4. Manual testing with Burp
python menu.py 28                              # Burp Suite GUI
```

### Credential Harvesting & Cracking

```bash
# 1. Extract hashes from capture
# Use Wireshark to analyze traffic
python menu.py 36

# 2. Brute force login services
python menu.py 32                              # Hydra
# or: python menu.py hydra target:22 ssh user pass

# 3. Crack collected hashes
python menu.py 33                              # John the Ripper
# or: python menu.py 34                        # Hashcat (GPU)
```

### Wireless Security Assessment

```bash
# 1. Scan networks with Nikto
python menu.py 30

# 2. Capture handshake
python menu.py 35                              # Aircrack-ng

# 3. Analyze traffic with Wireshark
python menu.py 36

# 4. Crack captured handshake
python menu.py aircrack capture.cap wordlist.txt
```

### Complete Exploitation Chain

```bash
# 1. Search for known exploits
python menu.py 26                              # Metasploit
python menu.py 27                              # SearchSploit

# 2. Generate payload
python menu.py metasploit search wordpress

# 3. Execute exploit
python menu.py 26 (interactive mode)

# 4. Post-exploitation on Windows
python menu.py 37                              # Mimikatz
```

---

## Integration with Striker

All 12 tools integrate seamlessly with Striker's existing framework:

### Menu Integration
- **Interactive mode:** Select tools by number (26-37) or name
- **CLI mode:** Run directly: `python menu.py <tool> [args]`
- **Readiness checks:** `python menu.py doctor` shows installation status
- **Profile system:** Tools respect standard/intensive profiles
- **Output storage:** Results automatically saved to `output/` directory

### Available Access Methods

```bash
# Interactive menu
python menu.py
# Then select: 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37

# Command line - by key
python menu.py 26              # Metasploit

# Command line - by name
python menu.py metasploit
python menu.py burpsuite
python menu.py hydra

# Command line - by alias
python menu.py msf
python menu.py sqlmap
python menu.py john
```

---

## Recommended Installation

### Quick Setup (macOS)
```bash
brew install metasploit exploitdb nikto hydra john aircrack-ng wireshark gobuster
```

### Quick Setup (Linux)
```bash
sudo apt update && sudo apt install -y \
  metasploit-framework exploitdb nikto hydra john aircrack-ng wireshark gobuster
```

### Manual Installations
- **Burp Suite:** Download from https://portswigger.net/burp
- **SQLmap:** `git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git`
- **Hashcat:** Download from https://hashcat.net
- **Mimikatz:** Download from https://github.com/gentilkiwi/mimikatz (Windows only)
- **Gobuster:** `go install github.com/OJ/gobuster/v3@latest`

---

## Tool Categories in Striker

```
Striker (37 total tools)
├── Domain & Network (1-11)        - 11 OSINT tools
├── Identity & Social (12-17)       - 6 Social OSINT tools
├── Search & Dorks (18-21)          - 4 Search/Dork tools
├── Vulnerability & Analysis (22-23) - 2 Vuln tools
├── Dark Web (24-25)                - 2 Dark Web tools
├── Exploitation & Frameworks (26-27) - 2 Frameworks
├── Web Application Testing (28-31) - 4 Web tools
├── Credential Testing (32-34)      - 3 Cracking tools
├── Wireless & Network (35-36)      - 2 Network tools
└── Windows Post-Exploitation (37)  - 1 Windows tool
```

---

## Penetration Testing Workflow

**Complete penetration testing pipeline now includes:**

1. **Reconnaissance (OSINT)** → Tools 1-25
2. **Vulnerability Research** → Tools 26-27 (SearchSploit)
3. **Vulnerability Assessment** → Tools 28-31 (Web testing)
4. **Credential Testing** → Tools 32-34 (Cracking)
5. **Network Analysis** → Tools 35-36 (Wireless/Packet)
6. **Exploitation** → Tools 26 (Metasploit)
7. **Post-Exploitation** → Tool 37 (Mimikatz)

All results are logged to `output/` for post-engagement analysis.

---

## Authorized Testing Reminder

**IMPORTANT:** These are dual-use security tools. Usage is authorized ONLY in:
- Authorized penetration testing engagements
- Your own systems/applications
- Legitimate educational contexts

Unauthorized access to computer systems is illegal.

---

## File Structure

```
modules/tools/
├── metasploit.py      (Tool #26)
├── searchsploit.py    (Tool #27)
├── burpsuite.py       (Tool #28)
├── sqlmap.py          (Tool #29)
├── nikto.py           (Tool #30)
├── gobuster.py        (Tool #31)
├── hydra.py           (Tool #32)
├── john.py            (Tool #33)
├── hashcat.py         (Tool #34)
├── aircrack.py        (Tool #35)
├── wireshark.py       (Tool #36)
└── mimikatz.py        (Tool #37)
```

---

## Support & Documentation

Each tool module implements:
- `is_installed()` - Check if tool is available
- `ready()` - Return (status, detail) tuple
- `install_hint()` - Provide installation instructions
- `run_*()` - Interactive handler
- `cli_*()` - CLI handler
- `ready_*()` - Menu integration hook

For detailed help on any tool:
```bash
python menu.py doctor      # See all tools & status
python menu.py help        # General help
python menu.py <tool> help # Tool-specific help
```
