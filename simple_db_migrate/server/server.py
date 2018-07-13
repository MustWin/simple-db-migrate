from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from subprocess import Popen, PIPE
import os
import urlparse
import random
import requests
from requests.auth import HTTPDigestAuth
import string
import json
import traceback
import shutil
import re
from .auth import SecretTokenAuth
from .secret_store import FileSecretStore, VaultSecretStore

#################      SERVER FRAMEWORK       #################

class http_server:
    def __init__(self, auth, store):

        def handler(*args):
            myHandler(router({
                "GET": {
                    "^/$": lambda handler: healthCheck(handler),
                    # /config/tmag/qlab06
                    "^/config/\w+/\w+$": lambda handler: authorized(handler, auth) and getConfig(handler, auth, store),
                },
                "POST": {
                    # Update to the latest version: /migrate/tmag/qlab06?artifactory_db_url=https://blah.com/t-mobile/app/v0.1.2/db
                    # Update or rollback to a specific version: /migrate/tmag/qlab06?version=20170703144937&artifactory_db_url=https://blah.com/t-mobile/app/v0.1.2/db
                    "^/migrate/\w+/\w+": lambda handler: authorized(handler, auth) and runMigrations(handler, auth, store),
                    "^/secret/\w+/\w+": lambda handler: authorized(handler, auth) and saveSecret(handler, auth, store),
                }
            }), auth, store, *args)
        print "Listening..."
        server = HTTPServer(('', os.environ.get("PORT", 8080)), handler)
        server.serve_forever()

# Super simple dumb regex router
class router:
    # routes is a dict like:
    """
    {
        "GET": {
            "\w+/\w+": func(handler)
        },
        "POST": {
            "\w+/\w+": func(handler)
        },

    }
    """
    def __init__(self, routes):
        self.routes = routes

    def route(self, method, path, handler):
        opts = self.routes[method]
        for opt in opts:
            pattern = re.compile(opt)
            if pattern.search(path) != None:
                opts[opt](handler)
                return
        respond(handler, 404, "text/html", "No matching route")


#################      HELPER FUNCTIONS      #################
def authorized(handler, auth):
    try:
        if not auth.is_authorized(handler):
            respond(handler, 401, "text/plain", "Unauthorized")
            return False
        return True
    except KeyError as e:
        print "Missing required parameters: %s" % e
        respond(handler, 400, 'text/plain', "Missing required parameters: %s" % e)
        return False

def fetch_artifacts(artifactory_dir_url):
    migrations = {}
    r = requests.get(artifactory_dir_url, verify=False, auth=HTTPDigestAuth('mihbe1', 'AKCp5aU5mc6UkxcLw7zK5eUhpj94WZv7pV8KBggePUHqCXhD1mctdKUo5GSAd7pggoUmcff4j'))
    if r.status_code < 200 or r.status_code > 299:
        raise Exception("Fetching artifacts failed %s: %s" % (r.status_code, r.text))
    for f in r.json()["children"]:
        print f
        fetch_req = requests.get(artifactory_dir_url.replace('api/storage/', '') + f['uri'], verify=False, auth=HTTPDigestAuth('mihbe1', 'AKCp5aU5mc6UkxcLw7zK5eUhpj94WZv7pV8KBggePUHqCXhD1mctdKUo5GSAd7pggoUmcff4j'))
        migrations[f['uri'][1:]] = fetch_req.text
    print migrations
    return migrations

def validate_config(config):
    try:
        config["oracle_host"]
        config["oracle_port"]
        config["oracle_service_name"]
        config["oracle_admin_username"]
        config["oracle_admin_password"]
        return None
    except KeyError as e:
        return "Config is missing required parameters: %s" % e

def respond(handler, code, contentType, body):
    handler.send_response(code)
    handler.send_header('Content-type', contentType)
    handler.end_headers()
    handler.wfile.write(body)
    return

#################      ROUTE FUNCTIONS       #################

def healthCheck(handler):
    respond(handler, 200, "text/html", "Healthcheck: OK")

def getConfig(handler, auth, store):
    _, app, env = handler.path.split('?')[0][1:].split('/')
    parsed = urlparse.urlparse(handler.path)
    params = urlparse.parse_qs(parsed.query)

    try:
        config = json.loads(store.fetch("%s/%s" % (app, env)))
        msg = validate_config(config)
        if msg is not None:
            print "Config is missing required parameters: %s" % msg
            respond(handler, 400, "text/html", "Missing required parameters: %s" % msg)
            return
        respond(handler, 200, "text/html", "Configuration valid for %s/%s\n" % (app, env))
    except Exception as e:
        respond(handler, 503, "text/html", "Error: %s\n%s" % (e, traceback.format_exc()))

def saveSecret(handler, auth, store):
    _, app, env = handler.path.split('?')[0][1:].split('/')

    try:
        content_len = int(handler.headers.getheader('content-length', 0))
        config = json.loads(handler.rfile.read(content_len))
        msg = validate_config(config)
        if msg is not None:
            print "Config is missing required parameters: %s" % msg
            respond(handler, 400, "text/html", "Missing required parameters: %s" % msg)
            return
        config = store.save("%s/%s" % (app, env), json.dumps(config))
        respond(handler, 200, "text/html", "Saved secret for %s/%s\n" % (app, env))
    except Exception as e:
        respond(handler, 503, "text/html", "Error: %s\n%s" % (e, traceback.format_exc()))

def runMigrations(handler, auth, store):
    try:
        app, env = handler.path.split('?')[0].replace('/migrate/', '').split('/')
        parsed = urlparse.urlparse(handler.path)
        params = urlparse.parse_qs(parsed.query)

        # Fetch application config
        config = json.loads(store.fetch("%s/%s" % (app, env)))
        msg = validate_config(config)
        if msg is not None:
            print "Config is missing required parameters: %s" % e
            respond(handler, 400, "text/html", "Missing required parameters: %s" % msg)
            return

        directory = "/tmp/" + ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))

        dirs = ['config', 'ddl', 'files']
        for dir in dirs:
            os.makedirs(directory + '/' + dir)

            # Download migrations from artifactory
            files = {}
            try:
                files = fetch_artifacts(params["artifactory_db_url"][0] + '/' + dir)
                for name, text in files.iteritems():
                    with open('%s/%s/%s' % (directory, dir, name), "w") as file:
                        file.write(text)
            except Exception as e:
                if dir != 'ddl' and str(e).find('404') > -1:
                    print "No files found for %s" % dir
                    continue
                print e
                respond(handler, 400, 'text/html', "Error while copying files from Artifactory: %s\n%s" % (e, traceback.format_exc()))
                return

        # Run Migrations

        try:
            cmd = ['db-migrate',
                        '--db-host=%s' % config["oracle_host"],
                        '--db-user=%s' % config["oracle_admin_username"],
                        '--db-password=%s' % config["oracle_admin_password"],
                        '--db-name=%s' % config["oracle_service_name"],
                        '--db-migrations-dir=%s' % directory + '/ddl',
                        '--db-engine=oracle',
                        '--db-engine-use-cli=True',
                        '--db-port=%s' % config["oracle_port"],
                        '--log-dir=/tmp/db-migrate' ,
                        '--log-level=2' ,
                        '--show-sql' ,
                        '--db-migrations-dir=%s' % directory + '/ddl',
                        ]
            sql_prefix_file = directory + ('/config/%s.sql' % env)
            if os.path.isfile(sql_prefix_file):
                cmd.append('--sql-prefix-file=%s' % sql_prefix_file)
            if "version" in params:
                cmd.append('--migration=%s' % params["version"][0])
            p = Popen(cmd , cwd=directory, stdin=PIPE, stdout=PIPE, stderr=PIPE,env=os.environ)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print "Error running migrations %s:\n%s" % (cmd, "STDOUT:\n" + stdout + "\n\nSTDERR:\n" + stderr)
                respond(handler, 400, 'text/plain', "Error running migrations %s:\n%s" % (cmd, "STDOUT:\n" + stdout + "\n\nSTDERR:\n" + stderr))
                return

            # Respond with 200 OK
            respond(handler, 200, "text/plain", "STDOUT:\n" + stdout + "\nSTDERR:\n\n" + stderr)
            return

        except KeyError as e:
            print "Missing required parameters: %s" % e
            respond(handler, 400, 'text/plain', "Missing required parameters: %s" % e)
            return

    except Exception as e:
        respond(handler, 503, 'text/plain', "Internal Server Error: %s\n%s" % (e, traceback.format_exc()))
        return
    finally:
        # Cleanup
        # shutil.rmtree(directory)
        1+1


class myHandler(BaseHTTPRequestHandler):
    def __init__(self, router, auth, store, *args):
        self.router = router
        self.auth = auth
        self.store = store
        BaseHTTPRequestHandler.__init__(self, *args)

    def do_GET(self):
        self.router.route("GET", self.path, self)

    def do_POST(self):
        self.router.route("POST", self.path, self)


class Server:
    def __init__(self):
        try:
            auth = {
                "secret": lambda env: SecretTokenAuth(env["AUTH_TOKEN"]),
            }[os.environ["AUTH_METHOD"]](os.environ)

            store = {
                "file": lambda env: FileSecretStore(env["STORAGE_ROOT"], env["ENCRYPTION_KEY"]),
                "vault": lambda env: VaultSecretStore(
                                env["VAULT_ADDR"], # E.g. http://vault.address:8200
                                env["EDP_RO_PASSWORD"])
            }[os.environ["SECRET_STORE"]](os.environ)
        except KeyError as e:
            raise Exception("Missing required environment variable: %s" % e)

        self.server = http_server(auth, store)
