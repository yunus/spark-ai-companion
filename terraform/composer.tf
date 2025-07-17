# 1. Dedicated Service Account for Cloud Composer with least-privilege roles
module "service_accounts_composer" {
  source     = "terraform-google-modules/service-accounts/google"
  version    = "~> 4.1"
  project_id = var.project_id
  prefix     = "composer"
  names      = ["composer-sa"]

  project_roles = [
    "${var.project_id}=>roles/composer.worker",
    "${var.project_id}=>roles/bigquery.jobUser",  
    "${var.project_id}=>roles/bigquery.dataEditor"
  ]
}

# 2. Cloud Composer Environment using the dedicated Service Account
resource "google_composer_environment" "airflow_troubleshooter" {
  provider = google-beta
  project  = var.project_id
  name     = "composer-env"
  region   = var.region

  config {
    software_config {
      image_version = "composer-3-airflow-2.10.5"
    }
    node_config {
      network         = module.vpc.network_name
      subnetwork      = module.vpc.subnets_self_links[0]
      service_account = module.service_accounts_composer.email
    }
  }
}
