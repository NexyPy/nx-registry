<!--
  Thanks for the pull request. The three sections below are required. Before you open it:

  1. Branch from `develop`: `feature/*`, `fix/*`, `docs/*`, `perf/*` or `chore/*`.
  2. Write the test first, and watch it fail before the code makes it pass.
  3. Run the gates the CI runs: `uv run pytest`, `uv run ruff check src tests`,
     `uv run ruff format src tests --check`, `uv run mypy src tests` and
     `uv run bandit -r src -q`.
-->

## Summary

<!-- Link one issue on its own line below. -->

Closes #

## How did you test this change?

<!-- The commands you ran and what they printed. -->

## Checklist

- [ ] The description has a `Closes #`, `Fixes #` or `Resolves #` line
- [ ] Tests pass with 100 percent statement and branch coverage
- [ ] Ruff, format, mypy strict and bandit pass
- [ ] Each new behaviour has a test that failed before the change
- [ ] Each commit changes one file written by hand, with its test
- [ ] Commit messages follow Conventional Commits
- [ ] No AI tool appears as author or co-author
