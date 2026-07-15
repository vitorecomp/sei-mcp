variable "project_id" {
  type        = string
  description = "The Google Cloud Project ID where resources will be created"
}

variable "region" {
  type        = string
  description = "The GCP region where Cloud Run service is deployed"
  default     = "southamerica-east1"
}

variable "cloud_run_service_name" {
  type        = string
  description = "The name of the Cloud Run service"
  default     = "sei-mcp-server"
}

variable "enable_ssl" {
  type        = boolean
  description = "Set to true to provision Google-managed SSL certificate for domain_name"
  default     = false
}

variable "domain_name" {
  type        = string
  description = "The custom domain name for the Load Balancer SSL certificate (e.g. mcp.example.com)"
  default     = ""
}
