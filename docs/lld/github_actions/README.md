# GitHub Actions Configuration Guide

This guide explains how GitHub Actions CI/CD is configured for the ansari-whatsapp repository, including secrets, variables, environments, and workflows.

## Table of Contents

- [GitHub Actions Configuration Guide](#github-actions-configuration-guide)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
    - [What is GitHub Actions?](#what-is-github-actions)
    - [ansari-whatsapp CI/CD Architecture](#ansari-whatsapp-cicd-architecture)
  - [Secrets \& Variables Distribution](#secrets--variables-distribution)
    - [Architecture: Repository vs Environment-Level](#architecture-repository-vs-environment-level)
    - [Distribution Table in ansari-whatsapp](#distribution-table-in-ansari-whatsapp)
  - [GitHub CLI Commands](#github-cli-commands)
    - [Prerequisites](#prerequisites)
    - [Creating Environments](#creating-environments)
    - [Setting Secrets](#setting-secrets)
    - [Setting Variables](#setting-variables)
    - [Viewing Secrets \& Variables](#viewing-secrets--variables)
    - [Updating Secrets \& Variables](#updating-secrets--variables)
    - [Deleting Secrets \& Variables](#deleting-secrets--variables)
  - [Understanding Workflows in GitHub Actions](#understanding-workflows-in-github-actions)
  - [ansari-whatsapp Workflows](#ansari-whatsapp-workflows)
  - [Ansari WhatsApp Pytests (perform-tests.yml)](#ansari-whatsapp-pytests-perform-testsyml)
  - [Syntax of Environment Variables in Workflows](#syntax-of-environment-variables-in-workflows)
  - [Artifacts](#artifacts)
  - [Monitoring](#monitoring)
    - [Monitoring Workflow Runs](#monitoring-workflow-runs)
  - [Troubleshooting](#troubleshooting)
    - [Debug Tips](#debug-tips)


---

## Overview

### What is GitHub Actions?

GitHub Actions is a CI/CD (Continuous Integration/Continuous Deployment) platform that allows you to automate your build, test, and deployment pipeline. It runs workflows in response to events in your repository (like pushes, pull requests, etc.).

**Key Concepts:**
- **Workflow**: A configurable automated process defined in `.github/workflows/*.yml`
- **Job**: A set of steps that execute on the same runner
- **Step**: An individual task that runs commands or actions
- **Runner**: A server that runs workflows (GitHub-hosted or self-hosted)
- **Action**: A reusable unit of code (like `actions/checkout@v4`)

### ansari-whatsapp CI/CD Architecture

```
Developer commits to GitHub
        ↓
GitHub Actions Workflow Triggers
        ↓
Run Tests (pytest)
        ↓
Upload Test Results as Artifacts
        ↓
(Future: Deploy to AWS App Runner)
```

**Current Setup:**
- **Test Workflow**: Runs on every push/PR to `main` or `develop` branches
- **Test Framework**: pytest with TestClient (no external dependencies)
- **Environment**: Python 3.10 container, uv for package management
- **Mock Mode**: Tests can run with mock clients (no real Meta API calls)

---

## Secrets & Variables Distribution

### Architecture: Repository vs Environment-Level

GitHub supports two levels for storing secrets and variables:
1. **Repository-level**: Accessible by all workflows in the repository
2. **Environment-level**: Scoped to specific environments (e.g., staging, production)

### Distribution Table in ansari-whatsapp

| Setting | Type | Level | Staging Value | Production Value |
|---------|------|-------|---------------|------------------|
| `META_WEBHOOK_VERIFY_TOKEN` | Secret | Repository | (same) | (same) |
| `WHATSAPP_DEV_PHONE_NUM` | Secret | Repository | (same) | (same) |
| `WHATSAPP_DEV_MESSAGE_ID` | Secret | Repository | (same) | (same) |
| `META_BUSINESS_PHONE_NUMBER_ID` | Secret | Environment | staging_phone_id | production_phone_id |
| `META_ACCESS_TOKEN_FROM_SYS_USER` | Secret | Environment | staging_token | production_token |
| `BACKEND_SERVER_URL` | Variable | Environment | staging URL | production URL |
| `MOCK_META_API` | Variable | Repository | `false` | `false` |
| `MOCK_ANSARI_CLIENT` | Variable | Repository | `false` | `false` |

IMPORTANT NOTES: If, for some reason, a key is defined:
1. In both repository and environment levels, the environment-level value takes precedence.
2. As a secret AND as a variable, the secret takes precedence.

---

## GitHub CLI Commands

These were (mostly) the commands used to set up the GitHub Actions environments, secrets, and variables for ansari-whatsapp. You can reuse these commands to modify or add new settings as needed.

### Prerequisites

Install GitHub CLI:
```bash
# Windows (Chocolatey)
choco install gh

# macOS (Homebrew)
brew install gh

# Linux (apt)
sudo apt install gh

# Authenticate
gh auth login
```

### Creating Environments

```bash
# Create staging environment
gh api repos/:owner/:repo/environments/gh-actions-staging-env --method PUT

# Create production environment
gh api repos/:owner/:repo/environments/gh-actions-production-env --method PUT
```

**Replace `:owner` and `:repo` with actual values:**
```bash
gh api repos/ansari-project/ansari-whatsapp/environments/gh-actions-staging-env --method PUT
```

Note about `:owner`: In the above example, `ansari-project` is the organization name. However, you may initially use your username in case you forked the repository. After creating and testing the environments, you can then transfer them to the organization.

### Setting Secrets

**Repository-level secrets (shared across all environments):**
```bash
# Meta webhook verification token (same for all environments)
gh secret set META_WEBHOOK_VERIFY_TOKEN --body "your_webhook_verify_token"

# Test phone number (used in CI tests)
gh secret set WHATSAPP_DEV_PHONE_NUM --body "201234567899"

# Test message ID (used in CI tests)
gh secret set WHATSAPP_DEV_MESSAGE_ID --body "wamid.seventy_two_char_hash"
```

**Environment-level secrets (different per environment):**
```bash
# Staging environment
gh secret set META_BUSINESS_PHONE_NUMBER_ID --env gh-actions-staging-env --body "staging_phone_id"
gh secret set META_ACCESS_TOKEN_FROM_SYS_USER --env gh-actions-staging-env --body "staging_access_token"

# Production environment
gh secret set META_BUSINESS_PHONE_NUMBER_ID --env gh-actions-production-env --body "production_phone_id"
gh secret set META_ACCESS_TOKEN_FROM_SYS_USER --env gh-actions-production-env --body "production_access_token"
```

### Setting Variables

**Environment-level variables:**
```bash
# Staging environment
gh variable set BACKEND_SERVER_URL --env gh-actions-staging-env --body "https://staging-api.ansari.chat"

# Production environment
gh variable set BACKEND_SERVER_URL --env gh-actions-production-env --body "https://api.ansari.chat"
```

**Repository-level variables:**
```bash
# Mock mode settings (used in tests)
gh variable set MOCK_META_API --body "false"
gh variable set MOCK_ANSARI_CLIENT --body "false"
```

### Viewing Secrets & Variables

```bash
# List repository secrets (names only, values are hidden)
gh secret list

# List environment secrets
gh secret list --env gh-actions-staging-env

# List repository variables
gh variable list

# List environment variables
gh variable list --env gh-actions-staging-env
```

### Updating Secrets & Variables

The same `gh secret set` / `gh variable set` syntax.

### Deleting Secrets & Variables

Use `gh secret delete` / `gh variable delete`.

---

## Understanding Workflows in GitHub Actions

A GitHub Actions workflow is defined in a YAML file (`.github/workflows/*.yml`) with this structure:

## ansari-whatsapp Workflows

## Ansari WhatsApp Pytests (perform-tests.yml)

**Workflow file:** `.github/workflows/perform-tests.yml`

**Flow diagram:**
```
Push/PR to main or develop
        ↓
Checkout repository code
        ↓
Install uv package manager
        ↓
Install dependencies (uv pip install -e .)
        ↓
Run pytest tests
        ↓
Upload test results (always, even if tests fail)
```

## Syntax of Environment Variables in Workflows

**Syntax for accessing secrets:**
```yaml
env:
  MY_SECRET: ${{ secrets.MY_SECRET }}
```

**Syntax for accessing variables:**
```yaml
env:
  MY_VAR: ${{ vars.MY_VAR }}
```

**With fallback values:**
```yaml
env:
  MY_VAR: ${{ vars.MY_VAR || 'default_value' }}
```

**Using environment-level secrets:**
```yaml
jobs:
  my-job:
    environment: gh-actions-staging-env    # Specify environment
    env:
      # Now secrets/vars are pulled from environment level first, but if not found, then they're pulled from repo level
      MY_SECRET: ${{ secrets.MY_SECRET }}
```

## Artifacts

**What are artifacts?**
- Files produced by workflow runs (logs, test results, build outputs)
- Stored for 30 days by default (configurable)
- Downloadable from GitHub Actions UI

**Current artifacts:**
- `test-results` (retention: 30 days)
  - `tests/detailed_test_results_whatsapp_service.json` - Test result summary
  - `tests/test_runner.log` - Test execution logs

**Uploading artifacts:**
```yaml
- name: Upload test results
  uses: actions/upload-artifact@v4
  if: always()                          # Run even if previous steps failed
  with:
    name: test-results
    path: |
      tests/detailed_test_results_whatsapp_service.json
      tests/test_runner.log
    retention-days: 30
```

---

## Monitoring

### Monitoring Workflow Runs

**GitHub UI:**
1. Go to repository: `https://github.com/ansari-project/ansari-whatsapp`
2. Click **Actions** tab
3. See the workflow runs.

**View detailed logs:**
1. Click on a workflow run
2. Click on the job name (`ansari-whatsapp-tests`)
3. Expand individual steps to see output

**Download artifacts:**
1. Scroll to bottom of workflow run page
2. Under "Artifacts" section, click the artifact name
3. Downloads a ZIP file with test results


---

## Troubleshooting

### Debug Tips

**Enable debug logging:**
1. Go to repository Settings � Secrets and variables � Actions
2. Add repository variable: `ACTIONS_STEP_DEBUG` = `true`
3. Rerun workflow to see detailed debug logs

**View raw workflow logs:**
```bash
# Using GitHub CLI
gh run view <run-id> --log

# List recent runs
gh run list --limit 5
```

**Test workflow changes locally:**
Use [act](https://github.com/nektos/act) to run workflows locally:
```bash
# Install act
brew install act  # macOS
choco install act  # Windows

# Run workflow locally
# NOTE: This will mark all of the env vars in `.env` to `secrets` context
#   Therefore, when running locally, you should temporarily change any `vars.MY_VAR` references
#   to `secrets.MY_VAR` in your workflow files.
act push --secret-file .env
```