

locals {
  gcp_apis = [
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "bigquery.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "dataform.googleapis.com",
    "aiplatform.googleapis.com",
    "dataproc.googleapis.com",
    "composer.googleapis.com",
    "vpcaccess.googleapis.com",
    "cloudaicompanion.googleapis.com",
    "discoveryengine.googleapis.com",
    "iap.googleapis.com",
    "geminidataanalytics.googleapis.com"
  ]
}

resource "google_project_service" "project" {
  for_each = toset(local.gcp_apis)

  project = var.project_id
  service = each.value
}


module "bigquery" {
  source  = "terraform-google-modules/bigquery/google"
  version = "10.2.0"

  project_id   = var.project_id
  dataset_id   = "knowledge_base"
  dataset_name = "knowledge base"
  description  = "knowledge base for co-browsing agent"
  location     = var.region

  external_tables = [{
    table_id                  = "cases_sheet",
    description               = "list of throubleshooting cases to get from a google sheet",
    autodetect                = false,
    source_format             = "GOOGLE_SHEETS",
    ignore_unknown_values     = true,
    compression               = "NONE",
    csv_options               = null,
    hive_partitioning_options = null,
    max_bad_records           = 1,
    schema = jsonencode([
      {
        "name" : "product",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "google cloud product name"
      },
      {
        "name" : "updated_at",
        "type" : "DATE",
        "mode" : "NULLABLE",
        "description" : "last update or added time for a case"
      },
      {
        "name" : "category",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "what kind of a case is it"
      },
      {
        "name" : "explanation",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "what is the problem"
      },
      {
        "name" : "solution",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "the step by step guide for solving an issue"
      }
    ]),
    google_sheets_options = {
      skip_leading_rows = 1
      range             = "knowledge_base"
    }
    source_uris = [
      "https://docs.google.com/spreadsheets/d/1y3ZBCgio05DUl--Vd_z-ORiv3JyVp_8gxTYPVBYqGOo/edit"
    ]
  }]
}

resource "google_artifact_registry_repository" "container-repo" {
  location      = "us-central1"
  repository_id = "containers"
  description   = "containers for cloud run"
  format        = "DOCKER"
  project       = var.project_id
}

module "service_accounts" {
  source     = "terraform-google-modules/service-accounts/google"
  version    = "~> 4.0"
  project_id = var.project_id

  prefix = "sa"
  names  = ["project"]
  project_roles = [
    "${var.project_id}=>roles/storage.objectUser",
    "${var.project_id}=>roles/discoveryengine.user",
    "${var.project_id}=>roles/logging.logWriter",
    "${var.project_id}=>roles/monitoring.metricWriter",
    "${var.project_id}=>roles/aiplatform.user",
    "${var.project_id}=>roles/cloudbuild.builds.builder",
    "${var.project_id}=>roles/artifactregistry.createOnPushWriter"
  ]
}