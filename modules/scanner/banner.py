import ssl
import socket
import concurrent.futures

# Ports that speak TLS as soon as you connect.
TLS_PORTS = {443, 465, 636, 989, 990, 993, 995, 2083, 2087, 2096, 8443, 9443}
# Ports where sending an HTTP request is the way to elicit a banner.
HTTP_PORTS = {80, 81, 88, 443, 591, 2082, 2083, 3000, 5000, 8000, 8008,
              8080, 8081, 8443, 8888, 9000, 9090, 9200, 9443}


def _extract(data, port):
    if not data:
        return None
    # Skip binary protocols (e.g. nmap's echo service) - only surface banners
    # that are predominantly printable text.
    printable = sum(1 for b in data if 32 <= b < 127 or b in (9, 10, 13))
    if printable / len(data) < 0.75:
        return None
    text = data.decode('latin-1', 'replace').strip()
    if not text:
        return None
    if text.startswith('HTTP/'):
        lines = text.split('\r\n')
        parts = [lines[0]]  # status line
        for line in lines[1:]:
            low = line.lower()
            if low.startswith(('server:', 'x-powered-by:')):
                parts.append(line.strip())
        return ' | '.join(parts)
    # Non-HTTP service greeting (SSH/FTP/SMTP/etc.) - keep the first line.
    return text.splitlines()[0][:200]


def _grab(host, ip, port, timeout):
    try:
        sock = socket.create_connection((ip, port), timeout=timeout)
    except OSError:
        return port, None
    try:
        sock.settimeout(timeout)
        if port in TLS_PORTS:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            try:
                sock = ctx.wrap_socket(sock, server_hostname=host)
            except (ssl.SSLError, OSError):
                return port, None
        if port in HTTP_PORTS or port in TLS_PORTS:
            req = ('HEAD / HTTP/1.0\r\nHost: %s\r\n'
                   'User-Agent: Mozilla/5.0\r\n\r\n' % host)
            sock.sendall(req.encode())
        data = sock.recv(2048)
        return port, _extract(data, port)
    except OSError:
        return port, None
    finally:
        try:
            sock.close()
        except OSError:
            pass


def grab_banners(host, ip, ports, timeout=4, workers=20):
    """Grab service banners from the given open ports. Returns
    {port: banner_string} for the ports that responded."""
    banners = {}
    if not ports:
        return banners
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_grab, host, ip, p, timeout) for p in ports]
        for fut in concurrent.futures.as_completed(futures):
            port, banner = fut.result()
            if banner:
                banners[port] = banner
    return banners
