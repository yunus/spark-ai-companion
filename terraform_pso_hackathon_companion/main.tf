
module "project-services" {
  source  = "terraform-google-modules/project-factory/google//modules/project_services"
  version = "~> 18.0"

  project_id                  = var.project_id


  activate_apis = [
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "bigquery.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "containerregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "dataform.googleapis.com",
    "aiplatform.googleapis.com",
    "workflows.googleapis.com",
    "essentialcontacts.googleapis.com",
    "dataproc.googleapis.com",
    "composer.googleapis.com",
    "vpcaccess.googleapis.com",
    "cloudaicompanion.googleapis.com"
  ]
}

module "service_accounts" {
  source        = "terraform-google-modules/service-accounts/google"
  version       = "~> 4.0"
  project_id    = var.project_id

  prefix        = "sa"
  names         = ["default"]
  project_roles = [
    "${var.project_id}=>roles/admin",
  ]
}

module "project-sandbox-iam-bindings" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.1"

  projects = [var.project_id]
  mode     = "additive"

  bindings = {
    "roles/admin" = [
      "user:prabhaarya@google.com",
      "user:ktchana@google.com",
      "user:isiroshtan@google.com"
    ]
  }
}

module "vpc" {
  source  = "terraform-google-modules/network/google"
  version = "~> 11.1"
  depends_on= [module.project-services]

  project_id                             = var.project_id
  network_name                           = "ai-vpc"
  routing_mode                           = "GLOBAL"
  delete_default_internet_gateway_routes = true

  subnets = [
    {
      subnet_name           = "ai-subnet"
      subnet_ip             = "10.164.0.0/20"
      subnet_region         = var.region
      subnet_private_access = "true"
    },
  ]

  secondary_ranges = {
    ai-subnet = [
      {
        range_name    = "ai-subnet-${var.region}-secondary-01"
        ip_cidr_range = "192.168.64.0/24"
      },
    ]
    
  }

  routes = [
    {
      name              = "egress-internet"
      description       = "route through IGW to access internet"
      destination_range = "0.0.0.0/0"
      next_hop_internet = "true"
    },
  ]


  ingress_rules = [
    {
      name        = "ai-allow-icmp"
      description = "Allow icmp anywhere"
      direction   = "INGRESS"
      destination_ranges = [
        "0.0.0.0/0",
      ]
      source_ranges = [
        "0.0.0.0/0",
      ]
      allow = [{
        protocol = "icmp"
      }]

    },
    {
      name          = "ai-allow-internal"
      description   = "Allow internal traffic"
      direction     = "INGRESS"
      source_ranges = ["10.128.0.0/9"]
      destination_ranges = [
        "0.0.0.0/0",
      ]
      allow = [{
        protocol = "tcp"
        ports    = ["0-65535"]
        }, {
        protocol = "udp"
        ports    = ["0-65535"]
        }, {
        protocol = "icmp"
        }
      ]
    },
    {
      name          = "ai-allow-ssh"
      description   = "Allow ssh from anywhere"
      direction     = "INGRESS"
      source_ranges = ["0.0.0.0/0"]
      destination_ranges = [
        "0.0.0.0/0",
      ]
      allow = [{
        protocol = "tcp"
        ports    = ["22"]
      }]

    }

  ]
}

module "cloud_router" {
  source  = "terraform-google-modules/cloud-router/google"
  version = "~> 7.0"
  name    = "r-${var.region}"
  project = var.project_id
  network = module.vpc.network_name
  region  = var.region

  nats = [{
    name                               = "nat-${var.region}"
    nat_ip_allocate_option             = "AUTO_ONLY"
    source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
    }
  ]
}

