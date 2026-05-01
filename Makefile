.PHONY: help build test run-headless run-game install-python clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk \
	'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Rust
build-sim: ## Build all Rust crates (debug)
	cargo build

build-sim-release: ## Build all Rust crates (release/optimized)
	cargo build --release

test-sim: ## Run all Rust tests
	cargo test

run-headless: ## Run sim headless for N ticks (usage: make run-headless TICKS=1000)
	cargo run -p cli -- --ticks $(TICKS)

# Python
install-python: ## Install Python package in development mode
	pip install -e models/[dev]

test-python: ## Run Python model tests
	pytest models/

# Combined
run-game: ## Build sim + launch Godot (requires Godot in PATH)
	cargo build && godot --path game/

# Maintenance
clean: ## Remove build artifacts
	cargo clean
	find models -name "*.pyc" -delete
	find models -name "__pycache__" -delete
