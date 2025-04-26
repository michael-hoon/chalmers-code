#!/usr/bin/env python3

from mrjob.job import MRJob
from mrjob.step import MRStep
import heapq

class MRMineralTopK(MRJob):
    def configure_args(self):
        super(MRMineralTopK, self).configure_args()
        self.add_passthru_arg('-k', type=int, default=10,
                              help='Number of top k star systems to return')
    def mapper_aggregate(self, _, line):
        columns = line.split(',')
        if columns[0] == 'Constellation': # skipping header row
            return
        constellation = columns[0]
        star = columns[1]
        mineral_str = columns[5]
        try:
            mineral_value = float(mineral_str)
        except ValueError:
            return
        
        if star == "Prime":
            star_system = constellation
        else:
            star_system = f"{star} {constellation}"
        yield f'"{star_system}"', mineral_value

    def reducer_sum(self, star_system, mineral_values):
        total_mineral_value = sum(mineral_values)
        yield star_system, int(total_mineral_value)

    def mapper_collect(self, star_system, total_mineral_value):
        yield None, (int(total_mineral_value), star_system)

    def reducer_top_k(self, _, values):
        k = self.options.k
        top_k = heapq.nlargest(k, values)
        for total_mineral_value, star_system in top_k:
            yield star_system, int(total_mineral_value)

    def steps(self):
        return [
            MRStep(mapper=self.mapper_aggregate,
                   reducer=self.reducer_sum),
            MRStep(mapper=self.mapper_collect,
                   reducer=self.reducer_top_k)
        ]

if __name__ == '__main__':
    MRMineralTopK().run()