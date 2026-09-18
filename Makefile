# Build the SIAM 50-digit challenge write-up (digit50.pdf).
#
# Nothing in the paper is typed by hand: code/paper.py computes every number
# and writes figs/*.pdf, tables/*.tex and snippets/*.tex, which digit50.tex
# \input{}s.  So the PDF depends on the Python, not just on the LaTeX.
#
# The document is plain pdfLaTeX with an inline thebibliography, so no BibTeX
# run is needed -- only enough passes for \ref and \cite to settle.

MAIN     := digit50
TEX      := pdflatex
TEXFLAGS := -interaction=nonstopmode -halt-on-error -file-line-error
MAX_RUNS := 5

# One script regenerates all three asset directories in a single run, so a
# stamp file stands in for its outputs.
GEN   := code/paper.py
STAMP := .assets.stamp
CODE  := $(wildcard code/*.py)

# Intermediate files pdfLaTeX leaves behind.
JUNK := $(addprefix $(MAIN).,aux log out toc lof lot bbl blg fls synctex.gz)

# The arXiv submission: the sources arXiv compiles, staged and zipped.
ARXIV    := $(MAIN)-arxiv.zip
ARXIVDIR := .arxiv

.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.PHONY: compile assets arxiv check clean help view warnings

compile: $(MAIN).pdf  ## Build the PDF

$(MAIN).pdf: $(MAIN).tex $(STAMP)
	@pass=1; \
	while :; do \
	  echo "==> $(TEX) $(MAIN).tex (pass $$pass)"; \
	  $(TEX) $(TEXFLAGS) $(MAIN).tex >/dev/null || { \
	    echo "--- last 40 lines of $(MAIN).log ---" >&2; \
	    tail -n 40 $(MAIN).log >&2; \
	    exit 1; \
	  }; \
	  pass=$$((pass + 1)); \
	  [ $$pass -le $(MAX_RUNS) ] || break; \
	  grep -qE 'Rerun to get|Label\(s\) may have changed' $(MAIN).log || break; \
	done

assets: $(STAMP)  ## Recompute figures, tables and listings from code/

$(STAMP): $(CODE)
	@command -v uv >/dev/null || { echo "error: uv not found (see astral.sh/uv)" >&2; exit 1; }
	uv run $(GEN)
	@touch $@

check:  ## Report inputs referenced by the source but missing on disk
	@missing=0; \
	for f in $$(grep -oE '\{(figs|tables|snippets)/[A-Za-z0-9._-]+\}' $(MAIN).tex \
	            | tr -d '{}' | sort -u); do \
	  case $$f in \
	    figs/*) [ -f "$$f.pdf" ] || [ -f "$$f" ] || { echo "missing: $$f.pdf"; missing=1; };; \
	    *)      [ -f "$$f.tex" ] || [ -f "$$f" ] || { echo "missing: $$f.tex"; missing=1; };; \
	  esac; \
	done; \
	[ $$missing -eq 0 ] || { echo "error: inputs above are referenced by $(MAIN).tex but absent; run 'make assets'" >&2; exit 1; }

arxiv: $(ARXIV)  ## Pack the LaTeX source into a zip for arXiv

# arXiv runs LaTeX itself, so the archive carries the source and the generated
# inputs -- figures, tables and listings -- but no Python and no Makefile: it
# has to build with nothing installed but TeX.  The document is plain article
# loading only amsmath, amssymb and graphicx, so no class file goes in, and
# the bibliography is inline, so there is no .bbl either.  Built from
# $(MAIN).pdf so that nothing is uploaded that has not just compiled here.
$(ARXIV): $(MAIN).pdf
	@command -v zip >/dev/null || { echo "error: zip not found" >&2; exit 1; }
	@$(MAKE) --no-print-directory check
	@rm -rf $(ARXIVDIR) $@
	@mkdir -p $(ARXIVDIR)
	@cp $(MAIN).tex $(ARXIVDIR)/
	@for d in figs tables snippets; do \
	  [ -d $$d ] || continue; \
	  mkdir -p $(ARXIVDIR)/$$d; \
	  cp $$d/* $(ARXIVDIR)/$$d/; \
	done
	@echo "==> $@"
	@cd $(ARXIVDIR) && zip -rX ../$@ . | sed -E 's/^ *adding: /  /'
	@rm -rf $(ARXIVDIR)

warnings: $(MAIN).pdf  ## Show over/underfull boxes and LaTeX warnings from the last build
	@grep -nE 'Warning|Overfull|Underfull' $(MAIN).log || echo "no warnings"

view: $(MAIN).pdf  ## Open the built PDF
	@(command -v open >/dev/null && open $(MAIN).pdf) || xdg-open $(MAIN).pdf

clean:  ## Remove LaTeX intermediates, keep the PDF and the generated assets
	@rm -f $(JUNK)
	@rm -rf $(ARXIVDIR) $(ARXIV)

help:  ## List targets
	@grep -hE '^[a-z][a-z-]*:.*##' $(MAKEFILE_LIST) \
	  | sed -E 's/:.*## /\t/' | expand -t 14
