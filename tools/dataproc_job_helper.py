"""'dataproc job helper' tool for Spark UI analyzer agent"""

import logging
from google.cloud import dataproc_v1 as dataproc
from google.cloud import storage

logger = logging.getLogger(__name__)

def get_dataproc_job_output(project_id: str, region: str, job_id: str):
    """
    Retrieves the stdout output of a Dataproc job.

    Args:
        project_id (str): Your Google Cloud project ID.
        region (str): The Dataproc region where the job was run.
        job_id (str): The unique ID of your Dataproc job.

    Returns:
        str: The content of the job's stdout, or None if the output
             could not be retrieved.
    """
    # Create a Dataproc client
    job_client = dataproc.JobControllerClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    try:
        # Get the job resource to find the output URI
        request = dataproc.GetJobRequest(
            project_id=project_id,
            region=region,
            job_id=job_id,
        )
        job = job_client.get_job(request=request)

        # The driver output is stored in GCS
        output_uri = job.driver_output_resource_uri

        if not output_uri:
            print("Job has no output URI.")
            return None

        print(f"Job output URI: {output_uri}")

        # Parse the GCS URI to get the bucket name and the directory prefix
        storage_client = storage.Client()
        path_parts = output_uri[5:].split("/", 1)
        bucket_name = path_parts[0]
        prefix = ("/").join(path_parts[1].split("/")[:-1])
        
        print(f"Bucket Name: {bucket_name}")
        print(f"Prefix: {prefix}")


        # Ensure the prefix ends with a '/' to only list files inside the "directory"
        if not prefix.endswith('/'):
            prefix += '/'

        bucket = storage_client.bucket(bucket_name)

        # List all blobs (files) with the correct prefix
        blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
        
        full_output = []
        for blob in blobs:
            # Check if the blob name matches the expected format, e.g., 'driveroutput.000000000'
            if blob.name.startswith(prefix + "driveroutput."):
                content = blob.download_as_text()
                full_output.append(content)

        return "".join(full_output)

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# --- Example Usage ---
if __name__ == "__main__":
    # Replace with your own project, region, and job ID
    my_project_id = "ktchana-demo"
    my_region = "europe-west2"
    my_job_id = "1a8fadfcd06f46ab8d93ecc81f5625fe"

    job_output = get_dataproc_job_output(my_project_id, my_region, my_job_id)

    if job_output:
        print("--- Dataproc Job Output ---")
        print(job_output)
    else:
        print("Failed to retrieve job output.")