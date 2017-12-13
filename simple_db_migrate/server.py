from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from subprocess import Popen, PIPE
import os
import urlparse
import random
import requests
from .main import Main
from requests.auth import HTTPDigestAuth
import string
import json
import traceback
import shutil

class test:
    def show(self):
        return "aaaa"

class http_server:
    def __init__(self, t1):
        # These will throw exceptions if not set
        try:
            os.environ["VAULT_ADDR"] # E.g. http://vault.address:8200
            os.environ["EDP_RO_PASSWORD"]
        except KeyError as e:
            raise Exception("Missing required environment variable: %s" % e)

        def handler(*args):
            myHandler(t1, *args)
        print "Listening..."
        server = HTTPServer(('', os.environ.get("PORT", 8080)), handler)
        server.serve_forever()

class myHandler(BaseHTTPRequestHandler):
    def __init__(self, t1, *args):
        self.t1 = t1
        self.VAULT_ADDR = os.environ["VAULT_ADDR"]
        self.EDP_RO_PASSWORD = os.environ["EDP_RO_PASSWORD"]
        BaseHTTPRequestHandler.__init__(self, *args)

    def fetch_artifacts(self, artifactory_dir_url):
        migrations = {}
        r = requests.get(artifactory_dir_url, verify=False, auth=HTTPDigestAuth('mihbe1', 'API_KEY_TODO'))
        if r.status_code < 200 or r.status_code > 299:
            raise Exception("Fetching artifacts failed %s: %s" % (r.status_code, r.text))
        for f in r.json()["children"]:
            print f
            fetch_req = requests.get(artifactory_dir_url.replace('api/storage/', '') + f['uri'], verify=False, auth=HTTPDigestAuth('mihbe1', 'API_KEY_TODO'))
            migrations[f['uri'][1:]] = fetch_req.text
        print migrations
        return migrations

    def fetch_config(self, app, env):
        print "POST " + self.VAULT_ADDR + '/v1/auth/userpass/login/edp-ro'
        r = requests.post(self.VAULT_ADDR + '/v1/auth/userpass/login/edp-ro', data=json.dumps({"password": self.EDP_RO_PASSWORD}))
        print r.json()
        auth_token = r.json()['auth']['client_token']

        # Based on usage of this service https://bitbucket.service.edp.t-mobile.com/projects/EDPPUBLIC/repos/vault-config-manager/browse
        print "GET " + self.VAULT_ADDR + '/v1/secret/edp/edp-%s/%s/config' % (app, env)
        r = requests.get(self.VAULT_ADDR + '/v1/secret/edp/edp-%s/%s/config' % (app, env),
            headers={"X-Vault-Token": auth_token})
        if r.status_code < 200 or r.status_code > 299:
            raise Exception("Fetching configuration failed: %s\n%s" % (r.status_code, r.text))
        return r.json()['data']

    def validate_config(self, config):
        try:
            config["oracle_host"]
            config["oracle_port"]
            config["oracle_service_name"]
            config["vaulted_oracle_admin_username"]
            config["vaulted_oracle_admin_password"]
            return None
        except KeyError as e:
            return "Config is missing required parameters: %s" % e

    # /tmag/qlab06?artifactory_db_url=https://artifactory.service.edp.t-mobile.com/artifactory/api/storage/tmo-releases/com/tmobile/tmag/4.23_PerfTest.31/db
    def do_GET(self):
        print self.command
        print self.path
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write("Healthcheck: OK")
            return
        app, env = self.path.split('?')[0][1:].split('/')
        parsed = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(parsed.query)

        try:
            config = self.fetch_config(app, env)
            msg = self.validate_config(config)
            if msg is not None:
                print "Config is missing required parameters: %s" % msg
                self.send_response(400)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write("Missing required parameters: %s" % msg)
                return
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write("Configuration valid for %s/%s\n" % (app, env))
        except Exception as e:
            self.send_response(503)
            self.end_headers()
            self.wfile.write("Error: %s\n%s" % (e, traceback.format_exc()))

    # /tmag/qlab06?artifactory_db_url=https://blah.com/t-mobile/app/v0.1.2/db
    def do_POST(self):
        try:
            print self.command
            print self.path
            app, env = self.path.split('?')[0][1:].split('/')
            parsed = urlparse.urlparse(self.path)
            params = urlparse.parse_qs(parsed.query)

            # Fetch application config
            config = self.fetch_config(app, env)
            msg = self.validate_config(config)
            if msg is not None:
                print "Config is missing required parameters: %s" % e
                self.send_response(400)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write("Config is missing required parameters: %s" % e)
                return

            directory = "/tmp/" + ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))

            dirs = ['config', 'ddl', 'files']
            for dir in dirs:
                os.makedirs(directory + '/' + dir)

                # Download migrations from artifactory
                files = {}
                try:
                    files = self.fetch_artifacts(params["artifactory_db_url"][0] + '/' + dir)
                    for name, text in files.iteritems():
                        with open('%s/%s/%s' % (directory, dir, name), "w") as file:
                            file.write(text)
                except Exception as e:
                    if dir != 'ddl' and str(e).find('404') > -1:
                        print "No files found for %s" % dir
                        continue
                    print e
                    self.send_response(400)
                    self.send_header('Content-type','text/html')
                    self.end_headers()
                    self.wfile.write("Error while copying files from Artifactory: %s\n%s" % (e, traceback.format_exc()))
                    return

            # Run Migrations

            try:
                cmd = ['db-migrate',
                            '--db-host=%s' % config["oracle_host"],
                            '--db-user=%s' % config["vaulted_oracle_admin_username"],
                            '--db-password=%s' % config["vaulted_oracle_admin_password"],
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
                p = Popen(cmd , cwd=directory, stdin=PIPE, stdout=PIPE, stderr=PIPE,env=os.environ)
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    print "Error running migrations: %s" % e
                    self.send_response(400)
                    self.send_header('Content-type','text/html')
                    self.end_headers()
                    self.wfile.write("Error running migrations:\n%s" % ("STDOUT:\n" + stdout + "\n\nSTDERR:\n" + stderr))
                    return

                # Respond with 200 OK
                self.send_response(200)
                self.end_headers()
                self.wfile.write(stdout)
                return

            except KeyError as e:
                print "Missing required parameters: %s" % e
                self.send_response(400)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write("Missing required parameters: %s" % e)
                return

        except Exception as e:
            self.send_response(503)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write("Internal Server Error: %s\n%s" % (e, traceback.format_exc()))
            return
        finally:
            # Cleanup
            # shutil.rmtree(directory)
            1+1


class Server:
    def __init__(self):
        self.t1 = test()

        self.server = http_server(self.t1)
