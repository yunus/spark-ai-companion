import sys
from typing import Tuple
import time

from pyspark import RDD
from pyspark.sql import SparkSession
from pyspark.sql.functions import split, explode, col, count
#from helper_modules import explain_dataframe




if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: sort <file>", file=sys.stderr)
        sys.exit(-1)



    with SparkSession.builder.appName("PythonSort").getOrCreate() as spark:

        print("------------ reading the file")
        spark.sparkContext.setJobDescription("read file")
        df = spark.read.text(sys.argv[1])

        # split every line and word with space and then filter words that are shorter than 3 characters
        spark.sparkContext.setJobDescription("split words")
        df = df.select(explode(split(df.value, "[,\\s]+")).alias("word"))

        spark.sparkContext.setJobDescription("groupby count")
        df_with_groupby = df.groupBy("word").agg(count("*").alias("count"))

        # sort the dataframe by count in descending order
        spark.sparkContext.setJobDescription("sort by counted words")
        df_words_sorted = df_with_groupby.sort("count", ascending=False)
        print("------------ First Count")
        df_words_sorted.explain()
        df_words_sorted.printSchema()
        cached_df_words_sorted = df_words_sorted.cache()
        spark.sparkContext.setJobDescription("show action with groupby/cache words")

        spark.sparkContext.setJobDescription("show action on top 10 words")
        cached_df_words_sorted.show(10, True)
        print('Showing Profiles')
        # spark.sparkContext.show_profiles()
        # print("showed profiles")

        print(f"++++ Number of partitions {cached_df_words_sorted.rdd.getNumPartitions()}")
        #explain_dataframe.explain_a_dataframe(cached_df_words_sorted)

        spark.sparkContext.setJobDescription("count action on cached words")
        count = cached_df_words_sorted.count()
        print(f"count: {count}")
        print("------------ Second count")
        spark.sparkContext.setJobDescription("filter words more than 1000 counts")
        df_words_sorted_filtered = cached_df_words_sorted.filter("count > 1000")
        df_words_sorted_filtered.explain()
        spark.sparkContext.setJobDescription("countwords more than 1000 occurences")
        count = df_words_sorted_filtered.count()
        print(f"count: {count}")
