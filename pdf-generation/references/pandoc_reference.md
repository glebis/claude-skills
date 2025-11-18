# Pandoc Commands Reference

## Basic PDF Generation
pandoc input.md -o output.pdf --pdf-engine=xelatex

## With Table of Contents
pandoc input.md -o output.pdf --pdf-engine=xelatex --toc --toc-depth=2

## Russian Documents (EB Garamond)
pandoc input-ru.md -o output.pdf --pdf-engine=xelatex -V mainfont="EB Garamond"

## Full Command Template
pandoc input.md -o output.pdf \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=2 \
  -V geometry:margin=2.5cm \
  -V fontsize=11pt \
  -V documentclass=article
