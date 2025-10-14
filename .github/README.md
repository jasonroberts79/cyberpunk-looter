# GitHub Actions CI/CD Setup

This repository includes a GitHub Actions workflow for automated testing and deployment of the Discord bot.

## Workflow Overview

The workflow (`deploy.yml`) runs on:
- **Push** to `main` or `master` branch
- **Pull requests** to `main` or `master` branch
- **Manual trigger** (workflow_dispatch)

## Jobs

### 1. Test Job
Runs on every push and pull request:
- Sets up Python 3.11 environment
- Installs all dependencies
- Runs code linting with flake8
- Verifies required files exist

### 2. Deploy Job
Runs only on push to main/master branch:
- Triggered after successful tests
- Ready for deployment configuration

## Setting Up Deployment

### Required GitHub Secrets

To use this workflow, add the following secrets in your GitHub repository:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Add these secrets:

#### For Discord Bot Runtime (if deploying to cloud):
- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `GROK_API_KEY` or `OPENAI_API_KEY` - AI API key
- `NEO4J_URI` - Neo4j database URI
- `NEO4J_USERNAME` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password

#### For Deployment Platform:
Choose based on where you're deploying:

**Replit:**
- `REPLIT_TOKEN` - Replit deployment token

**Railway:**
- `RAILWAY_TOKEN` - Railway API token

**Render:**
- `RENDER_API_KEY` - Render API key

## Deployment Platforms

### Option 1: Replit (Current)
Uncomment the Replit deployment section in `deploy.yml` and add your Replit token.

### Option 2: Railway
1. Install Railway CLI
2. Uncomment Railway deployment section
3. Add `RAILWAY_TOKEN` secret

### Option 3: Render
1. Uncomment Render deployment section
2. Add `RENDER_API_KEY` secret
3. Update service ID in the curl command

### Option 4: Other Platforms
Add your own deployment commands in the deploy job.

## Manual Deployment

You can manually trigger the workflow:
1. Go to **Actions** tab in GitHub
2. Select **"Discord Bot CI/CD"** workflow
3. Click **"Run workflow"**
4. Select branch and run

## Important Notes

⚠️ **GitHub Actions Limitations:**
- GitHub Actions is for CI/CD automation, not for hosting the bot 24/7
- Workflows have time limits (6 hours max per job)
- Best used for testing and triggering deployments to other platforms

✅ **Recommended Setup:**
- Use this workflow for automated testing
- Deploy to a proper hosting platform (Replit, Railway, Render, etc.)
- The workflow can trigger deployments automatically on push

## Workflow Status Badge

Add this badge to your README.md to show workflow status:

```markdown
![Discord Bot CI/CD](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Discord%20Bot%20CI%2FCD/badge.svg)
```

Replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub details.
