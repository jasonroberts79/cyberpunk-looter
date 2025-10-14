terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "jr_terraform_state"
    prefix = "cyberpunk-looter/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "cloud_run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry_api" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_build_api" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

  resource "google_project_service" "secret_manager_api" {
    service            = "secretmanager.googleapis.com"
    disable_on_destroy = false
  }

# Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = var.artifact_registry_repo
  description   = "Docker repository for Discord bot"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry_api]
}

# Service account for Cloud Run
resource "google_service_account" "discord_bot" {
  account_id   = "discord-bot-sa"
  display_name = "Discord Bot Service Account"
  description  = "Service account for the Discord bot running on Cloud Run"
}

# Cloud Storage bucket for bot memory
resource "google_storage_bucket" "bot_memory" {
  name          = "${var.project_id}-bot-memory"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# IAM binding for service account to access storage bucket
resource "google_storage_bucket_iam_member" "bot_memory_access" {
  bucket = google_storage_bucket.bot_memory.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.discord_bot.email}"
}

# Secret Manager for environment variables
resource "google_secret_manager_secret" "discord_token" {
  secret_id = "discord-bot-token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.cloud_run_api, google_project_service.secret_manager_api]
}

resource "google_secret_manager_secret" "grok_api_key" {
  secret_id = "grok-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.cloud_run_api, google_project_service.secret_manager_api]
}

resource "google_secret_manager_secret" "openai_embeddings_key" {
  secret_id = "openai-embeddings-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.cloud_run_api, google_project_service.secret_manager_api]
}

resource "google_secret_manager_secret" "neo4j_uri" {
  secret_id = "neo4j-uri"

  replication {
    auto {}
  }

  depends_on = [google_project_service.cloud_run_api, google_project_service.secret_manager_api]
}

resource "google_secret_manager_secret" "neo4j_username" {
  secret_id = "neo4j-username"

  replication {
    auto {}
  }

  depends_on = [google_project_service.cloud_run_api, google_project_service.secret_manager_api]
}

resource "google_secret_manager_secret" "neo4j_password" {
  secret_id = "neo4j-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.cloud_run_api, google_project_service.secret_manager_api]
}

# IAM binding for service account to access secrets
resource "google_secret_manager_secret_iam_member" "discord_token_access" {
  secret_id = google_secret_manager_secret.discord_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "grok_api_key_access" {
  secret_id = google_secret_manager_secret.grok_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "openai_embeddings_key_access" {
  secret_id = google_secret_manager_secret.openai_embeddings_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "neo4j_uri_access" {
  secret_id = google_secret_manager_secret.neo4j_uri.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "neo4j_username_access" {
  secret_id = google_secret_manager_secret.neo4j_username.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "neo4j_password_access" {
  secret_id = google_secret_manager_secret.neo4j_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

# Cloud Run Service with worker configuration (no ingress)
resource "google_cloud_run_v2_service" "discord_bot" {
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.discord_bot.email

    scaling {
      min_instance_count = 1
      max_instance_count = 1
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo}/${var.service_name}:${var.image_tag}"

      # Configure as worker (no ports exposed)
      startup_probe {
        period_seconds    = 240
        timeout_seconds   = 240
        failure_threshold = 1
        tcp_socket {
          port = 8080
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        startup_cpu_boost = true
      }

      env {
        name  = "OPENAI_MODEL"
        value = var.openai_model
      }

      env {
        name  = "OPENAI_BASE_URL"
        value = var.openai_base_url
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.bot_memory.name
      }

      # Secret environment variables
      env {
        name = "DISCORD_BOT_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.discord_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GROK_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.grok_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OPENAI_EMBEDDINGS_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_embeddings_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "NEO4J_URI"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.neo4j_uri.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "NEO4J_USERNAME"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.neo4j_username.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "NEO4J_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.neo4j_password.secret_id
            version = "latest"
          }
        }
      }
      }
    }
  }

  depends_on = [
    google_project_service.cloud_run_api,
    google_artifact_registry_repository.docker_repo,
    google_secret_manager_secret_iam_member.discord_token_access,
    google_secret_manager_secret_iam_member.grok_api_key_access,
    google_secret_manager_secret_iam_member.openai_embeddings_key_access,
    google_secret_manager_secret_iam_member.neo4j_uri_access,
    google_secret_manager_secret_iam_member.neo4j_username_access,
    google_secret_manager_secret_iam_member.neo4j_password_access
  ]

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }
}
