---
title: "Your Paper Title"
subtitle: "Optional Subtitle"
author:
  - name: John Doe
    email: john@example.com
    affiliation: 1
  - name: Jane Smith
    email: jane@example.com
    affiliation: [1, 2]
    corresponding: true
date: "2025-11-22"
abstract: |
  This is the abstract of your paper. It should be a concise summary of your research,
  typically 150-250 words. Include the main objective, methods, key results, and conclusions.

  Use multiple paragraphs if needed for clarity.
keywords: [keyword1, keyword2, keyword3, keyword4]
bibliography: references.bib
csl: nature.csl
link-citations: true
number-sections: true
urlcolor: blue
---

# Affiliations

^1^ Department Name, Institution Name, City, Country
^2^ Second Institution Name, City, Country
^*^ Corresponding author

# Introduction

Start your introduction here. You can cite references using [@AuthorYear] syntax, for example: recent research [@Smith2024] has shown that...

For multiple citations, use [@Author2023; @Jones2024].

Inline equations can be written as $E=mc^2$ within text.

# Methods

Describe your methodology here. You can include block equations:

$$
\frac{\partial f}{\partial t} + \nabla \cdot (f\mathbf{v}) = S
$$ {#eq:transport}

Reference the equation using @eq:transport in your text.

## Subsection Example

Use subsections to organize your content logically.

# Results

Present your findings here. You can include tables:

| Parameter | Value | Unit |
|-----------|-------|------|
| α         | 0.05  | rad  |
| β         | 1.23  | m/s  |
| γ         | 42.0  | kg   |

: Sample measurement results {#tbl:results}

Reference the table as @tbl:results in your text.

You can also include figures:

![This is the figure caption describing what the figure shows. Be detailed and specific.](figures/example.png){#fig:example width=80%}

Reference figures using @fig:example in the text.

# Discussion

Interpret your results here. Compare with previous work [@PreviousStudy2023] and discuss implications.

Multiple citations can be grouped: [@Study1; @Study2; @Study3].

# Conclusion

Summarize your main findings and their significance. Suggest future research directions.

# Acknowledgments

Acknowledge funding sources, collaborators, and resources here.

# References

::: {#refs}
:::

# Supplementary Material {.unnumbered}

Optional supplementary information can be included here.
