deps:
	[ -d .venv ] || python3 -m venv .venv
	.venv/bin/pip3 install -r requirements.txt
	.venv/bin/pip3 install -r requirements-dev.txt
	cd static && npm ci

start:
	@. .venv/bin/activate && python app.py
