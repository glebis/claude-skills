---
title: Your Paper Title
subtitle: Optional Subtitle or Conference Information
description: A brief description of your paper (used for metadata and previews)
authors:
  - name: John Doe
    email: john.doe@example.com
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Jane Smith
    email: jane.smith@example.com
    orcid: 0000-0000-0000-0001
    affiliation: [1, 2]
    corresponding: true
affiliations:
  - id: 1
    name: Department of Research, University Name
    city: City Name
    country: Country
  - id: 2
    name: Institute of Advanced Studies
    city: City Name
    country: Country
date: 2025-11-22
keywords:
  - keyword1
  - keyword2
  - keyword3
license: CC-BY-4.0
open_access: true
bibliography: references.bib
---

+++ {"part": "abstract"}

This is the abstract of your paper. Write a concise summary of your work here, typically 150-250 words.
Include the research objective, methods, key findings, and conclusions.

Use multiple paragraphs if necessary for clarity.

+++

# Introduction

Start your introduction with background and motivation. You can cite references using {cite}`AuthorYear` syntax.

Multiple citations: {cite}`Author2023,Jones2024`

Inline math: $E=mc^2$

Cross-references work automatically with MyST. Define labels and reference them throughout your document.

# Methods

## Data Collection

Describe your methodology. You can include block equations with labels:

```{math}
:label: transport-eq

\frac{\partial f}{\partial t} + \nabla \cdot (f\mathbf{v}) = S
```

Reference equations using {eq}`transport-eq` in your text.

## Analysis

Further methodological details here.

# Results

Present your findings. MyST supports advanced table formatting:

```{list-table} Sample measurement results
:header-rows: 1
:name: results-table

* - Parameter
  - Value
  - Unit
* - α
  - 0.05
  - rad
* - β
  - 1.23
  - m/s
* - γ
  - 42.0
  - kg
```

Reference tables as {numref}`results-table`.

Include figures with captions:

```{figure} figures/example.png
:name: example-fig
:width: 80%

This is the figure caption. Describe what the figure shows in detail.
Include information about methods, sample size, or statistical tests if relevant.
```

Reference figures using {numref}`example-fig`.

## Subsection

Organize results clearly with subsections.

# Discussion

Interpret your results. Compare with previous studies {cite}`PreviousWork2023` and discuss implications.

## Comparison with Literature

Detailed comparison here.

## Limitations

Acknowledge limitations of your study.

# Conclusion

Summarize main findings and significance. Suggest future research directions.

# Acknowledgments

:::{note}
Acknowledge funding sources, collaborators, technical support, and resources used.
:::

# Data Availability

Describe where data and code can be accessed (e.g., GitHub, Zenodo, institutional repository).

# References

```{bibliography}
```

# Supplementary Material {.unnumbered}

Optional supplementary information, extended data tables, or additional figures.
