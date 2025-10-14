output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.discord_bot.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.discord_bot.name
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo}"
}

output "service_account_email" {
  description = "Email of the service account"
  value       = google_service_account.discord_bot.email
}
