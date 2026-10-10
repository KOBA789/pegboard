HOOKS := $(wildcard hooks/*/build.py)

.PHONY: all test lint $(HOOKS)

# Regenerate every hook's STEP / STL into hooks/<name>/output/
all: $(HOOKS)

$(HOOKS):
	uv run $@

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .
