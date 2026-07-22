# Well-known TCP port -> service name, for readable/intelligent output.
COMMON_SERVICES = {
    21: 'ftp', 22: 'ssh', 23: 'telnet', 25: 'smtp', 43: 'whois', 53: 'dns',
    67: 'dhcp', 69: 'tftp', 79: 'finger', 80: 'http', 88: 'kerberos',
    110: 'pop3', 111: 'rpcbind', 119: 'nntp', 123: 'ntp', 135: 'msrpc',
    137: 'netbios-ns', 139: 'netbios-ssn', 143: 'imap', 161: 'snmp',
    179: 'bgp', 389: 'ldap', 443: 'https', 445: 'smb', 465: 'smtps',
    514: 'syslog', 515: 'printer', 543: 'klogin', 587: 'smtp-submission',
    631: 'ipp', 636: 'ldaps', 873: 'rsync', 989: 'ftps-data', 990: 'ftps',
    993: 'imaps', 995: 'pop3s', 1080: 'socks', 1433: 'mssql', 1521: 'oracle',
    1723: 'pptp', 2049: 'nfs', 2082: 'cpanel', 2083: 'cpanel-ssl',
    2181: 'zookeeper', 2375: 'docker', 2376: 'docker-ssl', 3000: 'http-dev',
    3306: 'mysql', 3389: 'rdp', 4444: 'metasploit', 5000: 'http-dev',
    5432: 'postgresql', 5601: 'kibana', 5672: 'amqp', 5900: 'vnc',
    5984: 'couchdb', 6379: 'redis', 7001: 'weblogic', 8000: 'http-alt',
    8008: 'http-alt', 8080: 'http-proxy', 8081: 'http-alt', 8443: 'https-alt',
    8888: 'http-alt', 9000: 'http-alt', 9200: 'elasticsearch',
    9300: 'elasticsearch', 11211: 'memcached', 15672: 'rabbitmq-mgmt',
    27017: 'mongodb', 27018: 'mongodb', 5555: 'freeciv', 6660: 'irc',
}


def label_ports(ports):
    """Map a list of open ports to {port: service} for readable output."""
    return {port: COMMON_SERVICES.get(port, 'unknown') for port in ports}
