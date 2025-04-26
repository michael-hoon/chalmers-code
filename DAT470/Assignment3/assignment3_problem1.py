#!/usr/bin/env python3

from mrjob.job import MRJob

class MRMineral(MRJob):
    def mapper(self, _, line):
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

    def reducer(self, star_system, mineral_values):
        total_mineral_value = sum(mineral_values)
        yield star_system, int(total_mineral_value)


if __name__ == '__main__':
    MRMineral().run()