# Helm deployments

Configure your kubectl connection, then do something like:
```
# Install
helm install --tiller-namespace edp-dev --namespace edp-dev --name edp-db-migration . -f staging_values.yaml

# Delete
helm delete --tiller-namespace edp-dev edp-db-migration --purge
```
