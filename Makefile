venv: poetry.lock
	python3.11 -m venv ./venv
	. venv/bin/activate && pip install poetry && poetry install

.PHONY: frontend
frontend:
	npm --prefix frontend/ ci
	npm --prefix frontend/ run build

.PHONY: test
test: venv
	venv/bin/mypy secretary/
	touch venv

.PHONY: clean
clean:
	rm -fr venv
