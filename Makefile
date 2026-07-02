.PHONY: help install package-build pdf docx build clean structure

UV ?= uv
MD2DOC ?= $(UV) run md2doc
DOC_TITLE ?= Document generated from Markdown
DOC_FOOTER ?= Working document
DOC_NAME ?= document

help:
	@echo "Targets:"
	@echo "  make install    Install project dependencies"
	@echo "  make package-build  Build wheel and source distribution"
	@echo "  make pdf        Generate dist/$(DOC_NAME).pdf"
	@echo "  make docx       Generate dist/$(DOC_NAME).docx"
	@echo "  make build      Generate PDF and DOCX"
	@echo "  make clean      Remove generated files"
	@echo "  make structure  Show expected Markdown/assets structure"

install:
	$(UV) sync

package-build:
	$(UV) build

pdf:
	$(MD2DOC) build . --format pdf --name "$(DOC_NAME)" --title "$(DOC_TITLE)" --footer "$(DOC_FOOTER)"

docx:
	$(MD2DOC) build . --format docx --name "$(DOC_NAME)"

build: pdf docx

clean:
	$(UV) run python -c "import shutil; shutil.rmtree('dist', ignore_errors=True); shutil.rmtree('build', ignore_errors=True)"

structure:
	$(MD2DOC) structure
