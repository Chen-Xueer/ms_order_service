
# Code quality control

black -l 79 -t py310 .
flake8 . --exclude=./venv,./alembic --extend-ignore=F401