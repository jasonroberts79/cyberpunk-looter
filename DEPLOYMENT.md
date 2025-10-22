# Deployment Guide

## Quick Start

### Prerequisites
1. GCP account with billing enabled
2. Discord bot token
3. Neo4j database (Aura free tier or self-hosted)
4. OpenAI API key for embeddings
5. OpenAI-compatible API key (OpenAI, Grok, Azure OpenAI, etc.)

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

# Apply the infrastructure
terraform apply -var="project_id=$env:PROJECT_ID"

```

### Step 5: Add Secrets to GCP Secret Manager

```bash
# Add Discord bot token
echo -n "YOUR_DISCORD_BOT_TOKEN" | gcloud secrets versions add discord-bot-token --data-file=- --project=$env:PROJECT_ID

# Add OpenAI-compatible API key
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=- --project=$env:PROJECT_ID

# Add OpenAI embeddings key
echo -n "YOUR_OPENAI_EMBEDDINGS_KEY" | gcloud secrets versions add openai-embeddings-key --data-file=- --project=$env:PROJECT_ID

# Add Neo4j credentials
echo -n "YOUR_NEO4J_URI" | gcloud secrets versions add neo4j-uri --data-file=- --project=$env:PROJECT_ID

echo -n "YOUR_NEO4J_USERNAME" | gcloud secrets versions add neo4j-username --data-file=- --project=$env:PROJECT_ID

echo -n "YOUR_NEO4J_PASSWORD" | gcloud secrets versions add neo4j-password --data-file=- --project=$env:PROJECT_ID
```