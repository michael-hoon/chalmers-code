#!/usr/bin/env python3

import time
import argparse
import findspark
findspark.init()
from pyspark import SparkContext

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = \
                                    'Compute Twitter follows.')
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
            follow_count = 0
        else:
            followed_part = parts[1].strip()
            follow_count = len(followed_part.split())
        is_zero = 1 if follow_count == 0 else 0
        return (user_id, follow_count, is_zero)

    parsed_lines = lines.map(parse_line)
    parsed_lines.cache()

    # max follows & user id
    max_follows = parsed_lines.map(lambda x: (x[1], x[0])).reduce(lambda a, b: a if a[0] > b[0] else b)
    max_count = max_follows[0]
    max_id = max_follows[1]

    # average follows
    sum_counts = parsed_lines.map(lambda x: (x[1], 1)).reduce(lambda a, b: (a[0]+b[0], a[1]+b[1]))
    total_follows, total_users = sum_counts
    average = total_follows / total_users if total_users != 0 else 0.0

    # number of users who follow no-one
    zero_count = parsed_lines.map(lambda x: x[2]).sum()
    
    end = time.time()
    
    total_time = end - start

    # the first ??? should be the twitter id
    print(f'max follows: {max_id} follows {max_count}')
    print(f'users follow on average: {average:.5f}')
    print(f'number of user who follow no-one: {int(zero_count)}')
    print(f'num workers: {args.num_workers}')
    print(f'total time: {total_time}')

    sc.stop()