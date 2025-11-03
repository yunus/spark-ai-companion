terraform {
  backend "gcs" {
    bucket = "co-browsing-agent-utility"
    prefix = "terraform/state/demo"
  }
}