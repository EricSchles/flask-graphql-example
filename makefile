default: format test

test:
	@nosetests --with-coverage --cover-package quick --with-doctest --rednose --nocapture


watch:
	@nosetests --rednose --with-watch


clean:
	@find . -name '*.pyc' -delete
	@find . -name '__pycache__' -type d -exec rm -fr {} \;
	@rm -rf dist
	@rm -f .coverage
	@rm -rf htmlcov
	@rm -rf build

format:
	@echo "Formating:"
	@yapf  -dr ./
	@yapf  -ir ./
