output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.discord_bot.name
}

output "service_location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_v2_service.discord_bot.location
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo}"
}

output "service_account_email" {
  description = "Email of the service account"
  value       = google_service_account.discord_bot.email
}

output "bot_memory_bucket" {
  description = "Name of the Cloud Storage bucket for bot memory"
  value       = google_storage_bucket.bot_memory.name
}
