import os
import errno
import string
import random
import base64
from Crypto.Cipher import AES

BLOCK_SIZE=16

class SecretStore:
    def save(self, path, value):
        raise NotImplementedError( "Not implemented" )

    def fetch(self, path, value):
        raise NotImplementedError( "Not implemented" )


BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[:-ord(s[len(s)-1:])]

class AESCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, raw):
        raw = pad(raw)
        iv = os.urandom(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.urlsafe_b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.urlsafe_b64decode(enc.encode('utf-8'))
        iv = enc[:BS]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc[BS:]))

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def randomString(len):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(len))

class FileSecretStore(SecretStore):
    def __init__(self, storageRoot, symmetricKey):
        mkdir(storageRoot)
        if len(symmetricKey) != 8:
            raise Exception("SymmetricKey must be 8 chars")
        self.symmetricKey = symmetricKey
        self.storageRoot = storageRoot

    def save(self, path, value):
        salt = randomString(8)
        mkdir(os.path.join(self.storageRoot, path))
        with open(os.path.join(self.storageRoot, path, "salt"), "w") as f:
            f.write(salt)
        cipher = AESCipher(self.symmetricKey + salt)
        secret = cipher.encrypt(value)
        with open(os.path.join(self.storageRoot, path, "secret"), "w") as f:
            f.write(secret)

    def fetch(self, path):
        with open(os.path.join(self.storageRoot, path, "salt"), "r") as fSalt:
            salt = fSalt.read()
            cipher = AESCipher(self.symmetricKey + salt)
            with open(os.path.join(self.storageRoot, path, "secret"), "r") as fSecret:
                return cipher.decrypt(fSecret.read())


class VaultSecretStore(SecretStore):
    def __init__(self, VAULT_ADDR, EDP_RO_PASSWORD):
        self.VAULT_ADDR = VAULT_ADDR
        self.EDP_RO_PASSWORD = EDP_RO_PASSWORD
        pass

    def save(self, path, value):
        pass

    # path should be app/env
    def fetch(self, path):
        print "POST " + self.VAULT_ADDR + '/v1/auth/userpass/login/edp-ro'
        r = requests.post(self.VAULT_ADDR + '/v1/auth/userpass/login/edp-ro', data=json.dumps({"password": self.EDP_RO_PASSWORD}))
        print r.json()
        auth_token = r.json()['auth']['client_token']

        # Based on usage of this service https://bitbucket.service.edp.t-mobile.com/projects/EDPPUBLIC/repos/vault-config-manager/browse
        print "GET " + self.VAULT_ADDR + '/v1/secret/edp/edp-%s/config' % (path)
        r = requests.get(self.VAULT_ADDR + '/v1/secret/edp/edp-%s/config' % (path),
            headers={"X-Vault-Token": auth_token})
        if r.status_code < 200 or r.status_code > 299:
            raise Exception("Fetching configuration failed: %s\n%s" % (r.status_code, r.text))
        return r.json()['data']
        pass
