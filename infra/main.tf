# Reserve a static global IP address for the Load Balancer
resource "google_compute_global_address" "lb_ip" {
  name        = "${var.cloud_run_service_name}-lb-ip"
  description = "Global Static IP address for ${var.cloud_run_service_name} Load Balancer"
}

# Create Serverless Network Endpoint Group (NEG) pointing to Cloud Run
resource "google_compute_region_network_endpoint_group" "serverless_neg" {
  name                  = "${var.cloud_run_service_name}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = var.cloud_run_service_name
  }
}

# Create Backend Service for Load Balancer
resource "google_compute_backend_service" "mcp_backend" {
  name                  = "${var.cloud_run_service_name}-backend"
  protocol              = "HTTP"
  port_name             = "http"
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.serverless_neg.id
  }
}

# URL Map to route requests to backend service
resource "google_compute_url_map" "url_map" {
  name            = "${var.cloud_run_service_name}-url-map"
  default_service = google_compute_backend_service.mcp_backend.id
}

# Optional Managed SSL Certificate if domain is configured
resource "google_compute_managed_ssl_certificate" "managed_ssl" {
  count = var.enable_ssl && var.domain_name != "" ? 1 : 0
  name  = "${var.cloud_run_service_name}-ssl-cert"

  managed {
    domains = [var.domain_name]
  }
}

# Target HTTPS Proxy (used when SSL is enabled)
resource "google_compute_target_https_proxy" "https_proxy" {
  count            = var.enable_ssl && var.domain_name != "" ? 1 : 0
  name             = "${var.cloud_run_service_name}-https-proxy"
  url_map          = google_compute_url_map.url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.managed_ssl[0].id]
}

# Global Forwarding Rule for HTTPS (Port 443)
resource "google_compute_global_forwarding_rule" "https_forwarding_rule" {
  count                 = var.enable_ssl && var.domain_name != "" ? 1 : 0
  name                  = "${var.cloud_run_service_name}-https-fw-rule"
  target                = google_compute_target_https_proxy.https_proxy[0].id
  port_range            = "443"
  ip_address            = google_compute_global_address.lb_ip.address
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# Target HTTP Proxy (for standard HTTP or HTTP-to-HTTPS redirect)
resource "google_compute_target_http_proxy" "http_proxy" {
  name    = "${var.cloud_run_service_name}-http-proxy"
  url_map = google_compute_url_map.url_map.id
}

# Global Forwarding Rule for HTTP (Port 80)
resource "google_compute_global_forwarding_rule" "http_forwarding_rule" {
  name                  = "${var.cloud_run_service_name}-http-fw-rule"
  target                = google_compute_target_http_proxy.http_proxy.id
  port_range            = "80"
  ip_address            = google_compute_global_address.lb_ip.address
  load_balancing_scheme = "EXTERNAL_MANAGED"
}
