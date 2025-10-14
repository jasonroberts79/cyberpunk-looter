# Deployment Guide

## Quick Start

### Prerequisites
1. GCP account with billing enabled
2. Discord bot token
3. Neo4j database (Aura free tier or self-hosted)
4. OpenAI API key for embeddings
5. Grok API key (or compatible LLM API)

### Step 1: Create GCP Service Account

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Create service account
gcloud iam service-accounts create discord-bot-deployer \
    --display-name="Discord Bot Deployer" \
    --project=$env:PROJECT_ID

# Grant necessary roles
gcloud projects add-iam-policy-binding $env:PROJECT_ID \
    --member="serviceAccount:discord-bot-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $env:PROJECT_ID \
    --member="serviceAccount:discord-bot-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding $env:PROJECT_ID \
    --member="serviceAccount:discord-bot-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.admin"

gcloud projects add-iam-policy-binding $env:PROJECT_ID \
    --member="serviceAccount:discord-bot-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create ~/discord-bot-key.json \
    --iam-account=discord-bot-deployer@${PROJECT_ID}.iam.gserviceaccount.com
```

### Step 2: Configure GitHub Secrets

Go to your repository settings → Secrets and variables → Actions, and add:

1. Variable: `GCP_PROJECT_ID` - Your GCP project ID
2. Secret: `GCP_SA_KEY` - Contents of the `discord-bot-key.json` file

### Step 3: Enable Required GCP APIs

```bash
gcloud services enable run.googleapis.com --project=$env:PROJECT_ID
gcloud services enable artifactregistry.googleapis.com --project=$env:PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$env:PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$env:PROJECT_ID
```

### Step 4: Run Terraform Locally (First Time)

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan the infrastructure
terraform plan -var="project_id=$env:PROJECT_ID"
# OR
terraform plan -var="project_id=$env:PROJECT_ID"

# Apply the infrastructure
terraform apply -var="project_id=$env:PROJECT_ID"
# OR
terraform apply -var="project_id=$env:PROJECT_ID"
```

This will create:
- Artifact Registry repository
- Secret Manager secrets (empty)
- Service account for Cloud Run
- Cloud Run service (will fail to start until secrets are populated)

### Step 5: Add Secrets to GCP Secret Manager

```bash
# Add Discord bot token
echo -n "YOUR_DISCORD_BOT_TOKEN" | gcloud secrets versions add discord-bot-token --data-file=- --project=$env:PROJECT_ID

# Add Grok API key
echo -n "YOUR_GROK_API_KEY" | gcloud secrets versions add grok-api-key --data-file=- --project=$env:PROJECT_ID

# Add OpenAI embeddings key
echo -n "YOUR_OPENAI_EMBEDDINGS_KEY" | gcloud secrets versions add openai-embeddings-key --data-file=- --project=$env:PROJECT_ID

# Add Neo4j credentials
echo -n "YOUR_NEO4J_URI" | gcloud secrets versions add neo4j-uri --data-file=- --project=$env:PROJECT_ID

echo -n "YOUR_NEO4J_USERNAME" | gcloud secrets versions add neo4j-username --data-file=- --project=$env:PROJECT_ID

echo -n "YOUR_NEO4J_PASSWORD" | gcloud secrets versions add neo4j-password --data-file=- --project=$env:PROJECT_ID
```

### Step 6: Push to Trigger Deployment

```bash
git add .
git commit -m "Add GCP Cloud Run infrastructure and deployment"
git push origin main
```

The GitHub Actions workflow will:
1. Run tests
2. Apply Terraform configuration
3. Build Docker image
4. Push to Artifact Registry
5. Deploy to Cloud Run

## Monitoring Your Deployment

### Check Cloud Run Service

```bash
# Get service URL
gcloud run services describe discord-bot \
    --region=us-central1 \
    --project=$env:PROJECT_ID

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=discord-bot" \
    --limit=50 \
    --project=$env:PROJECT_ID
```

### View in Console

- Cloud Run: https://console.cloud.google.com/run?project=$env:PROJECT_ID
- Artifact Registry: https://console.cloud.google.com/artifacts?project=$env:PROJECT_ID
- Secret Manager: https://console.cloud.google.com/security/secret-manager?project=$env:PROJECT_ID

## Updating Secrets

```bash
# Update a secret
echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME \
    --data-file=- \
    --project=$env:PROJECT_ID

# Force new deployment to pick up secret changes
gcloud run services update discord-bot \
    --region=us-central1 \
    --project=$env:PROJECT_ID
```

## Rollback

```bash
# List revisions
gcloud run revisions list \
    --service=discord-bot \
    --region=us-central1 \
    --project=$env:PROJECT_ID

# Rollback to previous revision
gcloud run services update-traffic discord-bot \
    --to-revisions=REVISION_NAME=100 \
    --region=us-central1 \
    --project=$env:PROJECT_ID
```

## Manual Deployment

```bash
# Build and push image
docker build -t us-central1-docker.pkg.dev/$env:PROJECT_ID/discord-bot-repo/discord-bot:manual .
docker push us-central1-docker.pkg.dev/$env:PROJECT_ID/discord-bot-repo/discord-bot:manual

# Deploy to Cloud Run
gcloud run deploy discord-bot \
    --image=us-central1-docker.pkg.dev/$env:PROJECT_ID/discord-bot-repo/discord-bot:manual \
    --region=us-central1 \
    --project=$env:PROJECT_ID
```

## Troubleshooting

### Bot not responding

1. Check logs for errors:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=discord-bot" \
    --limit=50 \
    --project=$env:PROJECT_ID
```

2. Verify secrets are set:
```bash
gcloud secrets versions access latest --secret=discord-bot-token --project=$env:PROJECT_ID
```

3. Check service is running:
```bash
gcloud run services describe discord-bot --region=us-central1 --project=$env:PROJECT_ID
```

### Terraform errors

1. Ensure APIs are enabled
2. Verify service account permissions
3. Check if resources already exist

### GitHub Actions failures

1. Verify secrets are set correctly
2. Check service account has proper permissions
3. Review workflow logs in GitHub Actions tab

## Cost Optimization

Current configuration runs with:
- 1 minimum instance (always on) - ~$7-15/month
- 512MB memory
- 1 vCPU

To reduce costs (but bot may have cold starts):
```hcl
# In terraform/main.tf, change:
scaling {
  min_instance_count = 0  # Allow scaling to zero
  max_instance_count = 1
}
```

Note: Discord bots should typically stay running, so min 1 instance is recommended.

## Cleanup

To destroy all infrastructure:

```bash
cd terraform
terraform destroy -var="project_id=$env:PROJECT_ID"
```

This will remove:
- Cloud Run service
- Artifact Registry repository
- Service accounts
- Secrets (WARNING: This deletes your secrets permanently!)
