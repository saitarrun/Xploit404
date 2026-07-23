"""Google dork query builder — a terminal-native reimplementation of the
Advanced Google Dork Generator (https://github.com/str1k3r0p/GoogleDorks).

The upstream project is a browser app; this module runs the same idea directly
in the terminal: pick a domain and a category and it emits ready-to-use Google
search queries (and the matching search URLs) without opening a browser.

Use only against domains you own or are authorised to test.
"""

from urllib.parse import quote_plus


# (category name, [dork templates]).  "{domain}" is filled in at run time.
# Mirrors the bugBountyCategories dataset from the upstream generator.
DORK_CATEGORIES = [
    ('Admin & Login Pages', [
        'site:{domain} inurl:admin',
        'site:{domain} inurl:login',
        'site:{domain} inurl:dashboard',
        'site:{domain} inurl:wp-admin',
        'site:{domain} inurl:controlpanel',
        'site:{domain} inurl:adminpanel',
        'site:{domain} inurl:administrator',
        'site:{domain} inurl:moderator',
        'site:{domain} inurl:webadmin',
        'site:{domain} inurl:backoffice',
        'site:{domain} inurl:backend',
        'site:{domain} inurl:auth',
        'site:{domain} inurl:portal',
        'site:{domain} inurl:staff',
        'site:{domain} inurl:manage',
    ]),
    ('Sensitive Information', [
        'site:{domain} "password"',
        'site:{domain} "config"',
        'site:{domain} "credentials"',
        'site:{domain} "secret"',
        'site:{domain} "api_key"',
        'site:{domain} "private key"',
        'site:{domain} "client_secret"',
        'site:{domain} "access_token"',
        'site:{domain} "dbpassword"',
        'site:{domain} "authorize"',
        'site:{domain} "confidential"',
        'site:{domain} "ssh key"',
        'site:{domain} "passwd"',
        'site:{domain} "authorization_bearer"',
        'site:{domain} "auth_token"',
        'site:{domain} "oauth_token"',
        'site:{domain} "token"',
        'site:{domain} "refresh_token"',
    ]),
    ('File Types & Documents', [
        'site:{domain} filetype:pdf',
        'site:{domain} filetype:doc OR filetype:docx',
        'site:{domain} filetype:xls OR filetype:xlsx',
        'site:{domain} filetype:ppt OR filetype:pptx',
        'site:{domain} filetype:txt',
        'site:{domain} filetype:csv',
        'site:{domain} filetype:zip OR filetype:rar OR filetype:tar OR filetype:gz',
        'site:{domain} filetype:sql',
        'site:{domain} filetype:bak',
        'site:{domain} filetype:log',
        'site:{domain} filetype:xml',
        'site:{domain} filetype:json',
        'site:{domain} filetype:env',
        'site:{domain} filetype:conf',
        'site:{domain} filetype:yaml OR filetype:yml',
        'site:{domain} filetype:rsa OR filetype:pem OR filetype:key',
        'site:{domain} filetype:svg',
        'site:{domain} filetype:jsp OR filetype:asp OR filetype:aspx OR filetype:php',
    ]),
    ('Directory & File Exposure', [
        'site:{domain} intitle:"index of"',
        'site:{domain} inurl:ftp',
        'site:{domain} inurl:uploads',
        'site:{domain} intext:"Index of /"',
        'site:{domain} intitle:"Directory Listing For"',
        'site:{domain} intext:"Parent Directory"',
        'site:{domain} intitle:"Index of" intext:".env"',
        'site:{domain} intitle:"Index of" intext:"config.php"',
        'site:{domain} intitle:"Index of" intext:"credentials"',
        'site:{domain} intitle:"Index of /backup"',
        'site:{domain} intitle:"Index of /admin"',
        'site:{domain} intitle:"Index of /config"',
        'site:{domain} intitle:"Index of /database"',
        'site:{domain} intitle:"Index of /password"',
        'site:{domain} intitle:"Index of /private"',
        'site:{domain} intitle:"Index of /wp-content/"',
        'site:{domain} intitle:"Index of /download"',
        'site:{domain} intitle:"Index of /logs"',
    ]),
    ('Configuration Files', [
        'site:{domain} "config.php"',
        'site:{domain} "settings.py"',
        'site:{domain} "database.yml"',
        'site:{domain} "web.config"',
        'site:{domain} inurl:".env"',
        'site:{domain} inurl:"wp-config.php"',
        'site:{domain} inurl:"configuration.php"',
        'site:{domain} inurl:"settings.json"',
        'site:{domain} inurl:"config.json"',
        'site:{domain} inurl:"application.yaml"',
        'site:{domain} inurl:"config.inc.php"',
        'site:{domain} inurl:"configuration.xml"',
        'site:{domain} inurl:"app.config"',
        'site:{domain} inurl:"application.properties"',
        'site:{domain} inurl:"appsettings.json"',
        'site:{domain} inurl:".npmrc" OR inurl:".yarnrc"',
        'site:{domain} inurl:"docker-compose.yml"',
        'site:{domain} inurl:"Dockerfile"',
    ]),
    ('API & GraphQL Endpoints', [
        'site:{domain} inurl:api | site:*/rest | site:*/v1 | site:*/v2 | site:*/v3',
        'site:{domain} intext:"api documentation"',
        'site:{domain} inurl:swagger | inurl:api-docs',
        'site:{domain} inurl:api/admin',
        'site:{domain} inurl:api/users',
        'site:{domain} inurl:api/auth',
        'site:{domain} inurl:graphql',
        'site:{domain} inurl:api.php',
        'site:{domain} inurl:api/v1/auth',
        'site:{domain} inurl:graphiql',
        'site:{domain} inurl:graphql.php',
        'site:{domain} inurl:graphql/console',
        'site:{domain} "query {" "__schema"',
        'site:{domain} intitle:"GraphiQL"',
        'site:{domain} inurl:playground',
        'site:{domain} inurl:api/token',
        'site:{domain} inurl:api/v1/user',
        'site:{domain} inurl:api/data',
        'site:{domain} inurl:api/password/reset',
        'site:{domain} inurl:graphql intext:"query" intext:"mutation"',
    ]),
    ('Authentication Issues', [
        'site:{domain} intext:"jwt token"',
        'site:{domain} intext:"Bearer eyJ"',
        'site:{domain} intext:"Authorization: Bearer"',
        'site:{domain} inurl:jwt',
        'site:{domain} inurl:callback',
        'site:{domain} inurl:oauth/authorize',
        'site:{domain} inurl:redirect_uri',
        'site:{domain} inurl:return_to',
        'site:{domain} inurl:oauth/token',
        'site:{domain} inurl:client_id',
        'site:{domain} inurl:response_type=token',
        'site:{domain} inurl:saml',
        'site:{domain} inurl:openid',
        'site:{domain} inurl:authorize',
        'site:{domain} inurl:auth/callback',
        'site:{domain} inurl:sso',
        'site:{domain} inurl:forgot-password',
        'site:{domain} inurl:reset',
        'site:{domain} inurl:verify',
        'site:{domain} inurl:2fa',
    ]),
    ('CORS & Header Issues', [
        'site:{domain} intext:"Access-Control-Allow-Origin: *"',
        'site:{domain} intext:"Access-Control-Allow-Credentials: true"',
        'site:{domain} intext:"crossorigin"',
        'site:{domain} intext:"X-XSS-Protection: 0"',
        'site:{domain} intext:"Content-Security-Policy"',
        'site:{domain} intext:"X-Frame-Options: DENY"',
        'site:{domain} intext:"Strict-Transport-Security"',
        'site:{domain} intext:"Access-Control-Expose-Headers"',
        'site:{domain} intext:"X-Content-Type-Options"',
    ]),
    ('Cloud Storage & Misconfig', [
        'site:s3.amazonaws.com "{domain}"',
        'site:blob.core.windows.net "{domain}"',
        'site:googleapis.com "{domain}"',
        'site:drive.google.com "{domain}"',
        'site:dev.azure.com "{domain}"',
        'site:onedrive.live.com "{domain}"',
        'site:digitaloceanspaces.com "{domain}"',
        'site:sharepoint.com "{domain}"',
        'site:s3-external-1.amazonaws.com "{domain}"',
        'site:s3.dualstack.us-east-1.amazonaws.com "{domain}"',
        'site:dropbox.com/s "{domain}"',
        'site:box.com/s "{domain}"',
        'site:docs.google.com inurl:"/d/" "{domain}"',
        'site:storage.googleapis.com "{domain}"',
        'site:amazonaws.com intext:"{domain}"',
        'site:firebasestorage.googleapis.com "{domain}"',
        'site:firebase.io "{domain}"',
        'site:firebaseio.com "{domain}"',
        'site:"{domain}".s3.amazonaws.com',
        'site:storage.cloud.google.com "{domain}"',
        'site:azurewebsites.net "{domain}"',
        'site:cloudfront.net "{domain}"',
    ]),
    ('WebSockets & Mobile APIs', [
        'site:{domain} inurl:websocket',
        'site:{domain} inurl:socket.io',
        'site:{domain} intext:"ws://"',
        'site:{domain} intext:"wss://"',
        'site:{domain} "WebSocket connection"',
        'site:{domain} intext:"mobile api"',
        'site:{domain} inurl:api/mobile',
        'site:{domain} inurl:mobileapi',
        'site:{domain} inurl:app/api',
        'site:{domain} inurl:mobile/api',
        'site:{domain} inurl:api/app',
        'site:{domain} inurl:app/v1',
        'site:{domain} inurl:mobile/v1',
        'site:{domain} inurl:app.json',
        'site:{domain} inurl:api/ios',
        'site:{domain} inurl:api/android',
    ]),
    ('SSRF Vulnerable Params', [
        'inurl:http | inurl:url= | inurl:path= | inurl:dest= | inurl:html= | inurl:data= | inurl:domain= | inurl:page= inurl:& site:{domain}',
        'inurl:proxy | inurl:fetch | inurl:process | inurl:pull | inurl:retrieve inurl:& site:{domain}',
        'inurl:go | inurl:redirect | inurl:return | inurl:src | inurl:source | inurl:u | inurl:uri | inurl:url inurl:& site:{domain}',
        'inurl:window | inurl:next | inurl:target | inurl:rurl | inurl:dest inurl:& site:{domain}',
        'inurl:api inurl:fetch inurl:& site:{domain}',
        'inurl:load= inurl:& site:{domain}',
        'inurl:file= inurl:& site:{domain}',
        'inurl:resource= inurl:& site:{domain}',
        'inurl:host= inurl:& site:{domain}',
        'inurl:preview= inurl:& site:{domain}',
        'inurl:view= inurl:& site:{domain}',
        'inurl:validate= inurl:& site:{domain}',
    ]),
    ('XSS Vulnerable Params', [
        'inurl:q= | inurl:s= | inurl:search= | inurl:query= | inurl:keyword= | inurl:lang= inurl:& site:{domain}',
        'inurl:msg= | inurl:text= | inurl:error= | inurl:title= | inurl:description= | inurl:content= inurl:& site:{domain}',
        'inurl:name= | inurl:message= | inurl:body= | inurl:feedback= inurl:& site:{domain}',
        'inurl:alert= inurl:& site:{domain}',
        'inurl:caption= inurl:& site:{domain}',
        'inurl:html= inurl:& site:{domain}',
        'inurl:comment= inurl:& site:{domain}',
        'inurl:subject= inurl:& site:{domain}',
        'inurl:callback= inurl:& site:{domain}',
        'inurl:redirect= inurl:& site:{domain}',
        'inurl:return= inurl:& site:{domain}',
        'inurl:next= inurl:& site:{domain}',
    ]),
    ('SQL Injection Params', [
        'inurl:id= | inurl:pid= | inurl:category= | inurl:cat= | inurl:action= | inurl:sid= | inurl:dir= inurl:& site:{domain}',
        'inurl:user= | inurl:uid= | inurl:article= | inurl:item= | inurl:page_id= inurl:& site:{domain}',
        'inurl:view= | inurl:product= | inurl:news= | inurl:file= | inurl:type= inurl:& site:{domain}',
        'inurl:tracking= inurl:& site:{domain}',
        'inurl:ref= inurl:& site:{domain}',
        'inurl:orderid= inurl:& site:{domain}',
        'inurl:cartid= inurl:& site:{domain}',
        'inurl:content= inurl:& site:{domain}',
        'inurl:section= inurl:& site:{domain}',
        'inurl:index.php?id= site:{domain}',
        'inurl:gallery.php?id= site:{domain}',
        'inurl:products.php?id= site:{domain}',
    ]),
    ('RCE Vulnerable Params', [
        'inurl:cmd | inurl:exec= | inurl:query= | inurl:code= | inurl:do= | inurl:run= | inurl:read= | inurl:ping= inurl:& site:{domain}',
        'inurl:system= | inurl:os= | inurl:execute= | inurl:shell= | inurl:download= inurl:& site:{domain}',
        'inurl:eval= | inurl:command= | inurl:execute= | inurl:script= | inurl:payload= inurl:& site:{domain}',
        'inurl:bash= inurl:& site:{domain}',
        'inurl:nslookup= inurl:& site:{domain}',
        'inurl:phpinfo= inurl:& site:{domain}',
        'inurl:proc= inurl:& site:{domain}',
        'inurl:curl= inurl:& site:{domain}',
        'inurl:wget= inurl:& site:{domain}',
        'inurl:whoami= inurl:& site:{domain}',
        'inurl:nc= inurl:& site:{domain}',
    ]),
    ('Template Injection', [
        'site:{domain} intext:"{{\'7\'*7}}"',
        'site:{domain} intext:"${7*7}"',
        'site:{domain} intext:"{{7*7}}"',
        'site:{domain} intext:"<%= 7*7 %>"',
        'site:{domain} intext:"#{7*7}"',
        'site:{domain} intext:"{{\'\'.constructor.constructor}}"',
        'site:{domain} intext:"{{config.items()}}"',
        'site:{domain} intext:"{{request}}"',
        'site:{domain} intext:"{{self}}"',
        'site:{domain} intext:"{{config}}"',
        'site:{domain} intext:"{{request.application.__globals__}}"',
        'site:{domain} intext:"{{request.__class__}}"',
        'site:{domain} intext:"${}"',
        'site:{domain} intext:"th:text"',
    ]),
    ('DevOps & Infrastructure', [
        'site:{domain} inurl:nagios',
        'site:{domain} inurl:zabbix',
        'site:{domain} inurl:prometheus',
        'site:{domain} inurl:grafana',
        'site:{domain} inurl:kibana',
        'site:{domain} inurl:splunk',
        'site:{domain} inurl:elasticsearch',
        'site:{domain} inurl:monitor',
        'site:{domain} inurl:jenkins',
        'site:{domain} inurl:travis',
        'site:{domain} inurl:circleci',
        'site:{domain} inurl:bamboo',
        'site:{domain} inurl:gitlab-ci',
        'site:{domain} inurl:drone',
        'site:{domain} intext:"pipeline"',
        'site:{domain} inurl:.git',
        'site:{domain} inurl:.git/HEAD',
        'site:{domain} inurl:.git/config',
        'site:{domain} intext:"Index of /.git"',
        'site:{domain} filetype:git',
        'site:{domain} inurl:kubernetes',
        'site:{domain} inurl:rancher',
        'site:{domain} inurl:docker',
        'site:{domain} inurl:swarm',
        'site:{domain} inurl:portainer',
        'site:{domain} inurl:sonarqube',
        'site:{domain} inurl:phabricator',
        'site:{domain} inurl:jira',
        'site:{domain} inurl:confluence',
    ]),
    ('Authentication Bypasses', [
        'site:{domain} inurl:debug=true',
        'site:{domain} inurl:test=true',
        'site:{domain} inurl:dev=true',
        'site:{domain} inurl:development=true',
        'site:{domain} inurl:bypass=true',
        'site:{domain} inurl:local=true',
        'site:{domain} inurl:staging=true',
        'site:{domain} inurl:backdoor',
        'site:{domain} inurl:auth=skip',
        'site:{domain} inurl:auth=false',
        'site:{domain} inurl:admin=true',
        'site:{domain} inurl:show_err=true',
        'site:{domain} inurl:debug_mode=true',
        'site:{domain} inurl:debug_level',
        'site:{domain} inurl:testing=true',
        'site:{domain} inurl:dev_mode=true',
        'site:{domain} inurl:access=all',
        'site:{domain} inurl:root=true',
        'site:{domain} inurl:demo_mode=true',
        'site:{domain} inurl:sample=true',
    ]),
    ('Open Redirects', [
        'site:{domain} inurl:redirect',
        'site:{domain} inurl:return',
        'site:{domain} inurl:r=http',
        'site:{domain} inurl:url=http',
        'site:{domain} inurl:next=http',
        'site:{domain} inurl:continue=http',
        'site:{domain} inurl:returnto=http',
        'site:{domain} inurl:goto=http',
        'site:{domain} inurl:link=http',
        'site:{domain} inurl:to=http',
        'site:{domain} inurl:out=http',
        'site:{domain} inurl:view=http',
        'site:{domain} inurl:location=http',
        'site:{domain} inurl:path=http',
        'site:{domain} inurl:uri=http',
    ]),
    ('Development & Hidden', [
        'site:{domain} inurl:beta',
        'site:{domain} inurl:hidden',
        'site:{domain} inurl:unreleased',
        'site:{domain} inurl:upcoming',
        'site:{domain} inurl:draft',
        'site:{domain} inurl:private',
        'site:{domain} inurl:preview',
        'site:{domain} inurl:testing',
        'site:{domain} inurl:dev',
        'site:{domain} inurl:develop',
        'site:{domain} inurl:development',
        'site:{domain} inurl:stage',
        'site:{domain} inurl:staging',
        'site:{domain} inurl:preprod',
        'site:{domain} inurl:prototype',
        'site:{domain} inurl:internal',
        'site:{domain} inurl:test',
        'site:{domain} inurl:debug',
        'site:{domain} inurl:local',
        'site:{domain} inurl:sandbox',
    ]),
    ('CMS & Framework', [
        'site:{domain} inurl:wp-admin',
        'site:{domain} inurl:wp-content',
        'site:{domain} inurl:wp-includes',
        'site:{domain} inurl:wp-json',
        'site:{domain} inurl:/wp-admin/admin-ajax.php',
        'site:{domain} intext:"Powered by" & intext:Drupal & inurl:user',
        'site:{domain} inurl:*/joomla/login',
        'site:{domain} inurl:administrator/index.php',
        'site:{domain} inurl:typo3',
        'site:{domain} inurl:magento',
        'site:{domain} inurl:admin/Cms_Wysiwyg/directive/',
        'site:{domain} inurl:shopify',
        'site:{domain} inurl:laravel',
        'site:{domain} inurl:symfony',
        'site:{domain} inurl:django',
        'site:{domain} inurl:flask',
        'site:{domain} inurl:rails',
        'site:{domain} inurl:spring',
        'site:{domain} inurl:struts',
        'site:{domain} inurl:node_modules',
        'site:{domain} inurl:package.json',
        'site:{domain} inurl:composer.json',
    ]),
    ('Security Misconfigurations', [
        'site:{domain} intext:"Content-Security-Policy"',
        'site:{domain} intext:"unsafe-inline"',
        'site:{domain} intext:"unsafe-eval"',
        'site:{domain} intext:"script-src \'self\'"',
        'site:{domain} intext:"style-src \'unsafe-inline\'"',
        'site:{domain} inurl:server-status',
        'site:{domain} inurl:status?full=true',
        'site:{domain} inurl:phpmyadmin',
        'site:{domain} inurl:adminer',
        'site:{domain} inurl:phpinfo',
        'site:{domain} inurl:info.php',
        'site:{domain} "You have an error in your SQL syntax"',
        'site:{domain} "Warning: mysql_connect()"',
        'site:{domain} "Fatal error:"',
        'site:{domain} "Exception in thread "main""',
        'site:{domain} intext:"syntax error at line"',
    ]),
    ('New & Advanced Dorks', [
        'site:{domain} inurl:api/graphql',
        'site:{domain} inurl:api/gql',
        'site:{domain} inurl:".well-known/security.txt"',
        'site:{domain} inurl:sourcemaps',
        'site:{domain} inurl:".map"',
        'site:{domain} inurl:swagger.json',
        'site:{domain} inurl:api-docs.json',
        'site:{domain} inurl:kubernetes.io/dockerconfigjson',
        'site:{domain} inurl:traefik',
        'site:{domain} inurl:terraform.tfstate',
        'site:{domain} inurl:".git/refs/heads"',
        'site:{domain} inurl:".env.local"',
        'site:{domain} intext:"Web.config file"',
        'site:{domain} inurl:composer.lock',
        'site:{domain} inurl:yarn.lock',
        'site:{domain} inurl:package-lock.json',
        'site:{domain} inurl:Pipfile.lock',
        'site:{domain} inurl:Gemfile.lock',
        'site:{domain} inurl:"/.netlify/"',
        'site:{domain} inurl:".vscode/"',
        'site:{domain} inurl:".idea/"',
        'site:{domain} inurl:"/.circleci/"',
        'site:{domain} inurl:"/.github/"',
    ]),
    ('Subdomain Takeover Probes', [
        'site:*.{domain} "this shop is currently unavailable"',
        'site:*.{domain} "The specified bucket does not exist"',
        'site:*.{domain} "NoSuchBucket"',
        'site:*.{domain} "You\'re Almost There!"',
        'site:*.{domain} "herokucdn.com/error-pages/no-such-app.html"',
        'site:*.{domain} "There isn\'t a GitHub Pages site here."',
        'site:*.{domain} "Sorry, this shop is currently unavailable."',
        'site:*.{domain} "Fastly error: unknown domain"',
        'site:*.{domain} "The page you are looking for does not exist."',
        'site:*.{domain} "If you\'re the owner of this website: Contact your hosting provider."',
        'site:*.{domain} "Repository not found"',
        'site:*.{domain} "Whatever you were looking for doesn\'t currently exist at this address."',
        'site:*.{domain} "Oops. We couldn\'t find that page."',
        'site:*.{domain} "This Amazon S3 bucket is not configured as a website."',
    ]),
    ('Exposed Tech Panels & Dashboards', [
        'site:{domain} intitle:"phpMyAdmin" inurl:phpmyadmin',
        'site:{domain} intitle:"Adminer" inurl:adminer.php',
        'site:{domain} intitle:"pgAdmin" inurl:pgadmin',
        'site:{domain} intitle:"RabbitMQ Management"',
        'site:{domain} intitle:"Flower" inurl:flower',
        'site:{domain} intitle:"Portainer" inurl:portainer',
        'site:{domain} intitle:"Rancher" inurl:rancher',
        'site:{domain} intitle:"Kubernetes Dashboard"',
        'site:{domain} intitle:"Jenkins" inurl:jenkins',
        'site:{domain} intitle:"GitLab" inurl:users/sign_in',
        'site:{domain} intitle:"Nexus Repository Manager"',
        'site:{domain} intitle:"Apache Tomcat"',
        'site:{domain} intitle:"JBoss Management Console"',
        'site:{domain} intitle:"Webmin" inurl:8000 OR inurl:10000',
        'site:{domain} intitle:"cPanel" inurl:2082 OR inurl:2083',
        'site:{domain} intitle:"Plesk" inurl:8443 OR inurl:8880',
    ]),
    ('Specific Vulnerability Footprints', [
        'site:{domain} intext:"Log4j" OR intext:"Log4Shell"',
        'site:{domain} inurl:cgi-bin intext:"Shellshock"',
        'site:{domain} intext:"Heartbleed test"',
        'site:{domain} filetype:swf intext:"Flash Player version"',
        'site:{domain} intext:"Apache Struts" intitle:"Welcome"',
        'site:{domain} intext:"Microsoft SharePoint" inurl:_layouts/',
        'site:{domain} intext:"BIG-IP" intitle:"BIG-IP F5"',
        'site:{domain} inurl:wp-content/plugins/revslider/',
        'site:{domain} inurl:Telerik.Web.UI.WebResource.axd',
        'site:{domain} intext:"vBulletin" inurl:showthread.php',
        'site:{domain} intext:"PHP Version" intitle:"phpinfo()"',
        'site:{domain} intext:"Pulse Connect Secure" intitle:"Login"',
        'site:{domain} intext:"Citrix Gateway" intitle:"Login"',
        'site:{domain} intext:"FortiGate" OR intext:"FortiClient" intitle:"Login"',
    ]),
]


def _normalise_domain(raw):
    """Reduce user input to a bare host by stripping any scheme and path,
    matching how the upstream generator treats the domain field."""
    domain = raw.strip()
    if '://' in domain:
        domain = domain.split('://', 1)[1]
    domain = domain.split('/', 1)[0].split('?', 1)[0].strip()
    return domain


def build_dorks(domain, categories=None):
    """Return [(category_name, [queries])] with {domain} substituted.

    ``categories`` is an optional list of indices into DORK_CATEGORIES; when
    omitted, every category is built.
    """
    selected = (DORK_CATEGORIES if categories is None
                else [DORK_CATEGORIES[i] for i in categories])
    built = []
    for name, templates in selected:
        queries = [tpl.replace('{domain}', domain) for tpl in templates]
        built.append((name, queries))
    return built


def search_url(query):
    """Ready-to-open Google search URL for a dork query."""
    return 'https://www.google.com/search?q=' + quote_plus(query)


def format_dorks(built, show_urls=False):
    """Render ``build_dorks`` output as text, grouped by category."""
    lines = []
    for name, queries in built:
        lines.append('')
        lines.append('# %s' % name)
        for query in queries:
            lines.append(query)
            if show_urls:
                lines.append('  %s' % search_url(query))
    return '\n'.join(lines).strip()


def run(input_func=input, out_dir=None, domain=None):
    """Interactive terminal flow: pick a domain and category, print the dorks,
    and optionally save them.  Returns an exit code (0 on success).

    ``domain`` may be supplied by the caller (e.g. a session target) to skip
    the domain prompt.
    """
    import os

    if not domain:
        domain = input_func('Target domain (e.g. example.com): ')
    domain = _normalise_domain(domain)
    if not domain:
        print('[error] No domain provided.')
        return 2

    print('\nCategories:')
    for i, (name, dorks) in enumerate(DORK_CATEGORIES, 1):
        print('  [%2d] %-34s (%d dorks)' % (i, name, len(dorks)))
    print('  [ 0] All categories')
    raw = input_func('Category [0]: ').strip() or '0'
    try:
        choice = int(raw)
        if choice < 0 or choice > len(DORK_CATEGORIES):
            raise ValueError
    except ValueError:
        print('[error] Invalid category: %r' % raw)
        return 2
    categories = None if choice == 0 else [choice - 1]

    show_urls = input_func('Show Google search URLs too? (y/N): ').strip().lower() == 'y'

    built = build_dorks(domain, categories)
    output = format_dorks(built, show_urls)
    print('\n' + output)

    total = sum(len(q) for _, q in built)
    print('\n[+] %d dork(s) generated for %s.' % (total, domain))

    if input_func('Save to a file? (y/N): ').strip().lower() == 'y':
        out_dir = out_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'output')
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, 'googledorks_%s.txt' % domain.replace('/', '_').replace(':', '_'))
        try:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(output + '\n')
        except OSError as exc:
            print('[error] Could not write %s: %s' % (path, exc))
            return 1
        print('[+] Saved to %s' % path)
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
