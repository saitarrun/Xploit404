#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import socket
import requests.exceptions


from core.requester import requester
from core.utils import loader, updateVar, var
from core.colors import red, white, end, green, info, run


if __name__ == '__main__':
	print ('''%s
.
  ` .        .             .        . `
      ` .   .  %sOsint_Tools%s  .   . `
          ` .` .         . `. `
              ` . ` . ` . `
                  ` . `
%s''' % (red, white, red, end))
	print ('%s Running component level check' % run)
	print ('%s Starting engine' % run)
	updateVar('path', sys.path[0])
	updateVar('checkedScripts', set())
	loader()
	from core.photon import photon

	from modules.scanner.whatcms import whatcms
	from modules.scanner.portscanner import portscanner
	from modules.scanner.findsubdomains import findsubdomains
	from modules.scanner.security_trails import security_trails
	from modules.scanner.sublister import sublister
	from modules.scanner.waf import detect_waf
	from modules.scanner.headers import analyze_headers
	from modules.scanner.dns_enum import enumerate_dns
	from modules.scanner.content_discovery import discover
	from modules.scanner.services import label_ports
	from modules.scanner.banner import grab_banners
	from modules.scanner.cve import correlate

	print ('%s Turning on radar' % run)
	dataset = {}
	source_1 = findsubdomains(sys.argv[1])
	try:
		source_2 = security_trails(sys.argv[1])
	except AttributeError:
		source_2 = []
	source_3 = sublister(sys.argv[1])
	raw_subdomains = list(set(source_1 + source_2 + source_3))
	raw_subdomains.append(sys.argv[1])
	print ('%s %i targets were caught on radar.' % (info, len(raw_subdomains)))

	unique_ips = {}
	for raw_subdomain in raw_subdomains:
		try:
			ip = socket.gethostbyname(raw_subdomain)
			dataset[raw_subdomain] = {}
			dataset[raw_subdomain]['ip'] = ip
			if ip not in unique_ips:
				open_ports = portscanner([(ip, port) for port in var('ports')])
				dataset[raw_subdomain]['ports'] = open_ports
				unique_ips[ip] = open_ports
				if 443 in open_ports:
					dataset[raw_subdomain]['schema'] = 'https'
				else:
					dataset[raw_subdomain]['schema'] = 'http'
			else:
				open_ports = unique_ips[ip]
				dataset[raw_subdomain]['ports'] = open_ports
				if 443 in open_ports:
					dataset[raw_subdomain]['schema'] = 'https'
				else:
					dataset[raw_subdomain]['schema'] = 'http'
			print ('%s[✈️]%s %s' % (green, end, raw_subdomain))
		except (socket.gaierror, UnicodeError):
			pass

	# print ('%s Deploying wavelet analyzing module to detect hidden targets.' % run)
	# print ('Wavelets analyzed [1/1]')
	print ('%s Deploying Zoom for subdomain takeovers' % run)
	print ('%s Deploying Photon for component assessment' % run)
	print ('%s Deploying Alpha for software fingerprinting' % run)
	print ('%s Deploying Zetanize for identifying entry points' % run)
	print ('%s ETA: %i seconds' % (info, 10 * 2 * len(dataset)))

	for subdomain in dataset:
		url = dataset[subdomain]['schema'] + '://' + subdomain
		takeover = False
		for each in var('sub_takeover'):
			for i in each['cname']:
				if i in url:
					try:
						response = requester(url)
						for i in each['fingerprint']:
							if i in response.text:
								takeover = True
								break
					except requests.exceptions.ConnectionError:
						if each['nxdomain']:
							takeover = True
					break
				break
		dataset[subdomain]['takeover'] = takeover
		dataset[subdomain]['cms'] = whatcms(subdomain)
		dataset[subdomain]['services'] = label_ports(dataset[subdomain]['ports'])
		dataset[subdomain]['dns_records'] = enumerate_dns(subdomain)

		# Grab service banners from open ports, then correlate the versions
		# they reveal against the NVD CVE database.
		print ('%s Grabbing banners on %s' % (run, subdomain))
		banners = grab_banners(subdomain, dataset[subdomain]['ip'],
		                       dataset[subdomain]['ports'])
		dataset[subdomain]['banners'] = banners
		dataset[subdomain]['cves'] = correlate(banners)

		# Fingerprint protections and misconfigurations from a single fetch.
		try:
			resp = requester(url)
			dataset[subdomain]['waf'] = detect_waf(resp)
			dataset[subdomain]['security'] = analyze_headers(resp)
		except requests.exceptions.RequestException:
			dataset[subdomain]['waf'] = []
			dataset[subdomain]['security'] = {}

		# Aggressive content discovery for sensitive files / exposed paths.
		print ('%s Hunting exposed paths on %s' % (run, subdomain))
		dataset[subdomain]['sensitive_paths'] = discover(url)

		crawled = photon(url)
		dataset[subdomain]['forms'] = crawled[0]
		dataset[subdomain]['all_urls'] = list(crawled[1])
		dataset[subdomain]['technologies'] = list(crawled[2])
		dataset[subdomain]['outdated_libs'] = crawled[3]

	print (json.dumps(dataset, indent=4))
