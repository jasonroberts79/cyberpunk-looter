variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "discord-bot"
}

variable "artifact_registry_repo" {
  description = "Name of the Artifact Registry repository"
  type        = string
  default     = "discord-bot-repo"
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "openai_model" {
  description = "OpenAI model to use"
  type        = string
  default     = "grok-4-fast"
}

variable "openai_base_url" {
  description = "OpenAI API base URL"
  type        = string
  default     = "https://api.x.ai/v1"
}
