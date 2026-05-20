# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SOURCEDIR     = source
BUILDDIR      = build
ABS_SOURCEDIR := $(abspath $(SOURCEDIR))
ABS_BUILDDIR  := $(abspath $(BUILDDIR))

# Use Sphinx from the Poetry dev env when sphinx-build is not on PATH.
PROJECT_ROOT := $(abspath ..)
POETRY       := $(shell command -v poetry 2>/dev/null)
ifeq ($(SPHINXBUILD),)
  ifneq ($(POETRY),)
    SPHINXBUILD := poetry -C $(PROJECT_ROOT) run sphinx-build
  else
    SPHINXBUILD := sphinx-build
  endif
endif

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(ABS_SOURCEDIR)" "$(ABS_BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(ABS_SOURCEDIR)" "$(ABS_BUILDDIR)" $(SPHINXOPTS) $(O)
