# Configure the Google Cloud provider
provider "google" {
  project = "macroflow-486515"
  region  = "us-central1"
}

# Create a Cloud Run service
resource "google_cloud_run_v2_service" "pyfrbus_service" {
  name     = "pyfrbus-app"
  location = "us-central1"
  deletion_protection = false
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      # This points to the image we just successfully built
      image = "gcr.io/macroflow-486515/pyfrbus-app:latest"
      
      ports {
        container_port = 8080
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1024Mi"
        }
      }
    }
  }
}

# Allow public (unauthenticated) access so your terminal can reach it
resource "google_cloud_run_v2_service_iam_binding" "public_access" {
  location = google_cloud_run_v2_service.pyfrbus_service.location
  name     = google_cloud_run_v2_service.pyfrbus_service.name
  role     = "roles/run.invoker"
  members = [
    "allUsers",
  ]
}

# Output the URL once it's deployed
output "service_url" {
  value = google_cloud_run_v2_service.pyfrbus_service.uri
}
