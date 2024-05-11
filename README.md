
# Pipeline-tool

## Simple tool for running pipelines

:white_check_mark: - Run pipelines locally.

:white_check_mark: - Simple yaml representation of pipeline.

:white_check_mark: - Use Cron for simple scheduling of pipeline runs.

## Usage

Clone the repo, install the required packages listed in requirements.txt and copy the _pipeline.py_ file in to your project.

### Run a pipeline from the terminal

```python
python3 pipeline.py -f pipeline.yml
```

### Run a pipeline from a python script

```python
from pipeline import Pipeline

if __name__ == '__main__':
    p = Pipeline('workflow', spec='pipeline.yml')
    p.run()
    p.print_summary()
```

### Schedule a pipeline run

Example, run a pipeline at 12am every day. Add the following as a cronjob by editing crontab with `crontab -e`.
```bash
0 12 * * * python3 /path/to/pipeline-tool/pipeline.py -f /path/to/pipeline/file.yml
```
