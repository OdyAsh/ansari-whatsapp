# ansari-whatsapp AWS Deployment Guide

This guide walks you through deploying the ansari-whatsapp microservice to AWS using the same infrastructure pattern as ansari-backend.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [AWS Resources](#aws-resources)
3. [Prerequisites](#prerequisites)
4. [Deployment Steps](#deployment-steps)
5. [Environment Configuration](#environment-configuration)
6. [Validation & Go-Live](#validation--go-live)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### The Deployment Pipeline

```
Developer pushes to GitHub (main/develop)
            ↓
    GitHub Actions Workflow triggers
            ↓
    Build Docker image with uv
            ↓
    Tag with git commit SHA
            ↓
    Push to Amazon ECR
            ↓
    Deploy to AWS App Runner
            ↓
    Load secrets from SSM Parameter Store
            ↓
    Service goes live! 🚀
```

### Service Architecture

```
Meta WhatsApp API
        ↓
    [Webhook Request]
        ↓
AWS App Runner (ansari-whatsapp)
        ↓
    [API Calls]
        ↓
AWS App Runner (ansari-backend)
        ↓
    [MongoDB, Claude API, etc.]
```

**Key Points:**
- ansari-whatsapp is a **client service** - it doesn't need its own database
- It communicates with ansari-backend via HTTP API calls
- Both services deployed independently on AWS App Runner
- Secrets managed via AWS Systems Manager Parameter Store

---

## AWS Resources

### Resources We'll Reuse from ansari-backend

These IAM roles already exist and we'll use them:

| Resource | Purpose | Notes |
|----------|---------|-------|
| `CustomAppRunnerServiceRole` | Allows App Runner to pull Docker images from ECR | Already has ECR access policy attached |
| `CustomAppRunnerInstanceRole` | Allows your app to read secrets from SSM | Already has Parameter Store access |
| `app-runner-github-actions-user` | GitHub Actions credentials for AWS | Already has ECR push and App Runner deploy permissions |

### New Resources We'll Create

| Resource | Name | Purpose |
|----------|------|---------|
| ECR Repository | `ansari-whatsapp` | Store Docker images |
| App Runner Service (Staging) | `ansari-whatsapp-staging` | Staging environment |
| App Runner Service (Production) | `ansari-whatsapp-production` | Production environment |
| SSM Parameters | `/app-runtime/ansari-whatsapp/staging/*` | Staging environment variables |
| SSM Parameters | `/app-runtime/ansari-whatsapp/production/*` | Production environment variables |

### Resource Specifications

**App Runner Configuration:**
- **Region**: us-west-2 (Oregon) - same as ansari-backend
- **CPU**: 1 vCPU
- **Memory**: 2 GB
- **Port**: 8001
- **Health Check**: `GET /` (returns `{"status": "ok"}`)
- **Auto-scaling**: Enabled (default)
- **Min/Max Instances**: 1/25 (default)

**Why These Specs?**
- **1 vCPU + 2GB**: ansari-whatsapp is lightweight - just webhook handling and HTTP forwarding
- **Port 8001**: Distinguishes from ansari-backend (8000)
- **us-west-2**: Same region as backend for low latency communication

---

## Prerequisites

Before you begin, ensure you have:

- [x] AWS CLI installed and configured (`aws --version`)
- [x] AWS credentials with admin access (or permissions for ECR, App Runner, SSM, IAM)
- [x] AWS profile named `ansari` configured (or adjust commands to use your profile)
- [x] Access to the ansari-project GitHub organization
- [x] Admin access to the ansari-whatsapp repository settings (to add secrets)
- [x] The existing IAM role ARNs from ansari-backend:
  - `CustomAppRunnerServiceRole` ARN
  - `CustomAppRunnerInstanceRole` ARN
  - `app-runner-github-actions-user` access keys

**To Get Existing Role ARNs:**
```bash
# Get Service Role ARN
aws iam get-role --role-name CustomAppRunnerServiceRole \
  --query 'Role.Arn' --output text \
  --profile ansari --region us-west-2

# Get Instance Role ARN
aws iam get-role --role-name CustomAppRunnerInstanceRole \
  --query 'Role.Arn' --output text \
  --profile ansari --region us-west-2
```

---

## Deployment Steps

### Step 1: Create AWS Resources

Follow the detailed commands in [aws-cli.md](./aws-cli.md) to create:
1. ECR repository for ansari-whatsapp
2. SSM parameters for staging environment
3. SSM parameters for production environment

**Quick Summary:**
```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name ansari-whatsapp \
  --profile ansari --region us-west-2

# 2. Add SSM parameters (see aws-cli.md for complete list)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/backend-server-url" \
  --value "https://staging-api.ansari.chat" \
  --type SecureString \
  --profile ansari --region us-west-2
```

### Step 2: Configure GitHub Secrets

Follow the detailed instructions in [github_actions_setup.md](./github_actions_setup.md) to add:
- AWS credentials (reuse from ansari-backend)
- ECR registry URL
- App Runner service names
- IAM role ARNs
- Environment-specific settings

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `SERVICE_ROLE_ARN`
- `INSTANCE_ROLE_ARN`
- `SSM_ROOT_STAGING`
- `SSM_ROOT_PRODUCTION`

### Step 3: First Deployment

**For Staging:**
1. Push to `develop` branch (or merge a PR to develop)
2. GitHub Actions will automatically trigger `deploy-staging.yml`
3. Monitor the workflow in GitHub Actions tab
4. Wait for deployment to complete (~5-10 minutes)
5. App Runner URL will be output in the workflow logs

**For Production:**
1. Push to `main` branch (or manually trigger workflow)
2. GitHub Actions will automatically trigger `deploy-production.yml`
3. Monitor and wait for completion
4. Note the production App Runner URL

### Step 4: Update Meta Webhook URL

Once deployed, you need to tell Meta about the new webhook URL:

**Current Setup (Local Development):**
- Webhook URL: `https://<ZROK_TOKEN>.share.zrok.io/whatsapp/v2`

**New Setup (Production):**
- Webhook URL: `https://<app-runner-url>/whatsapp/v2`

**How to Update:**
1. Go to [Meta App Dashboard](https://developers.facebook.com/apps/)
2. Select your WhatsApp app
3. Navigate to WhatsApp → Configuration
4. Update Callback URL to: `https://<your-app-runner-url>/whatsapp/v2`
5. Verify token should remain the same (stored in SSM)
6. Click "Verify and Save"

**Testing:**
- Send a WhatsApp message to your business number
- Check App Runner logs in AWS Console
- Verify response is sent back to WhatsApp

---

## Environment Configuration

### Environment Variables by Category

The ansari-whatsapp service needs these environment variables, all stored in AWS SSM Parameter Store:

#### **Backend Integration**
| Variable | Staging Value | Production Value |
|----------|---------------|------------------|
| `BACKEND_SERVER_URL` | `https://staging-api.ansari.chat` | `https://api.ansari.chat` |
| `DEPLOYMENT_TYPE` | `staging` | `production` |

#### **Meta/WhatsApp Credentials**
| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `META_ACCESS_TOKEN_FROM_SYS_USER` | System user access token | Meta Business Dashboard |
| `META_BUSINESS_PHONE_NUMBER_ID` | WhatsApp business phone ID | Meta WhatsApp Settings |
| `META_WEBHOOK_VERIFY_TOKEN` | Webhook verification token | You generate this (secure random string) |
| `META_API_VERSION` | WhatsApp API version | Currently `v22.0` |

#### **Application Settings**
| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind to all interfaces |
| `PORT` | `8001` | Service port |
| `WHATSAPP_CHAT_RETENTION_HOURS` | `3` | How long to keep chat history |
| `WHATSAPP_MESSAGE_AGE_THRESHOLD_SECONDS` | `86400` | Reject messages older than 24 hours |
| `WHATSAPP_UNDER_MAINTENANCE` | `False` | Enable maintenance mode |

#### **Operational Settings**
| Variable | Default | Description |
|----------|---------|-------------|
| `ALWAYS_RETURN_OK_TO_META` | `True` | Always return HTTP 200 to Meta (required!) |
| `LOGGING_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `ORIGINS` | Auto-configured | CORS allowed origins |

### SSM Parameter Store Structure

**Staging Environment:**
```
/app-runtime/ansari-whatsapp/staging/
├── backend-server-url
├── deployment-type
├── meta-access-token-from-sys-user
├── meta-business-phone-number-id
├── meta-webhook-verify-token
├── meta-api-version
├── whatsapp-chat-retention-hours
├── whatsapp-message-age-threshold-seconds
├── whatsapp-under-maintenance
├── always-return-ok-to-meta
└── logging-level
```

**Production Environment:**
```
/app-runtime/ansari-whatsapp/production/
├── (same structure as staging)
```

**Note:** Parameter names use hyphens (not underscores) in SSM paths, but App Runner converts them to underscores for environment variables.

---

## Validation & Go-Live

### Pre-Deployment Checklist

Before deploying to production, verify:

- [ ] All SSM parameters are set correctly
- [ ] GitHub secrets are configured
- [ ] Staging deployment successful and tested
- [ ] App Runner service health checks passing
- [ ] Test messages sent and received in staging
- [ ] ansari-backend is accessible from App Runner
- [ ] Meta webhook URL updated (staging)
- [ ] No hardcoded secrets in code

### Post-Deployment Verification

After deployment, test these scenarios:

#### 1. Health Check
```bash
curl https://<app-runner-url>/
# Expected: {"status": "ok"}
```

#### 2. Webhook Verification (Meta's GET request)
```bash
curl "https://<app-runner-url>/whatsapp/v2?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=<your-verify-token>"
# Expected: test123
```

#### 3. Send Test WhatsApp Message
- Send a message to your WhatsApp business number
- Check App Runner logs for incoming webhook
- Verify response received in WhatsApp

#### 4. Check Logs in AWS Console
1. Go to AWS Console → App Runner
2. Select `ansari-whatsapp-production` service
3. Click "Logs" tab
4. Look for recent webhook requests

#### 5. Monitor Error Rates
- Check CloudWatch metrics for the service
- Look for 4xx/5xx error rates
- Verify latency is acceptable (<1s for health checks)

### Rollback Procedures

If something goes wrong after deployment:

**Option 1: Revert Git Commit**
```bash
git revert <bad-commit-sha>
git push origin main
# This triggers a new deployment with the reverted code
```

**Option 2: Manual Rollback in AWS Console**
1. Go to App Runner → ansari-whatsapp-production
2. Click "Deployments" tab
3. Find the last working deployment
4. Click "Rollback to this deployment"

**Option 3: Emergency - Point Meta Back to Staging**
1. Go to Meta App Dashboard
2. Update webhook URL to staging URL temporarily
3. Fix production issue
4. Redeploy
5. Point Meta back to production

---

## Troubleshooting

### Common Issues

#### Issue: "App Runner service failed to start"
**Symptoms:** Service shows "Failed" status in AWS Console

**Possible Causes:**
1. **Port mismatch:** Dockerfile exposes 8001, but App Runner expects different port
   - **Fix:** Verify `PORT=8001` in environment variables
2. **Missing environment variables:** Required vars not set in SSM
   - **Fix:** Check all parameters in SSM Parameter Store
3. **Health check failing:** App failing to respond to GET /
   - **Fix:** Check application logs for startup errors

#### Issue: "Could not pull image from ECR"
**Symptoms:** Deployment fails at image pull step

**Possible Causes:**
1. **Wrong service role:** App Runner doesn't have ECR access
   - **Fix:** Verify `CustomAppRunnerServiceRole` is attached
2. **Image doesn't exist:** Build failed or image not pushed
   - **Fix:** Check GitHub Actions logs for build errors
3. **Wrong region:** Looking in wrong ECR registry
   - **Fix:** Verify region is `us-west-2` in workflow

#### Issue: "Meta webhook returning 401 Unauthorized"
**Symptoms:** Meta shows webhook verification failed

**Possible Causes:**
1. **Wrong verify token:** SSM parameter doesn't match Meta config
   - **Fix:** Verify `META_WEBHOOK_VERIFY_TOKEN` matches Meta dashboard
2. **Environment variable not loaded:** App Runner didn't inject the var
   - **Fix:** Check "Configuration" tab in App Runner console

#### Issue: "Messages not reaching ansari-backend"
**Symptoms:** WhatsApp receives no response, logs show backend errors

**Possible Causes:**
1. **Wrong backend URL:** Pointing to wrong environment
   - **Fix:** Verify `BACKEND_SERVER_URL` in SSM
2. **Backend not running:** ansari-backend service is down
   - **Fix:** Check ansari-backend App Runner service status
3. **Network issue:** App Runner can't reach backend
   - **Fix:** Verify both services in same VPC (if using VPC)

### Debugging Commands

**Check App Runner Service Status:**
```bash
aws apprunner list-services --profile ansari --region us-west-2
aws apprunner describe-service --service-arn <service-arn> --profile ansari --region us-west-2
```

**Check SSM Parameters:**
```bash
aws ssm get-parameters-by-path \
  --path "/app-runtime/ansari-whatsapp/production" \
  --with-decryption \
  --profile ansari --region us-west-2
```

**Check ECR Images:**
```bash
aws ecr list-images --repository-name ansari-whatsapp \
  --profile ansari --region us-west-2
```

**View App Runner Logs (CLI):**
```bash
aws logs tail /aws/apprunner/ansari-whatsapp-production/service \
  --follow \
  --profile ansari --region us-west-2
```

### Getting Help

If you're stuck:
1. Check AWS App Runner logs in the Console
2. Review GitHub Actions workflow logs
3. Compare with ansari-backend deployment (working reference)
4. Check Meta Developer Console for webhook errors
5. Consult the [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)

---

## Next Steps

After successful deployment:

1. **Monitor Performance**
   - Set up CloudWatch alarms for error rates
   - Monitor response times
   - Track WhatsApp message volume

2. **Security Hardening**
   - Rotate access tokens periodically
   - Review IAM policies for least privilege
   - Enable AWS CloudTrail for audit logging

3. **Optimization**
   - Adjust auto-scaling settings based on traffic
   - Optimize Docker image size
   - Consider VPC integration for better security

4. **Documentation**
   - Document any environment-specific quirks
   - Update runbooks for on-call engineers
   - Create dashboards for monitoring

---

**Congratulations! 🎉 Your ansari-whatsapp service is now running on AWS App Runner!**
