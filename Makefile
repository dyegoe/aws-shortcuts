.ONESHELL :

CURRENT_DIR := $(shell pwd)
CONTAINER_NAME := "aws-shortcuts"
CONTAINER_IMAGE := "aws-shortcuts:0.2"
CONTAINER_APP_DIR := "/aws-shortcuts"
AWS_CONFIG_DIR := $(HOME)/.aws

# DOCKER TASKS
.PHONY : build
build: ## Build the container
	@echo Building $(CONTAINER_IMAGE)
	@docker build -t $(CONTAINER_IMAGE) .

.PHONY : run
run: ## Runs the container
	@echo Running $(CONTAINER_IMAGE)
	@docker run --rm \
		-v $(AWS_CONFIG_DIR):/root/.aws:ro \
		-v $(CURRENT_DIR):$(CONTAINER_APP_DIR) \
		-v $(SSH_PRIVATE_KEY):/root/.ssh/id_rsa \
		-w $(CONTAINER_APP_DIR) \
		--name $(CONTAINER_NAME) \
		-it $(CONTAINER_IMAGE) sh

.PHONY : stop
stop: ## Stops the container
	@echo Stopping $(CONTAINER_IMAGE)
	@docker stop $(CONTAINER_NAME)

.PHONY : rm
rm: ## Removes the container
	@echo Removing $(CONTAINER_IMAGE)
	@docker rm -f $(CONTAINER_NAME)
