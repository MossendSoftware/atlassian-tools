PACKAGE := atlassian-tools
INSTALL_DIR := $(shell uv tool dir)/../bin

.PHONY: install uninstall dev

install:
	uv tool install . --force --no-cache
	@echo "bb, jira, and cfl installed to $(INSTALL_DIR)"
	@echo "Ensure $(INSTALL_DIR) is in your PATH (run: uv tool update-shell)"

uninstall:
	uv tool uninstall $(PACKAGE)

dev:
	uv sync --group dev
