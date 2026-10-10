# Each hooks/<name>/ is a package whose build.py writes its STEP / STL into hooks/<name>/output/
HOOKS := $(patsubst %/build.py,%,$(wildcard hooks/*/build.py))

.PHONY: all test lint $(HOOKS)

all: $(HOOKS)

$(HOOKS):
	uv run python -m $(subst /,.,$@).build

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .
