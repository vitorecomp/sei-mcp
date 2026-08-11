output "load_balancer_ip" {
  value       = google_compute_global_address.lb_ip.address
  description = "The external static IP address assigned to the Global Load Balancer"
}

output "url_map_id" {
  value       = google_compute_url_map.url_map.id
  description = "The ID of the created URL Map"
}

output "mcp_sse_endpoint_http" {
  value       = "http://${google_compute_global_address.lb_ip.address}/sse"
  description = "HTTP SSE endpoint to use in Gemini Enterprise / MCP clients"
}

output "mcp_sse_endpoint_https" {
  value       = var.enable_ssl && var.domain_name != "" ? "https://${var.domain_name}/sse" : null
  description = "HTTPS SSE endpoint to use in Gemini Enterprise when custom domain and SSL are enabled"
}
