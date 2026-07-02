.PHONY: help install pdf docx build clean structure

UV ?= uv
PYTHON ?= $(UV) run python
DOC_TITLE ?= Documento generado desde Markdown
DOC_FOOTER ?= Documento de trabajo
DOC_NAME ?= documento
PARTS ?= partes
DIST ?= dist

help:
	@echo "Targets:"
	@echo "  make install    Install Python dependencies"
	@echo "  make pdf        Generate dist/$(DOC_NAME).pdf"
	@echo "  make docx       Generate dist/$(DOC_NAME).docx"
	@echo "  make build      Generate PDF and DOCX"
	@echo "  make clean      Remove generated files"
	@echo "  make structure  Show expected Markdown/assets structure"

install:
	$(UV) sync

pdf:
	$(PYTHON) tools/md_to_pdf_cli.py "$(PARTS)" "$(DIST)/$(DOC_NAME).pdf" --title "$(DOC_TITLE)" --footer "$(DOC_FOOTER)"

docx:
	$(PYTHON) tools/md_to_docx_cli.py "$(PARTS)" "$(DIST)/$(DOC_NAME).docx"

build: pdf docx

clean:
	$(PYTHON) -c "import shutil; shutil.rmtree('$(DIST)', ignore_errors=True)"

structure:
	$(PYTHON) tools/md_to_pdf_cli.py --print-structure
