from pipeline import Pipeline

if __name__ == '__main__':
    p = Pipeline('workflow', spec='pipeline.yml')
    p.run()
    p.print_summary()
