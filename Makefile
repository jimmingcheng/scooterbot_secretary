venv: poetry.lock
	virtualenv --python=python3.8 venv
	. venv/bin/activate && pip install poetry && poetry install

.PHONY: test
test: venv
	venv/bin/mypy secretary/
	venv/bin/pytest tests/
	touch venv

.PHONY: clean
clean:
	rm -fr venv
