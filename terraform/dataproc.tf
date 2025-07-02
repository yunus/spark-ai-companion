
module "gcs_buckets_dataset" {
  source  = "terraform-google-modules/cloud-storage/google"
  version = "~> 11.0"
  project_id = var.project_id
  location   = var.region
  names      = ["dataset"]
  prefix     = "${var.project_id}-dataproc"
}

module "gcs_buckets" {
  source  = "terraform-google-modules/cloud-storage/google"
  version = "~> 11.0"
  project_id = var.project_id
  location   = var.region
  names      = ["temp", "staging"]
  prefix     = "${var.project_id}-dataproc-utility"

  lifecycle_rules = [{
    action    = { type = "Delete" }
    condition = { age = 180 }

    }]
}

module "service_accounts_dataproc" {
  source     = "terraform-google-modules/service-accounts/google"
  version    = "~> 4.1"
  project_id = var.project_id
  prefix     = "spark"
  names      = ["cluster-sa"]
  project_roles = [
    "${var.project_id}=>roles/editor",
    "${var.project_id}=>roles/dataproc.worker",
    "${var.project_id}=>roles/bigquery.admin"
  ]
}


resource "google_dataproc_autoscaling_policy" "asp" {
  policy_id = "dataproc-policy"
  location  = var.region
  project   = var.project_id

  worker_config {
    max_instances = 2
    min_instances = 2
  }
  secondary_worker_config {
    max_instances = 20
    min_instances = 0
  }

  basic_algorithm {
    cooldown_period = "120s"
    yarn_config {
      graceful_decommission_timeout = "10s"
      scale_up_factor               = 1.0
      scale_down_factor             = 1.0
    }
  }
}

resource "google_dataproc_cluster" "spark-cluster" {
  depends_on = [
    module.service_accounts_dataproc
  ]
  provider = google-beta
  count    = 1
  name     = "spark-cluster-${count.index + 1}"
  project  = var.project_id
  region   = var.region
  #graceful_decommission_timeout = "120s"
  labels = {
    "environment"   = "prod",
    "shared"        = "yes",
    "cluster_no"    = tostring(count.index + 1),
    "cluster_group" = "small_medium",
    "status"        = "active"
  }


  timeouts {
    create = "5m"
    update = "5m"
    delete = "5m"
  }

  cluster_config {

    autoscaling_config {
      policy_uri = google_dataproc_autoscaling_policy.asp.name
    }

    lifecycle_config {
      idle_delete_ttl = "1800s" # after 15 minute of idle time, the cluster is deleted
    }

    master_config {
      num_instances = 1
      machine_type  = "n2-standard-4"
      disk_config {
        boot_disk_type    = "pd-balanced"
        boot_disk_size_gb = 500
        # num_local_ssds      = 2
        # local_ssd_interface = "nvme"
      }
    }

    worker_config {
      num_instances = 2
      machine_type  = "n2d-standard-8"
      disk_config {
        boot_disk_size_gb = 500
        boot_disk_type    = "pd-balanced"
        # num_local_ssds    = 2
      }
    }

    preemptible_worker_config {
      num_instances  = 0
      preemptibility = "SPOT"

      disk_config {
        boot_disk_type    = "pd-balanced"
        boot_disk_size_gb = 500
        # num_local_ssds    = 2
      }
      # instance_flexibility_policy {
      #   instance_selection_list {
      #     machine_types = ["n2-standard-4","n4-standard-4"]
      #     rank          = 1
      #   }
      #   # instance_selection_list {
      #   #   machine_types = ["n2-standard-4"]
      #   #   rank          = 2
      #   # }
      # }
    }


    # Override or set some custom properties
    software_config {
      image_version = "2.2.44-ubuntu22"
      override_properties = {
        "dataproc:dataproc.logging.stackdriver.enable"                    = "true",
        "dataproc:dataproc.logging.stackdriver.job.driver.enable"         = "true",
        "dataproc:dataproc.logging.stackdriver.job.yarn.container.enable" = "true",
        #"dataproc:efm.spark.shuffle"                                      = "primary-worker",
        "spark:spark.dataproc.enhanced.optimizer.enabled"         = "true",
        "spark:spark.dataproc.enhanced.execution.enabled"         = "true",
        "spark:spark.dynamicAllocation.cachedExecutorIdleTimeout" = "20m",
        #        "spark:spark.dynamicAllocation.executorIdleTimeout"              = "60s"
        "spark:spark.history.fs.logDirectory"                            = "gs://${module.gcs_buckets.buckets_map["temp"].id}/spark-cluster/spark-job-history"
        "spark:spark.eventLog.dir"                                       = "gs://${module.gcs_buckets.buckets_map["temp"].id}/spark-cluster/spark-job-history"
        "spark:spark.history.fs.gs.outputstream.type"                    = "FLUSHABLE_COMPOSITE"
        "yarn:yarn.nodemanager.remote-app-log-dir"                       = "gs://${module.gcs_buckets.buckets_map["temp"].id}/spark-cluster/yarn-logs"
        "dataproc:user-attribution.enabled"                              = "false"
        "capacity-scheduler:yarn.scheduler.capacity.resource-calculator" = "org.apache.hadoop.yarn.util.resource.DominantResourceCalculator"
        "spark:spark.metrics.executorMetricsSource.enabled"              = "true"
        "dataproc:pip.packages"                                          = "bigframes==1.27.0,memory_profiler==0.61.0"
        #"dataproc:dataproc.scheduler.max-concurrent-jobs"                 = "1"
        "dataproc:dataproc.components.deactivate" = "mysql hive-metastore hive hive-server2 "
        #"core:fs.defaultFS"                                              = "gs://${module.gcs_buckets.buckets_map["staging"].id}/corefs"
      }
      optional_components = ["JUPYTER", "DOCKER"]
    }

    temp_bucket    = module.gcs_buckets.buckets_map["temp"].id
    staging_bucket = module.gcs_buckets.buckets_map["staging"].id

    dataproc_metric_config {
      metrics {
        metric_source = "SPARK"
        metric_overrides = [

          "spark:executor:executor:diskBytesSpilled",
          "spark:executor:executor:memoryBytesSpilled",

          "spark:executor:executor:runTime",

          "spark:driver:BlockManager:memory.maxOffHeapMem_MB",
          "spark:driver:BlockManager:memory.maxOnHeapMem_MB",

          "spark:driver:ExecutorMetrics:JVMHeapMemory",
          "spark:driver:ExecutorMetrics:JVMOffHeapMemory",

          "spark:executor:ExecutorMetrics:JVMHeapMemory",
          "spark:executor:ExecutorMetrics:JVMOffHeapMemory",
          "spark:executor:ExecutorMetrics:MajorGCTime"
        ]
      }
      # metrics {
      #   metric_source = "SPARK_HISTORY_SERVER"
      # }
      metrics {
        metric_source = "YARN"
        metric_overrides = [
          "yarn:ResourceManager:ClusterMetrics:NumActiveNMs",
          "yarn:ResourceManager:QueueMetrics:running_0",
          "yarn:ResourceManager:QueueMetrics:running_60",
          "yarn:ResourceManager:QueueMetrics:running_300",
          "yarn:ResourceManager:QueueMetrics:running_1440",
          "yarn:ResourceManager:QueueMetrics:AppsSubmitted",
          "yarn:ResourceManager:QueueMetrics:AvailableMB",
          "yarn:ResourceManager:QueueMetrics:PendingContainers",
        ]
      }
      
    }

    #You can define multiple initialization_action blocks
    initialization_action {
      script      = "gs://goog-dataproc-initialization-actions-${var.region}/opsagent/opsagent_nosyslog.sh"
      timeout_sec = 500
    }

    gce_cluster_config {
      # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
      service_account = module.service_accounts_dataproc.service_account.email
      service_account_scopes = [
        "cloud-platform",
        "https://www.googleapis.com/auth/cloud.useraccounts.readonly",
        "https://www.googleapis.com/auth/devstorage.read_write",
        "https://www.googleapis.com/auth/logging.write",
      ]
      internal_ip_only = true
      
      #network    = "projects/${var.project_id}/global/networks/argolis-vpc"
      subnetwork = module.vpc.subnets_self_links[0]
      
      
      # metadata = {
      #   "SPARK_BQ_CONNECTOR_URL" = "gs://yunus-playground-dataproc-dataset/spark-3.5-bigquery-0.0.1-SNAPSHOT.jar"
      # }
    }

    endpoint_config {
      enable_http_port_access = "true"
    }


    # initialization_action {
    #   script      = "gs://${module.gcs_buckets.buckets_map["temp"].id}/enable-linux-container-executor.sh"
    #   timeout_sec = 500
    # }
  }
}