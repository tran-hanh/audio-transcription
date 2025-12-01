# CI/CD Pipeline Documentation

This project uses GitHub Actions for continuous integration and deployment.

## Workflow Overview

### 1. **CI Pipeline** (`.github/workflows/ci.yml`)
Runs on every push and pull request to `main` or `develop` branches.

**Jobs:**
- **Test**: Runs pytest tests on Python 3.12 and 3.13
- **Lint**: Runs pylint for code quality checks

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Manual trigger via `workflow_dispatch`

### 2. **Test Workflow** (`.github/workflows/test.yml`)
Dedicated test workflow with comprehensive coverage reporting.

**Features:**
- Tests on Python 3.12 and 3.13
- Generates coverage reports
- Uploads coverage to Codecov
- Includes linting step

### 3. **Deploy Workflow** (`.github/workflows/deploy.yml`)
Deploys to GitHub Pages **only after tests pass**.

**Pipeline:**
1. ✅ **Test** - Runs all pytest tests
2. ✅ **Lint** - Runs pylint checks
3. 🚀 **Deploy** - Deploys to GitHub Pages (only if tests pass)

**Safety:** Deployment is blocked if tests fail!

### 4. **Pylint Workflow** (`.github/workflows/pylint.yml`)
Standalone code quality checks.

## How It Works

### On Push to Main Branch:

```
┌─────────────┐
│   Push to   │
│    main     │
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────┐      ┌──────────┐
│   CI     │      │  Test    │
│ Pipeline │      │ Workflow │
└────┬─────┘      └──────────┘
     │
     ├─── Test (3.12, 3.13)
     │
     ├─── Lint
     │
     └───► If all pass ──┐
                          │
                          ▼
                   ┌──────────────┐
                   │   Deploy     │
                   │   Workflow   │
                   └──────┬───────┘
                          │
                          ├─── Test (required)
                          │
                          ├─── Lint (required)
                          │
                          └─── Deploy to GitHub Pages
```

## Test Requirements

Tests **must pass** before:
- ✅ Code can be merged (via PR checks)
- ✅ Deployment to GitHub Pages
- ✅ Any production deployment

## Coverage Reports

Coverage reports are generated and uploaded to:
- **Codecov**: Automatic coverage tracking
- **GitHub Actions**: View in Actions tab → Artifacts

## Manual Testing

You can manually trigger workflows:
1. Go to **Actions** tab in GitHub
2. Select the workflow (CI, Test, Deploy)
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Workflow Status Badges

Add these to your README.md:

```markdown
![Tests](https://github.com/yourusername/audio_transcription/workflows/Run%20Tests/badge.svg)
![Deploy](https://github.com/yourusername/audio_transcription/workflows/Deploy%20to%20GitHub%20Pages/badge.svg)
```

## Troubleshooting

### Tests Failing
1. Check the Actions tab for error details
2. Run tests locally: `pytest tests/ -v`
3. Check test logs in GitHub Actions

### Deployment Blocked
- Tests must pass before deployment
- Check the "Test" and "Lint" jobs in deploy workflow
- Fix any failing tests or lint errors

### Coverage Not Uploading
- Codecov token is optional (workflow will still run)
- Coverage reports are available in Actions artifacts

## Best Practices

1. **Always run tests locally** before pushing:
   ```bash
   pytest tests/ -v
   ```

2. **Check linting** before committing:
   ```bash
   pylint $(git ls-files '*.py') --disable=import-error
   ```

3. **Review PR checks** before merging

4. **Monitor deployment** after merge to main

## Workflow Files

- `.github/workflows/ci.yml` - Main CI pipeline
- `.github/workflows/test.yml` - Comprehensive test suite
- `.github/workflows/deploy.yml` - Deployment with test gates
- `.github/workflows/pylint.yml` - Code quality checks

