all:
	docker build -t purgeomatic .

venv:
	python -m venv .venv

.PHONY: venv
