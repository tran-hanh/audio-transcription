# CI/CD Pipeline Documentation

This project uses a **single unified CI/CD pipeline** that handles testing, linting, and deployment.

## Workflow Overview

### **Unified CI/CD Pipeline** (`.github/workflows/ci-cd.yml`)

One workflow that handles everything:

**Jobs:**
1. **Test** - Runs pytest tests on Python 3.12 and 3.13
2. **Lint** - Runs pylint for code quality checks
3. **Deploy** - Deploys to GitHub Pages (only if tests and lint pass)

**Triggers:**
- Push to `main` branch
- Pull requests to `main` branch
- Manual trigger via `workflow_dispatch`

## How It Works

### On Push to Main Branch:

```
┌─────────────┐
│   Push to   │
│    main     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   CI/CD Pipeline    │
└──────┬──────────────┘
       │
       ├───┐
       │   │
       ▼   ▼
   ┌────┐ ┌────┐
   │Test│ │Lint│  (Run in parallel)
   └─┬──┘ └─┬──┘
     │      │
     └──┬───┘
        │
        ▼
   ┌─────────┐
   │  Deploy │  (Only if both pass)
   │  Pages  │
   └─────────┘
```

### On Pull Request:

```
┌─────────────┐
│ Pull Request│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   CI/CD Pipeline    │
└──────┬──────────────┘
       │
       ├───┐
       │   │
       ▼   ▼
   ┌────┐ ┌────┐
   │Test│ │Lint│  (Run in parallel)
   └────┘ └────┘
   
   (No deployment on PRs)
```

## Pipeline Stages

### 1. Test Job
- **Runs on:** Python 3.12 and 3.13 (matrix strategy)
- **Steps:**
  - Checkout code
  - Set up Python
  - Install dependencies
  - Run pytest tests
  - Generate coverage report
  - Upload to Codecov

### 2. Lint Job
- **Runs on:** Python 3.12
- **Steps:**
  - Checkout code
  - Set up Python
  - Install pylint
  - Run pylint on all Python files

### 3. Deploy Job
- **Runs only if:**
  - Test job passes ✅
  - Lint job passes ✅
  - Push to `main` branch (not PRs)
- **Steps:**
  - Checkout code
  - Setup GitHub Pages
  - Upload artifact
  - Deploy to GitHub Pages

## Safety Features

✅ **Deployment is blocked if:**
- Tests fail
- Linting fails
- Running on a pull request (not main branch)

✅ **Tests run on multiple Python versions:**
- Python 3.12
- Python 3.13

✅ **Parallel execution:**
- Test and Lint jobs run simultaneously for faster feedback

## Coverage Reports

Coverage reports are generated and uploaded to:
- **Codecov**: Automatic coverage tracking (optional token)
- **GitHub Actions**: View in Actions tab → Artifacts

## Manual Trigger

You can manually trigger the workflow:
1. Go to **Actions** tab in GitHub
2. Select **CI/CD Pipeline**
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Workflow Status Badge

Add this to your README.md:

```markdown
![CI/CD](https://github.com/yourusername/audio_transcription/workflows/CI/CD%20Pipeline/badge.svg)
```

## Troubleshooting

### Tests Failing
1. Check the Actions tab for error details
2. Run tests locally: `pytest tests/ -v`
3. Check test logs in GitHub Actions

### Deployment Blocked
- Tests must pass before deployment
- Linting must pass before deployment
- Only runs on push to `main` (not PRs)
- Check the "Test" and "Lint" jobs in the workflow

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

## Workflow File

- `.github/workflows/ci-cd.yml` - Unified CI/CD pipeline

## Benefits of Unified Pipeline

✅ **Simpler**: One workflow file instead of multiple
✅ **Faster**: Jobs run in parallel
✅ **Clearer**: Easy to see the full pipeline flow
✅ **Safer**: Deployment only happens after all checks pass
✅ **Easier to maintain**: Single source of truth
