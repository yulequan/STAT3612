# Tutorial 07: Midterm Review

**STAT/SDST3612 · Statistical Machine Learning**

Tutor: Yinghao Zhu (yhzhu99@connect.hku.hk)

Read `midterm_review_slides.pdf` (33 slides, 69 pages with step-by-step reveals). There is no
notebook: every calculation in the review is done by hand on small datasets that are printed on
the slides.

## What the deck covers

1. **Exam overview and core concepts.** The three question types (True/False and multiple choice,
   short answer, applied calculation), regression vs. classification, parametric vs. non-parametric,
   generative vs. discriminative, gradient descent and SGD, the bias-variance tradeoff, and
   validation vs. k-fold cross-validation.
2. **Linear models.** The normal equations, a fifth-order polynomial fit, Ridge vs. LASSO,
   regularization paths and Elastic Net.
3. **Classification models.** Precision, recall and ROC, linear vs. quadratic boundaries,
   k-nearest neighbors, and matching classifiers to their training errors.
4. **Trees, ensembles and SVM.** Impurity measures, a full Gini split calculation, the partition a
   fitted tree induces, bagging, random forests, boosting, support vectors and margins.
5. **Final advice.** Recurring exam traps and a preparation checklist.

Worked problems are taken from Practice Paper 1, Practice Paper 2 and Midterm 2022. Each one is
shown with its data table and a plot, and each multi-part question reveals its answer one page at a
time. A cited question is paraphrased or quoted from the supplied papers; the solutions and the
figures are written for this review.

## Using the deck

Read the PDF in the tutorial page or download `student.zip` for an offline copy with this README.
In the embedded viewer, the next page usually adds one reveal step, so a slide can appear several
times. Sketch the points, boundary or tree on paper before advancing.

## Publication source

Published from `stat3612-26fall-tutorial` (Tutorial 07, October 2026). The PDF is an unchanged copy
of that repository's `build/main.pdf`, compiled with pdfLaTeX: it is the slide-only copy, so it has
no speaker notes and no presenter script. The notes version (`main-notes.tex`) is for the tutor only.

For maintainers: edit and compile the authoring repository first, then replace this publication
copy. Website builds need neither that checkout nor LaTeX.
