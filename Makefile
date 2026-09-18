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

.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.PHONY: all assets check clean distclean help view warnings

all: $(MAIN).pdf  ## Build the PDF (default)

$(MAIN).pdf: $(MAIN).tex siamltex.cls siam10.clo $(STAMP)
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

warnings: $(MAIN).pdf  ## Show over/underfull boxes and LaTeX warnings from the last build
	@grep -nE 'Warning|Overfull|Underfull' $(MAIN).log || echo "no warnings"

view: $(MAIN).pdf  ## Open the built PDF
	@(command -v open >/dev/null && open $(MAIN).pdf) || xdg-open $(MAIN).pdf

clean:  ## Remove LaTeX intermediates, keep the PDF and the generated assets
	@rm -f $(JUNK)

distclean: clean  ## Also remove the PDF and everything code/paper.py generates
	@rm -f $(MAIN).pdf $(STAMP)
	@rm -rf figs tables snippets code/__pycache__

help:  ## List targets
	@grep -hE '^[a-z][a-z-]*:.*##' $(MAKEFILE_LIST) \
	  | sed -E 's/:.*## /\t/' | expand -t 14
