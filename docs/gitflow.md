# GitFlow Workflow

This repository uses a lightweight GitFlow model.

## Branches

- `main`: stable branch. It should only receive changes that are ready to be considered stable.
- `develop`: integration branch. Completed features are merged here first.
- `feature/<name>`: work branches created from `develop`.
- `release/<version>`: stabilization branches created from `develop` when a release candidate makes sense.
- `hotfix/<name>`: urgent fixes created from `main`.

Release branches do not publish artifacts by themselves. Publishing packages,
GitHub Releases, tags, or PyPI distributions is a separate explicit decision.

## Current Setup

The local repository is initialized with:

```text
main
develop
feature/diagram-as-code-workflow
```

Current feature work should stay on:

```powershell
git switch feature/diagram-as-code-workflow
```

## Feature Flow

Start a feature:

```powershell
git switch develop
git pull origin develop
git switch -c feature/my-change
```

Validate locally:

```powershell
uv run ruff check .
uv run python -m unittest discover -s tests
uv run md2doc build
```

Merge completed work into `develop`:

```powershell
git switch develop
git merge --no-ff feature/my-change
```

## Release Candidate Flow

Use this only when the project is ready to stabilize a version. This creates a
branch for validation, not a published release artifact.

```powershell
git switch develop
git switch -c release/0.2.0
```

Only stabilization changes should happen on a release branch: version metadata,
documentation corrections, and final bug fixes.

When publishing is explicitly approved, merge to `main` and tag manually:

```powershell
git switch main
git merge --no-ff release/0.2.0
git tag v0.2.0
```

Then back-merge to `develop`:

```powershell
git switch develop
git merge --no-ff release/0.2.0
```

Do not publish packages or GitHub Releases unless that has been explicitly
requested.

## Hotfix Flow

Use this only for urgent fixes against stable `main`:

```powershell
git switch main
git pull origin main
git switch -c hotfix/my-fix
```

After validation:

```powershell
git switch main
git merge --no-ff hotfix/my-fix

git switch develop
git merge --no-ff hotfix/my-fix
```

## CI Policy

CI validates pushes and pull requests for:

- `main`
- `develop`
- `feature/**`
- `release/**`
- `hotfix/**`

CI does not publish release artifacts. It only validates quality, package build,
security checks, generated sample documents, and metadata consistency.
