
# SERVER

The python package installs 2 scripts:
* db-migrate        - `The normal running mode that runs migrations`
* db-migrate-server - `A new command that runs an API service to run migrations for you`

The rest of this documentation is for the `db-migrate-server` command.


## Configuration

Must add configuration through environment variables.

* AUTH_METHOD - Options: [`secret`]
  * `secret`
    * AUTH_TOKEN - a shared secret that will authorize any request
* SECRET_STORE - Options: [`file`, `vault`]
  * `file`
    * STORAGE_ROOT - the directory to write secrets to
    * ENCRYPTION_KEY - an 8 character secret code
  * `vault`
    * VAULT_ADDR - e.g. http://vaul.address:8200
    * EDP_RO_PASSWORD - The password used to access vault secrets
* PORT - defaults to 8080
