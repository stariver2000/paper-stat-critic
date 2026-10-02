Below is one part of a research paper, split into blocks. Each block starts
with its id in square brackets, e.g. `[p3b2]`. Other parts of the paper are
processed separately; extract only what appears in this part.

Extract every inferential test whose statistic is printed in the text (t, F,
chi2, r, z). Use `other` for statistics outside that list (e.g. W, U, H,
beta). Include tests reported inside parentheses and in running text.

Rules:

- Copy numbers exactly as printed. Keep the number of decimals and keep or
  omit the leading zero as the paper does (`.045` stays `.045`).
- For `p < .001` set `p_comparator` to `<` and `p_value` to `.001`.
- Every `evidence.quote` must be a verbatim span copied from one block, and
  `evidence.block_id` must be that block's id.
- When the paper does not state something, use null. Never compute or guess
  a value that is not printed.

<paper>
$document
</paper>
