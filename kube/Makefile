# This script *requires* that you export NAMESPACE and ENV_VALUES

# These are acceptable values for those variables
#NAMESPACE=edp-infra-tools
#ENV_VALUES=./infra_values.yaml
# NAMESPACE=edp-staging
# ENV_VALUES=./staging_values.yaml
#NAMESPACE=edp-prod
#ENV_VALUES=./prod_values.yaml

deploy: check-env ## Deploy
	helm install . --name=edp-db-migration-api -f $(ENV_VALUES) --tiller-namespace $(NAMESPACE) --namespace $(NAMESPACE)

clean: check-env ## Remove all running instances
	helm delete edp-db-migration-api --purge --tiller-namespace $(NAMESPACE) &

help: ## Display help text.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

check-env:
ifndef NAMESPACE
  $(error env var NAMESPACE is undefined)
endif
ifndef ENV_VALUES
  $(error env var ENV_VALUES is undefined)
endif

.PHONY: all_containers deploy clean help check-env
.DEFAULT_GOAL := help
