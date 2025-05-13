import time
import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import udf, col, to_date, year
from pyspark.sql.types import IntegerType
import pandas as pd
import numpy as np
import sys

@udf(returnType=IntegerType())
def jdn(dt):
    """
    Computes the Julian date number for a given date.
    Parameters:
    - dt, datetime : the Gregorian date for which to compute the number

    Return value: an integer denoting the number of days since January 1, 
    4714 BC in the proleptic Julian calendar.
    """
    y = dt.year
    m = dt.month
    d = dt.day
    if m < 3:
        y -= 1
        m += 12
    a = y//100
    b = a//4
    c = 2-a+b
    e = int(365.25*(y+4716))
    f = int(30.6001*(m+1))
    jd = c+d+e+f-1524
    return jd

    
# you probably want to use a function with this signature for computing the
# simple linear regression with least squares using applyInPandas()
# key is the group key, df is a Pandas dataframe
# should return a Pandas dataframe
def lsq(key,df):
    # raise NotImplementedError
    if len(df) < 2:
        return pd.DataFrame()
    x = df['JDN'].values.astype(np.float64)
    y = df['TAVG'].values.astype(np.float64)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    if denominator == 0:
        beta = 0.0
    else:
        beta = numerator / denominator
    name = df['NAME'].iloc[0] if 'NAME' in df.columns and not df.empty else ''
    return pd.DataFrame({'STATION': [str(key)], 'NAME': [str(name)], 'BETA': [float(beta)]})

if __name__ == '__main__':
    # do not change the interface
    parser = argparse.ArgumentParser(description = \
                                    'Compute climate data.')
    parser.add_argument('-w','--num-workers',default=1,type=int,
                            help = 'Number of workers')
    parser.add_argument('filename',type=str,help='Input filename')
    args = parser.parse_args()

    start = time.time()

    # this bit is important: by default, Spark only allocates 1 GiB of memory 
    # which will likely cause an out of memory exception with the full data
    spark = SparkSession.builder \
            .master(f'local[{args.num_workers}]') \
            .config("spark.driver.memory", "128g") \
            .getOrCreate()
    
    # read the CSV file into a pyspark.sql dataframe and compute the things you need

    start_reading = time.time()

    df = spark.read.csv(args.filename, header=True, inferSchema=True)
    df = df.withColumn("TAVG", (F.col("TMAX") + F.col("TMIN")) / 2) \
              .filter(F.col("TMAX").isNotNull() & F.col("TMIN").isNotNull()) \
              .withColumn("JDN", jdn(col("DATE"))) \
              .withColumn("DATE", to_date(col("DATE"), "yyyy-MM-dd")) \
              .cache()
    
    reading_time = time.time() - start_reading
    print(f'Time taken to read data: {reading_time:.2f} seconds')
    
    # linear regression
    start_processing = time.time()
    
    stations_regression = df.groupBy('STATION').applyInPandas(lsq, schema='STATION string, NAME string, BETA double')
    stations_regression.cache()

    # top 5 slopes are printed here
    top_slopes = stations_regression.orderBy(F.desc('BETA')).limit(5).collect()
    # replace None with your dataframe, list, or an appropriate expression
    # replace STATIONCODE, STATIONNAME, and BETA with appropriate expressions
    print('Top 5 coefficients:')
    for row in top_slopes:
        print(f'{row.STATION} at {row.NAME} BETA={row.BETA:0.3e} °F/d')

    # replace None with an appropriate expression
    positive_slopes = stations_regression.filter(col('BETA') > 0).count()
    total_slopes = stations_regression.count()
    fraction_positive = positive_slopes / total_slopes if total_slopes > 0 else 0.0
    print('Fraction of positive coefficients:')
    print(f'{fraction_positive:0.3f}')

    # Five-number summary of slopes, replace with appropriate expressions
    quantiles = stations_regression.approxQuantile('BETA', [0.0, 0.25, 0.5, 0.75, 1.0], 0.01)
    beta_min, beta_q1, beta_median, beta_q3, beta_max = quantiles if quantiles else [0.0, 0.0, 0.0, 0.0, 0.0]
    print('Five-number summary of BETA values:')
    print(f'beta_min {beta_min:0.3e}')
    print(f'beta_q1 {beta_q1:0.3e}')
    print(f'beta_median {beta_median:0.3e}')
    print(f'beta_q3 {beta_q3:0.3e}')
    print(f'beta_max {beta_max:0.3e}')

    # Here you will need to implement computing the decadewise differences 
    # between the average temperatures of 1910s and 2010s

    # There should probably be an if statement to check if any such values were 
    # computed (no suitable stations in the tiny dataset!)

    # Note that values should be printed in celsius
    # Replace None with an appropriate expression
    # Replace STATION, STATIONNAME, and TAVGDIFF with appropriate expressions

    df_decade = df.withColumn("YEAR", year(col("DATE"))) \
        .withColumn("DECADE", (F.floor(col("YEAR") / 10) * 10).cast("integer")) \
            .filter(col("DECADE").isin([1910, 2010]))

    station_decade_avg = df_decade.groupBy("STATION", "NAME", "DECADE") \
        .agg(F.avg("TAVG").alias("AVG_TAVG")) \
    
    pivoted_df = station_decade_avg.groupBy("STATION", "NAME") \
        .pivot("DECADE", [1910, 2010]) \
        .agg(F.first("AVG_TAVG")) 

    pivoted_df = pivoted_df.filter(col('1910').isNotNull() & col('2010').isNotNull())
    
    if pivoted_df.count() > 0:
        differences = pivoted_df.withColumn("TAVGDIFF_CELCIUS", (col("2010") - col("1910")) * 5.0 / 9.0)
        differences.cache()

        top_differences = differences.orderBy(F.desc('TAVGDIFF_CELCIUS')).limit(5).collect()

        print('Top 5 differences:')
        for row in top_differences:
            print(f'{row.STATION} at {row.NAME} difference {row.TAVGDIFF_CELCIUS:0.1f} °C)')

        positive_differences = differences.filter(differences['TAVGDIFF_CELCIUS'] > 0).count()
        total_differences = differences.count()
        fraction_positive_differences = positive_differences / total_differences if total_differences > 0 else 0.0
        # replace None with an appropriate expression
        print('Fraction of positive differences:')
        print(f'{fraction_positive_differences:0.3f}')

        quantiles_diff = differences.approxQuantile('TAVGDIFF_CELCIUS', [0.0, 0.25, 0.5, 0.75, 1.0], 0.01)
        tdiff_min, tdiff_q1, tdiff_median, tdiff_q3, tdiff_max = quantiles_diff if quantiles_diff else [0.0, 0.0, 0.0, 0.0, 0.0]
    
    else:
        print('Top 5 differences:')
        print('No suitable stations found for the specified decades.')
        print('Fraction of positive differences:')
        print('0.000')
        tdiff_min, tdiff_q1, tdiff_median, tdiff_q3, tdiff_max = 5*[0.0]

    # Five-number summary of temperature differences, replace with appropriate expressions
    print('Five-number summary of decade average difference values:')
    print(f'tdiff_min {tdiff_min:0.1f} °C')
    print(f'tdiff_q1 {tdiff_q1:0.1f} °C')
    print(f'tdiff_median {tdiff_median:0.1f} °C')
    print(f'tdiff_q3 {tdiff_q3:0.1f} °C')
    print(f'tdiff_max {tdiff_max:0.1f} °C')

    end_processing = time.time()
    processing_time = end_processing - start_processing
    print(f'Time taken to process data: {processing_time:.2f} seconds')

    # Add your time measurements here
    total_time = time.time() - start
    # It may be interesting to also record more fine-grained times (e.g., how 
    # much time was spent computing vs. reading data)
    print(f'num workers: {args.num_workers}')
    print(f'total time: {total_time:0.1f} s')
