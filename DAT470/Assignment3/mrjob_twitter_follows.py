 #!/usr/bin/env python3

from mrjob.job import MRJob
from mrjob.step import MRStep

class MRJobTwitterFollows(MRJob):
    # The final (key,value) pairs returned by the class should be
    # 
    # yield ('most followed id', ???)
    # yield ('most followed', ???)
    # yield ('average followed', ???)
    # yield ('count follows no-one', ???)
    #
    # You will, of course, need to replace ??? with a suitable expression
    # def mapper(self, _, line):
    #     if not line.strip():
    #         return
    #     parts = line.strip().split(':')
    #     if len(parts) != 2:
    #         return
    #     user_id = parts[0].strip()
    #     followed = parts[1].strip()

    #     if followed:
    #         followed_ids = [f_id.strip() for f_id in followed.split(',')]
    #         followed_count = len(followed_ids)
    #     else:
    #         followed_count = 0

    #     yield 'max', (followed_count, user_id)
    #     yield 'sum', followed_count
    #     yield 'total_users', 1
    #     if followed_count == 0:
    #         yield 'zero_count', 1

    # def reducer_aggregate(self, key, values):
    #     if key == 'max':
    #         max_count = -1
    #         max_id = None
    #         for count, user_id in values:
    #             if count > max_count or (count == max_count and user_id < max_id):
    #                 max_count = count
    #                 max_id = user_id
    #         yield 'aggregate', ('max', max_count, max_id)
    #     elif key == 'sum_counts':
    #         total = sum(values)
    #         yield 'aggregate', ('sum_counts', total)
    #     elif key == 'total_users':
    #         total_users = sum(1 for _ in values)
    #         yield 'aggregate', ('total_users', total_users)
    #     elif key == 'zero_count':
    #         zero_total = sum(1 for _ in values)
    #         yield 'aggregate', ('zero_count', zero_total)

    # def reducer_finalize(self, key, values):
    #         max_count = 0
    #         max_id = None
    #         sum_counts = 0
    #         total_users = 0
    #         zero_count = 0

    #         for value in values:
    #             metric_type = value[0]
    #             if metric_type == 'max':
    #                 _, current_max_count, current_max_id = value
    #                 if (current_max_count > max_count) or (current_max_count == max_count and current_max_id < max_id):
    #                     max_count = current_max_count
    #                     max_id = current_max_id
    #             elif metric_type == 'sum_counts':
    #                 sum_counts = value[1]
    #             elif metric_type == 'total_users':
    #                 total_users = value[1]
    #             elif metric_type == 'zero_count':
    #                 zero_count = value[1]

    #         average = sum_counts / total_users if total_users != 0 else 0

    #         yield ('most followed id', max_id)
    #         yield ('most followed', max_count)
    #         yield ('average followed', round(average, 5))
    #         yield ('count follows no-one', zero_count)

    # def steps(self):
    #     return [
    #         MRStep(
    #             mapper=self.mapper,
    #             reducer=self.reducer_aggregate
    #         ),
    #         MRStep(
    #             reducer=self.reducer_finalize
    #         )
    #     ]

    def steps(self):
        return [
            MRStep(mapper=self.mapper_extract_follows,
            reducer=self.reducer_collect_stats),
            MRStep(reducer=self.reducer_compute_final)
        ]
    def mapper_extract_follows(self, _, line):
        parts = line.strip().split(':')
        if len(parts) != 2:
            return

        user = parts[0].strip()
        followees_str = parts[1]
        followees = followees_str.strip().split()
        follow_count = len(followees)
        yield "stats", (user, follow_count)

    def reducer_collect_stats(self, key, values):
        max_user = None
        max_count = 0
        total_follows = 0
        total_users = 0
        num_zero_followers = 0
        for user, count in values:
            total_users += 1
            total_follows += count
            if count == 0:
                num_zero_followers += 1
            if count > max_count:
                max_count = count
                max_user = user
        yield None, (max_user, max_count, total_users, total_follows, num_zero_followers)
    
    def reducer_compute_final(self, _, values):
        # Only one group passed here
        for max_user, max_count, total_users, total_follows, num_zero_followers in values:
            avg_follows = total_follows / total_users if total_users > 0 else 0
            yield "most followed id", max_user
            yield "most followed", max_count
            yield "average followed", round(avg_follows, 5)
            yield "count follows no-one", num_zero_followers

if __name__ == '__main__':
    MRJobTwitterFollows.run()