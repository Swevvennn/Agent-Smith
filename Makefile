VENV := /tmp/venv

install: clean
	python3 -m venv $(VENV)
	ln -s $(VENV) .venv
	$(VENV)/bin/pip install uv
	UV_CACHE_DIR=/tmp/uv-cache \
	$(VENV)/bin/uv sync
	@echo "Finished !!!"

clean:
	rm -rf .venv /tmp/venv /tmp/uv-cache
	@echo "Tout propre le PC !!!"
