.ONESHELL :

CURRENT_DIR := $(shell pwd)
CONTAINER_NAME := "aws-shortcuts"
CONTAINER_IMAGE := "aws-shortcuts:0.2"
CONTAINER_APP_DIR := "/aws-shortcuts"
AWS_CONFIG_DIR := $(HOME)/.aws

# DOCKER TASKS
.PHONY : docker-build
docker-build: ## Build the container
	@echo Building $(CONTAINER_IMAGE)
	@docker build -t $(CONTAINER_IMAGE) .

.PHONY : docker-run
docker-run: ## Runs the container
	@echo Running $(CONTAINER_IMAGE)
	@docker run --rm \
		-v $(AWS_CONFIG_DIR):/root/.aws:ro \
		-v $(CURRENT_DIR):$(CONTAINER_APP_DIR) \
		-v $(SSH_PRIVATE_KEY):/root/.ssh/id_rsa \
		-w $(CONTAINER_APP_DIR) \
		--name $(CONTAINER_NAME) \
		-it $(CONTAINER_IMAGE) sh

.PHONY : docker-stop
docker-stop: ## Stops the container
	@echo Stopping $(CONTAINER_IMAGE)
	@docker stop $(CONTAINER_NAME)

.PHONY : docker-rm
docker-rm: ## Removes the container
	@echo Removing $(CONTAINER_IMAGE)
	@docker rm -f $(CONTAINER_NAME)

.PHONY : docker-rmi
docker-rmi: ## Removes the image
	@echo Removing $(CONTAINER_IMAGE)
	@docker rmi $(CONTAINER_IMAGE)

# SCRIPT TASKS
.PHONY : build
build: ## Installs pip3 requirements
	@echo Installing requirements
	@/usr/bin/env python3 -m pip install -r requirements.txt

.PHONY : install
install: ## Installs aws-shortcuts
	@echo Installing aws-shortcuts
	@mkdir -p $(HOME)/.local/bin
	@cp $(CURRENT_DIR)/aws-shortcuts.py $(HOME)/.local/bin/aws-shortcuts
	@chmod +x $(HOME)/.local/bin/aws-shortcuts
