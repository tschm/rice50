# The Rice SIAM chapter 50-digit challenge

In 2005 the Rice University SIAM student chapter published five problems, each
with a single real number as its answer, to be given to as many correct digits
as possible. This repository holds a corrected edition of my write-up of them,
together with the code that computes every number in it.

The paper builds to `digit50.pdf`. The latest build is also published to the
orphan branch [`paper`](https://github.com/tschm/rice50/tree/paper), which
holds that one file and nothing else.

## What is corrected

The original is twenty years old and three of its sections needed work.

- **Problem 5 was wrong.** The two balls exchanged their whole velocity
  vectors on impact, which is only the head-on case. For smooth spheres of
  equal mass just the normal component of the relative velocity reverses.
  Both rules conserve energy and momentum, which is why the error survived
  every check the note made.
- **Problem 2 drew the wrong moral from a right answer.** A table of
  Mathematica runs was read as showing that a loss of 43 digits is unavoidable
  in an elliptic billiard. It measured the worst-case bound significance
  arithmetic carries, not the conditioning of the problem.
- **Problem 4 certified its answer the wrong way.** Perturbing the initial
  data measures conditioning; the integration error is common to all those
  runs and cannot show up in their spread. Both experiments are now run, and
  separately.
- **Problem 3 had a gap.** The bound that licensed truncating the polynomial
  controls function values and says nothing about where the roots go.
  Rouché's theorem closes it.

The MATLAB and Mathematica of 2005 has been rewritten in Python. An appendix
adds a sixth problem, the integral of $\sin^2(\tan(\tan(\pi x)))$ over $[0,1]$,
which is where the mathematics is.

## Nothing is typed by hand

`code/paper.py` computes every result and writes all three asset directories:

| directory   | contents                                                        |
|-------------|-----------------------------------------------------------------|
| `figs/`     | the figures, as PDF                                             |
| `tables/`   | the tables, plus `numbers.tex`, one LaTeX macro per constant     |
| `snippets/` | the listings, cut out of `code/*.py` between sentinel comments   |

`digit50.tex` `\input{}`s them. A displayed constant in the text is a macro
expansion, and a listing is the code that ran rather than a transcript of it,
so the paper and the code cannot drift apart.

## Building

Needs [`uv`](https://astral.sh/uv) and a pdfLaTeX with the recommended LaTeX
and font packages. `uv` handles the Python dependencies itself — `code/paper.py`
declares them inline (PEP 723), so there is no environment to set up.

```
make            # list the targets
make compile    # build digit50.pdf, regenerating assets if code/ changed
make assets     # recompute figures, tables and listings from code/
make check      # report inputs the source references but that are absent
make arxiv      # pack the LaTeX source into digit50-arxiv.zip for arXiv
make warnings   # over/underfull boxes and LaTeX warnings from the last build
make view       # open the PDF
make clean      # remove LaTeX intermediates, keep the PDF and the assets
```

`make arxiv` stages the files arXiv needs to compile the paper itself — the
source, the class, and the generated figures, tables and listings — and zips
them. No Python and no Makefile goes in: the archive has to build with nothing
installed but TeX, and it is checked here by building the PDF first.

`make assets` takes a few minutes: several of the problems are integrated in
30-digit arithmetic and each answer is computed twice, at two precisions or by
two methods.

## Layout

```
digit50.tex                 the paper
siamltex.cls, siam10.clo    the SIAM class it is set in
THE_RICE_SIAM_CHAPTER_...pdf  the 2005 original, kept for comparison
code/paper.py               the driver: writes figs/, tables/ and snippets/
code/knights.py             problem 1, a 4096-state Markov chain
code/photon.py              problem 2, a billiard between two elliptic mirrors
code/polynomial.py          problem 3, the root nearest the origin
code/planets.py             problem 4, five gravitating point masses
code/taylor.py              the Taylor-series integrator problem 4 uses
code/fishbowl.py            problem 5, two balls loose in an open bowl
code/integral.py            the appendix, by contour shift
code/snippets.py            cuts the listings out of the sources
.github/workflows/paper.yml builds the PDF and publishes it to `paper`
```

The generated directories are not committed, apart from the figures; run
`make assets` to produce the rest.

## Author

Thomas Schmelzer. Written in 2005 at the Computing Laboratory, Oxford
University, with the support of the Rhodes Trust.
