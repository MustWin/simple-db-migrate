


class Auth:
    def is_authorized(self, handler):
        raise NotImplementedError( "Not implemented" )

# class LDAPAuth(Auth):
#     # TODO: Fill this in with ldap credential information
#     def __init__():
#         self.
#
#     def is_authorized(credential):
#         raise NotImplementedError( "Should have implemented this" )
#         if token == credential:
#             return true
#         return false


class SecretTokenAuth(Auth):
    def __init__(self, token):
        self.token = token

    def is_authorized(self, handler):
        if self.token == handler.headers["Authorization"]:
            return True
        return False
