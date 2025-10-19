# Troubleshooting GitHub Actions

Common issues and solutions for GitHub Actions workflows in ansari-whatsapp.

***TOC:***

- [Troubleshooting GitHub Actions](#troubleshooting-github-actions)
  - [Common Issues](#common-issues)
    - [Issue: "Secret not found"](#issue-secret-not-found)
    - [Issue: "Tests fail in CI but pass locally"](#issue-tests-fail-in-ci-but-pass-locally)
    - [Issue: "Artifact upload failed"](#issue-artifact-upload-failed)
    - [Issue: "Environment not found"](#issue-environment-not-found)
    - [Issue: "Permission denied" or "Resource not accessible"](#issue-permission-denied-or-resource-not-accessible)
  - [Debug Tips](#debug-tips)
    - [Enable Debug Logging](#enable-debug-logging)
    - [View Workflow Logs from CLI](#view-workflow-logs-from-cli)
    - [Test Workflows Locally](#test-workflows-locally)
    - [Check Workflow Syntax](#check-workflow-syntax)
    - [Compare with Working Setup](#compare-with-working-setup)
  - [Getting Help](#getting-help)
    - [Where to Look](#where-to-look)
    - [Common Commands for Debugging](#common-commands-for-debugging)


---

## Common Issues

### Issue: "Secret not found"

**Symptoms:**
- Workflow fails with error: `Secret MY_SECRET not found`
- Workflow step shows empty value for secret

**Causes:**
1. Secret name mismatch (typo in workflow YAML)
2. Secret not added to repository/environment
3. Accessing environment secret without specifying `environment:` in job

**Solutions:**

**Check if secret exists:**
```bash
# List repository secrets
gh secret list

# List environment secrets
gh secret list --env gh-actions-staging-env
```

**Add missing secret:**
```bash
# Repository-level
gh secret set MY_SECRET --body "my_secret_value"

# Environment-level
gh secret set MY_SECRET --env gh-actions-staging-env --body "my_secret_value"
```

**If using environment secrets, ensure job specifies environment:**
```yaml
jobs:
  my-job:
    environment: gh-actions-staging-env  # Add this line
    env:
      MY_SECRET: ${{ secrets.MY_SECRET }}
```

---

### Issue: "Tests fail in CI but pass locally"

**Symptoms:**
- Tests pass on your machine but fail in GitHub Actions
- Different behavior between local and CI environments

**Causes:**
1. Missing environment variables in CI
2. Different Python/package versions
3. Mock mode disabled in CI (trying to make real API calls)
4. Backend service not available

**Solutions:**

**1. Compare environment variables:**
- Check `.env` file locally vs GitHub secrets
- Ensure all required env vars are set in workflow

**2. Verify Python version matches:**
- Local: Check with `python --version`
- CI: Defined in workflow as `container: python:3.10`

**3. Enable mock mode in CI:**
```bash
gh variable set MOCK_META_API --body "true"
gh variable set MOCK_ANSARI_CLIENT --body "true"
```

**4. Check test logs for specific errors:**
```bash
# View recent workflow runs
gh run list --limit 5

# View logs for specific run
gh run view <run-id> --log
```

---

### Issue: "Artifact upload failed"

**Symptoms:**
- Test results not uploaded
- Error in "Upload test results" step
- Artifacts section shows no files

**Causes:**
1. File path doesn't exist (tests didn't create the file)
2. Incorrect path in workflow YAML
3. Insufficient permissions

**Solutions:**

**1. Verify files are created:**
Check test logs to ensure these files are generated:
- `tests/detailed_test_results_whatsapp_service.json`
- `tests/test_runner.log`

**2. Check workflow artifact paths:**
```yaml
- name: Upload test results
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: |
      tests/detailed_test_results_whatsapp_service.json
      tests/test_runner.log
```

**3. Ensure permissions are set:**
```yaml
permissions:
  contents: read  # Required for artifact upload
```

---

### Issue: "Environment not found"

**Symptoms:**
- Workflow fails with: `Environment 'gh-actions-staging-env' not found`
- Job references an environment that doesn't exist

**Causes:**
1. Environment hasn't been created
2. Typo in environment name

**Solutions:**

**Create the environment:**
```bash
gh api repos/ansari-project/ansari-whatsapp/environments/gh-actions-staging-env --method PUT
```

**Verify it exists:**
```bash
# List all environments
gh api repos/ansari-project/ansari-whatsapp/environments --jq '.[].name'
```

**Check in GitHub UI:**
1. Go to repository Settings → Environments
2. Verify environment name matches exactly

---

### Issue: "Permission denied" or "Resource not accessible"

**Symptoms:**
- GitHub CLI commands fail with permission errors
- Can't set secrets or create environments

**Causes:**
1. Not authenticated with GitHub CLI
2. Insufficient repository permissions
3. Using wrong repository owner/name

**Solutions:**

**1. Re-authenticate:**
```bash
gh auth logout
gh auth login
```

**2. Check repository access:**
- Ensure you have admin or write access to the repository
- If using an organization repo, ensure you're a member

**3. Verify repository path:**
```bash
# Check current repository
gh repo view

# Use full path explicitly
gh secret set MY_SECRET --repo ansari-project/ansari-whatsapp --body "value"
```

---

## Debug Tips

### Enable Debug Logging

Get more detailed logs from GitHub Actions:

**1. Add debug variable:**
```bash
gh variable set ACTIONS_STEP_DEBUG --body "true"
```

**2. Re-run workflow:**
- Go to Actions tab → Failed workflow run
- Click "Re-run jobs" → "Re-run failed jobs"

**3. View detailed logs:**
- Logs will now include debug information
- Look for lines starting with `##[debug]`

**Remove debug mode when done:**
```bash
gh variable delete ACTIONS_STEP_DEBUG
```

---

### View Workflow Logs from CLI

**List recent runs:**
```bash
gh run list --limit 5
```

**View specific run:**
```bash
gh run view <run-id>
```

**View full logs:**
```bash
gh run view <run-id> --log
```

**Watch a running workflow:**
```bash
gh run watch
```

**Download logs:**
```bash
gh run download <run-id>
```

---

### Test Workflows Locally

Use [act](https://github.com/nektos/act) to run workflows on your machine:

**Install act:**
```bash
# macOS
brew install act

# Windows (Chocolatey)
choco install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**Run workflow locally:**
```bash
# Run using .env file for secrets
# NOTE: act treats all env vars as secrets, so temporarily change
# any `vars.MY_VAR` references to `secrets.MY_VAR` in workflow files
act push --secret-file .env
```

**Run specific workflow:**
```bash
act push --workflows .github/workflows/perform-tests.yml
```

---

### Check Workflow Syntax

**Validate workflow YAML:**
```bash
# Install actionlint
# macOS: brew install actionlint
# Windows: choco install actionlint

# Check workflow files
actionlint .github/workflows/*.yml
```

---

### Compare with Working Setup

If workflows stop working after changes:

**1. Check recent commits:**
```bash
git log --oneline .github/workflows/
```

**2. View diff of workflow file:**
```bash
git diff HEAD~1 .github/workflows/perform-tests.yml
```

**3. Revert to previous version if needed:**
```bash
git checkout HEAD~1 -- .github/workflows/perform-tests.yml
```

---

## Getting Help

### Where to Look

**1. GitHub Actions Documentation:**
- [Workflow syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Troubleshooting](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows)

**2. Project Documentation:**
- [Current Setup](./current_setup.md) - Verify your setup matches expected configuration
- [Setup Commands](./setup_commands.md) - Re-run setup commands if needed
- [Concepts](./concepts.md) - Review fundamental concepts

**3. Workflow Logs:**
- Always check the full logs for detailed error messages
- Look for lines marked `Error:` or `Failed:`

**4. Community Resources:**
- [GitHub Community Forum](https://github.com/orgs/community/discussions/categories/actions)
- [Stack Overflow - GitHub Actions](https://stackoverflow.com/questions/tagged/github-actions)

---

### Common Commands for Debugging

```bash
# Check authentication
gh auth status

# List all secrets (names only)
gh secret list

# List all variables
gh variable list

# View repository info
gh repo view

# List recent workflow runs
gh run list

# View specific run details
gh run view <run-id>

# Re-run failed workflow
gh run rerun <run-id> --failed
```
