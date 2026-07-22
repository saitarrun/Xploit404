"""Beautiful xploit404 styled UI for Striker Toolkit."""

import os
import sys
from colorama import Fore, Back, Style, init

init(autoreset=True)


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_banner():
    """Print xploit404 style banner."""
    banner = f"""
{Fore.CYAN}
    ███████╗████████╗██████╗ ██╗██╗  ██╗███████╗██████╗ 
    ██╔════╝╚══██╔══╝██╔══██╗██║██║ ██╔╝██╔════╝██╔══██╗
    ███████╗   ██║   ██████╔╝██║█████╔╝ █████╗  ██████╔╝
    ╚════██║   ██║   ██╔══██╗██║██╔═██╗ ██╔══╝  ██╔══██╗
    ███████║   ██║   ██║  ██║██║██║  ██╗███████╗██║  ██║
    ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    
{Fore.YELLOW}                  Penetration Testing Toolkit{Style.RESET_ALL}
{Fore.MAGENTA}              52 Tools | 5 Red Team Phases | Enterprise Ready{Style.RESET_ALL}
{Fore.CYAN}{'═' * 75}
"""
    print(banner)


def print_category_section(category_name, tools, session_info):
    """Print tools organized by category."""
    print(f"\n{Fore.GREEN}[+]{Style.RESET_ALL} {Fore.CYAN}{category_name}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'─' * 73}{Style.RESET_ALL}")
    
    for tool in tools:
        key = tool['key'].rjust(2)
        name = tool['name'].ljust(30)
        aliases = ', '.join(tool.get('aliases', [])[:2])
        desc = tool['desc'][:35]
        
        # Color code by ready status
        try:
            ready_func = tool.get('ready')
            if ready_func:
                is_ready, status = ready_func()
                status_icon = f"{Fore.GREEN}✓{Style.RESET_ALL}" if is_ready else f"{Fore.RED}✗{Style.RESET_ALL}"
            else:
                status_icon = f"{Fore.YELLOW}?{Style.RESET_ALL}"
        except:
            status_icon = f"{Fore.YELLOW}?{Style.RESET_ALL}"
        
        print(f"  {status_icon} [{Fore.YELLOW}{key}{Style.RESET_ALL}] {Fore.CYAN}{name}{Style.RESET_ALL} {desc}")


def print_tools_by_phase(tools):
    """Display tools organized by red team phases."""
    print(f"\n{Fore.MAGENTA}{'═' * 75}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] RED TEAM PHASES{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'═' * 75}{Style.RESET_ALL}")
    
    # Group by category (which represents phases)
    categories = {}
    for tool in tools:
        cat = tool.get('cat', 'Other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)
    
    # Print in order
    phase_order = [
        'Advanced Reconnaissance',
        'Initial Access & Delivery',
        'C2 & Command Control',
        'Post-Exploitation',
        'Continuous Security Testing',
        'Domain & Network',
        'Identity & Social',
        'Search & Dorks',
        'Vulnerability & Analysis',
        'Dark Web',
        'Exploitation & Frameworks',
        'Web Application Testing',
        'Credential Testing',
        'Wireless & Network',
        'Cryptography & Cipher Tools',
    ]
    
    for phase in phase_order:
        if phase in categories:
            print_category_section(phase, categories[phase], {})


def print_quick_reference(tools):
    """Print quick reference guide."""
    print(f"\n{Fore.MAGENTA}{'═' * 75}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] QUICK REFERENCE{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'═' * 75}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}Usage:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}[NUMBER]{Style.RESET_ALL}         Run tool by ID (e.g., {Fore.YELLOW}1{Style.RESET_ALL} for Domain Scanner)")
    print(f"  {Fore.GREEN}[ALIAS]{Style.RESET_ALL}          Run tool by alias (e.g., {Fore.YELLOW}nmap{Style.RESET_ALL} for Nmap)")
    print(f"  {Fore.GREEN}[TARGET]{Style.RESET_ALL}         Set session target (e.g., {Fore.YELLOW}target example.com{Style.RESET_ALL})")
    print(f"  {Fore.GREEN}help{Style.RESET_ALL}             Show help menu")
    print(f"  {Fore.GREEN}doctor{Style.RESET_ALL}           Check toolkit status")
    print(f"  {Fore.GREEN}list{Style.RESET_ALL}             List all tools")
    print(f"  {Fore.GREEN}quit{Style.RESET_ALL}             Exit program\n")
    
    print(f"{Fore.CYAN}Examples:{Style.RESET_ALL}")
    print(f"  striker> {Fore.YELLOW}1{Style.RESET_ALL}                 Run Domain Scanner")
    print(f"  striker> {Fore.YELLOW}40{Style.RESET_ALL}                Run Amass")
    print(f"  striker> {Fore.YELLOW}cipher{Style.RESET_ALL}             Run Cipher Toolkit")
    print(f"  striker> {Fore.YELLOW}nmap example.com{Style.RESET_ALL}    Run Nmap against example.com")


def print_toolkit_stats(tools):
    """Print toolkit statistics."""
    ready_count = 0
    for tool in tools:
        try:
            ready_func = tool.get('ready')
            if ready_func:
                is_ready, _ = ready_func()
                if is_ready:
                    ready_count += 1
        except:
            pass
    
    print(f"\n{Fore.MAGENTA}{'═' * 75}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] TOOLKIT STATISTICS{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'═' * 75}{Style.RESET_ALL}")
    
    total = len(tools)
    pct = 100 * ready_count // total if total > 0 else 0
    
    print(f"{Fore.CYAN}  Total Tools:{Style.RESET_ALL}        {Fore.YELLOW}{total}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  Ready:{Style.RESET_ALL}              {Fore.GREEN}{ready_count}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  Not Ready:{Style.RESET_ALL}          {Fore.RED}{total - ready_count}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  Completion:{Style.RESET_ALL}         {Fore.YELLOW}{pct}%{Style.RESET_ALL}\n")


def interactive_menu():
    """Main interactive menu with beautiful UI."""
    from menu import TOOLS, SESSION
    
    clear_screen()
    print_banner()
    print_tools_by_phase(TOOLS)
    print_quick_reference(TOOLS)
    print_toolkit_stats(TOOLS)
    
    print(f"{Fore.MAGENTA}{'═' * 75}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {Fore.CYAN}Striker Ready - Type 'help' for commands{Style.RESET_ALL}\n")
    
    while True:
        try:
            profile = SESSION.get('profile', 'standard')
            domain = SESSION.get('domain') or 'none'
            
            prompt = f"{Fore.YELLOW}striker{Style.RESET_ALL}({Fore.MAGENTA}{profile}{Style.RESET_ALL})({Fore.CYAN}{domain}{Style.RESET_ALL})> "
            cmd = input(prompt).strip().lower()
            
            if not cmd:
                continue
            
            # Import here to avoid circular imports
            from menu import TOOLS, help_menu, list_tools, doctor_check
            
            parts = cmd.split()
            tool_id = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            if tool_id in ['quit', 'exit', 'q']:
                print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Exiting Striker...")
                break
            elif tool_id == 'help' or tool_id == '?':
                print(help_menu())
            elif tool_id == 'doctor':
                print(doctor_check(TOOLS))
            elif tool_id == 'list' or tool_id == 'ls':
                print(list_tools(TOOLS))
            elif tool_id == 'clear' or tool_id == 'cls':
                clear_screen()
                print_banner()
            else:
                # Find and run tool
                tool = None
                for t in TOOLS:
                    if t['key'] == tool_id or t['key'].lstrip('0') == tool_id or tool_id in t.get('aliases', []):
                        tool = t
                        break
                
                if tool:
                    try:
                        ready_func = tool.get('ready')
                        if ready_func:
                            is_ready, status = ready_func()
                            if not is_ready:
                                print(f"{Fore.RED}[-]{Style.RESET_ALL} Tool not ready: {status}")
                                continue
                        
                        if args:
                            cli_func = tool.get('cli')
                            if cli_func:
                                result = cli_func(args)
                                print(result if isinstance(result, str) else str(result))
                        else:
                            runner_func = tool.get('runner')
                            if runner_func:
                                result = runner_func()
                                print(result if isinstance(result, str) else str(result))
                    except KeyboardInterrupt:
                        print(f"\n{Fore.YELLOW}[!]{Style.RESET_ALL} Interrupted")
                    except EOFError:
                        print(f"\n{Fore.YELLOW}[!]{Style.RESET_ALL} Input required - run in interactive mode")
                else:
                    print(f"{Fore.RED}[-]{Style.RESET_ALL} Unknown command: {tool_id}")
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!]{Style.RESET_ALL} Interrupted")
            break
        except Exception as e:
            print(f"{Fore.RED}[-]{Style.RESET_ALL} Error: {str(e)}")


if __name__ == '__main__':
    interactive_menu()
