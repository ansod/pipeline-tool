from __future__ import annotations

from enum import Enum
from typing import List
import subprocess
from multiprocessing import Process, Queue
import time
import argparse

import yaml


class Result(Enum):
    SUCCESS = 0
    ERROR = 1
    NA = 2


class PipelineGraph:
    # TODO: Implement this
    pass


class Summary:
    def __init__(self, result: Result, time: float, stdout: str = '', stderr: str = '') -> None:
        self.result = result
        self.time = time
        self.stdout = stdout
        self.stderr = stderr


class PipelineObject:
    def __init__(self, name) -> None:
        self.name = name


class PipelineObjectFactory:
    def create_pipeline_object(k, spec) -> PipelineObject:
        if k == 'concurrent':
            return Concurrent.create(spec)

        return Job(k, spec=spec)


class Job(PipelineObject):
    def __init__(self, name, spec) -> None:
        super().__init__(name)
        self.spec = spec
        self.ctx = self.spec['context'] if 'context' in spec else '.'
        self.cmd = self.spec['run']

        self.summary: Summary = Summary(Result.NA, 0.0, 'Not available.')

    def run(self, ret_queue=None, i=None, verbose=False, cancel=False) -> None:
        if cancel:
            self.summary = Summary(Result.NA, 0, 'Not available.')
            return

        t_start = time.time()
        ret = subprocess.run(
            self.cmd,
            shell=True,
            cwd=self.ctx,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True)
        t_fin = time.time()

        if verbose:
            print(f'#### {self.name} output:')
            print(f'## Stdout:\n{ret.stdout}')
            print(f'## Stderr:\n{ret.stderr}')

        res = Result.SUCCESS if ret.returncode == 0 else Result.ERROR

        self.summary = Summary(res, t_fin - t_start, ret.stdout, ret.stderr)
        if ret_queue:
            ret_queue.put((i, self.summary))

    def print_summary(self, spaces=0):
        indent = " "*spaces
        if self.summary.result == Result.SUCCESS:
            print(f'{indent}\u2705 {self.name} succeeded after {self.summary.time:.2f}s.')
        elif self.summary.result == Result.NA:
            print(f'{indent}\u26D4 {self.name} was not run due to fail-fast argument.')
        else:
            print(f'{indent}\u274c {self.name} failed after {self.summary.time:.2f}s.')


class Concurrent(PipelineObject):
    def __init__(self, jobs) -> None:
        super().__init__('Concurrent')
        self.jobs: List[Job] = jobs

        self.summary: Summary = Summary(Result.NA, 0, 'Not available.')

    def run(self, cancel=False, verbose=False) -> None:
        if cancel:
            for j in self.jobs:
                j.run(cancel=cancel)
            self.summary = Summary(Result.NA, 0, 'Not available.')
            return

        ret_queue = Queue()
        procs = [Process(target=j.run, args=(ret_queue, i, verbose)) for i, j in enumerate(self.jobs)]
        for p in procs:
            p.start()
        for p in procs:
            p.join()

        summaries = []
        while not ret_queue.empty():
            resp = ret_queue.get()
            self.jobs[resp[0]].summary = resp[1]
            summaries.append(resp[1])

        self.collect(summaries)

    def collect(self, summaries) -> None:
        t_max = max(s.time for s in summaries)
        res = Result.ERROR if Result.ERROR in [s.result for s in summaries] else Result.SUCCESS
        self.summary = Summary(res, t_max)

    def print_summary(self, spaces=0):
        indent = " "*spaces
        if self.summary.result == Result.SUCCESS:
            print(f'{indent}\u2705 Concurrent jobs succeeded after {self.summary.time:.2f}s.')
        elif self.summary.result == Result.NA:
            print(f'{indent}\u26D4 Concurrent jobs were not run due to fail-fast argument.')
        else:
            print(f'{indent}\u274c Some Concurrent job(s) failed after {self.summary.time:.2f}s.')

        for job in self.jobs:
            job.print_summary(spaces=2)

    @staticmethod
    def create(spec) -> Concurrent:
        jobs = list()
        for job in spec:
            obj = Job(job, spec[job])
            jobs.append(obj)

        return Concurrent(jobs)


class Pipeline:
    def __init__(self, name, spec=None) -> None:
        self.name = name
        self._pipline_objects: List[PipelineObject] = list()
        self.config = dict()
        if spec:
            # Read jobs from yaml file
            with open(spec, 'r') as yml:
                try:
                    pipeline_spec = yaml.safe_load(yml)
                    self.yml_to_pipeline(pipeline_spec)
                except yaml.YAMLError as e:
                    print(e)

        self.summary: Summary = Summary(Result.NA, 0.0, 'Not available.')

    def run(self) -> Result:
        t_total = 0
        res = Result.SUCCESS
        cancel = False
        verbose = True if self.config.get('verbose') else False

        for item in self._pipline_objects:
            item.run(cancel=cancel, verbose=verbose)
            t_total += item.summary.time
            if item.summary.result == Result.ERROR:
                res = Result.ERROR
                if self.config.get('fail-fast'):
                    cancel = True

        self.summary = Summary(res, t_total)

    def yml_to_pipeline(self, spec):
        assert 'pipeline' in spec

        if 'config' in spec['pipeline']:
            self.config = spec['pipeline']['config']
            del spec['pipeline']['config']

        for k in spec['pipeline']:
            obj = PipelineObjectFactory.create_pipeline_object(k, spec['pipeline'][k])
            self._pipline_objects.append(obj)

    def print_summary(self):
        print('=== Summary ===')
        if self.summary.result == Result.SUCCESS:
            print(f'\u2705: All jobs completed successfully. \u23F1 Total time: {self.summary.time:.2f}s.')
            print('Jobs:')
            for item in self._pipline_objects:
                item.print_summary(spaces=1)
        else:
            print(f'\u274c: Some jobs failed. \u23F1 Total time: {self.summary.time:.2f}s.')
            print('Jobs:')
            for item in self._pipline_objects:
                item.print_summary(spaces=1)
        print("===============")

    def get_graph(self) -> PipelineGraph:
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                                    prog='Pipeline-tool', 
                                    description='Helps you run custom pipelines locally.')
    parser.add_argument('-f', '--file', help='the yaml file specifying your pipeline.')
    args = parser.parse_args()

    p = Pipeline('workflow', spec=args.file)
    p.run()
    p.print_summary()
