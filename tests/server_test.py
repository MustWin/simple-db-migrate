import string
import random
import unittest
from simple_db_migrate.server.secret_store import FileSecretStore
from simple_db_migrate.server.server import router

class ServerTest(unittest.TestCase):

    def test_file_secret_store_saves_and_fetches(self):
        store = FileSecretStore("/tmp/secret_store/", ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)))
        secretVal = "testsecret"
        store.save("domain1", secretVal)
        foundVal = store.fetch("domain1")
        self.assertEqual(secretVal, foundVal)

    def test_router_routes(self):
        def ab():
            ab.has_been_called = True
            pass
        ab.has_been_called = False

        def regex():
            regex.has_been_called = True
            pass
        regex.has_been_called = False

        r = router({
            "GET": {
                "a/b": lambda handler: ab()
            },
            "POST": {
                "\w+/\w+": lambda handler: regex()
            }
        })
        r.route("GET", "a/b", None)
        r.route("POST", "foo/bar", None)
        self.assertEqual(ab.has_been_called, True)
        self.assertEqual(regex.has_been_called, True)

        # This works, and we should write a test for it.
        # r.route("POST", "nonexistant", None)
