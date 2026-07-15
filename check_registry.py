import mlflow
c = mlflow.MlflowClient()
versions = c.search_model_versions("name='RULModel'")
if not versions:
    print("NO RULModel VERSIONS FOUND")
for v in versions:
    print("found:", v.name, "v" + v.version, v.current_stage, v.status)
