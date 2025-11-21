# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""'dataproc helper' tool for Spark UI analyzer agent"""

import json
import logging

import google.auth
import requests
from google.auth.transport.requests import Request as AuthRequest

logger = logging.getLogger(__name__)


def get_creds():
    credentials, proj_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = AuthRequest()
    credentials.refresh(auth_req)  # refresh token
    token_str = credentials.token  # prints token
    # print(credentials.expiry)
    return token_str, proj_id


def get_dataproc_cluster_list(project_id: str, region: str):
    """Get a list of Dataproc cluster from the input project using Dataproc Python SDK

    Args:
      project_id: Google Cloud project ID to get the list of Dataproc cluster
      region: GCP Region where the clusters are located

    Returns:
      A dict with "status" and (optional) "cluster_name" list.
    """

    access_token, _ = get_creds()
    functions_url = f"https://dataproc.googleapis.com/v1/projects/{project_id}/regions/{region}/clusters"
    headers_req = {"Authorization": "Bearer " + access_token}
    resp = requests.get(url=functions_url, headers=headers_req)
    clusters = json.loads(resp.content)

    cluster_names = [cluster["clusterName"] for cluster in clusters["clusters"]]
    return {"status": "ok", "cluster_names": cluster_names}


def get_dataproc_cluster_detatils(project_id: str, region: str, cluster_name: str):
    """Get details of a specific Dataproc cluster using Dataproc Python SDK

    Args:
      project_id: Google Cloud project ID where the cluster is located.
      region: GCP Region where the cluster is located.
      cluster_name: The name of the Dataproc cluster.

    Returns:
      A dict with "status" and (optional) "cluster_details" dictionary.
    """
    logger.info(f"fetching cluster details for cluster name: {cluster_name}")
    access_token, _ = get_creds()
    functions_url = f"https://dataproc.googleapis.com/v1/projects/{project_id}/regions/{region}/clusters/{cluster_name}"
    headers_req = {"Authorization": "Bearer " + access_token}
    resp = requests.get(url=functions_url, headers=headers_req)
    clusters = json.loads(resp.content)

    print(json.dumps(clusters, indent=2))
    if "clusterName" in clusters and clusters["clusterName"] == cluster_name:
        return {"status": "ok", "cluster_details": clusters}
    else:
        return {"status": "not found"}


# print(json.dumps(get_dataproc_cluster_list("ktchana-demo", "europe-west2"),indent=2))
# print(json.dumps(get_dataproc_cluster_detatils("ktchana-demo", "europe-west2", "ktchana-demo-dataproc"), indent=2))
