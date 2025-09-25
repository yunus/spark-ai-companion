#!/bin/zsh


gcloud dataproc jobs submit pyspark \
    --project=pso-hackathon-companion \
    --region=europe-west4 \
    --cluster spark-cluster-1 \
    --bucket="pso-hackathon-companion-dataproc-utility-temp" \
    --async \
    --properties spark.sql.files.maxPartitionBytes=100m,spark.dynamicAllocation.executorAllocationRatio=0.5,spark.executor.memoryOverheadFactor=0.4 \
   sort.py -- gs://pso-hackathon-companion-dataproc-dataset/EpisodeAgents.csv

