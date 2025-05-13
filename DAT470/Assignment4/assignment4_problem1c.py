#!/usr/bin/env python3

import time
import argparse
import findspark
findspark.init()
from pyspark import SparkContext

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = \
                                    'Compute Twitter followers.')
    parser.add_argument('-w','--num-workers',default=1,type=int,
                            help = 'Number of workers')
    parser.add_argument('filename',type=str,help='Input filename')
    args = parser.parse_args()

    start = time.time()
    sc = SparkContext(master = f'local[{args.num_workers}]')

    lines = sc.textFile(args.filename)

    # fill in your code here
    def parse_line(line):
        parts = line.strip().split(':')
        user_id = parts[0].strip()
        if len(parts) != 2:
            followed_users = []
        else:
            followed_part = parts[1].strip()
            followed_users = followed_part.split()
        return (user_id, followed_users)

    parsed_lines = lines.map(parse_line)
    parsed_lines.cache()

    # follower counts for each user
    follower_counts = parsed_lines.flatMap(lambda x: [(followed, 1) for followed in x[1]]).reduceByKey(lambda a, b: a + b)

    # collect all user_ids
    all_user_ids = parsed_lines.flatMap(lambda x: [x[0]] + x[1]).distinct()
    all_user_ids.cache()

    # join follower counts with all user_ids
    all_users_pair = all_user_ids.map(lambda user_id: (user_id, None))
    followers_joined = all_users_pair.leftOuterJoin(follower_counts)
    user_follower_counts = followers_joined.mapValues(lambda x: x[1] if x[1] is not None else 0)

    # max followers & user id
    max_follows = user_follower_counts.reduce(lambda a, b: a if a[1] > b[1] else b)
    max_user, max_count = max_follows

    # average followers
    sum_counts = user_follower_counts.map(lambda x: x[1]).sum()
    total_users = all_user_ids.count()
    average = sum_counts / total_users if total_users != 0 else 0.0

    # number of users who follow no-one
    zero_count = user_follower_counts.filter(lambda x: x[1] == 0).count()
    
    end = time.time()
    
    total_time = end - start

    # the first ??? should be the twitter id
    print(f'max followers: {max_user} has {max_count} followers')
    print(f'followers on average: {average:.5f}')
    print(f'number of user with no followers: {int(zero_count)}')
    print(f'num workers: {args.num_workers}') 
    print(f'total time: {total_time:.5f} seconds')

    sc.stop()