
# Pipeline-tool

## Simple tool for running pipelines

:white_check_mark: - Run pipelines locally.

:white_check_mark: - Simple yaml representation of pipeline.

:white_check_mark: - Use Cron for simple scheduling of pipeline runs.

## Usage

### Run a pipeline

```python
python3 pipeline.py -f pipeline.yml
```

### Schedule a pipeline run

1. Edit Crontab with `crontab -e`.
2. Add cronjob to Crontab.
   - `min hour day(month) month day(week) python3 /path/to/pipeline-tool/pipeline.py -f /path/to/pipeline/file.yml`.
   - Example: `0 12 * * * python3 /path/to/pipeline-tool/pipeline.py -f /path/to/pipeline/file.yml`.
        - This will run the pipeline at 12am each day of the week.
