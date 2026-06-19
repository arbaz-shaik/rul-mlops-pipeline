import mlflow
from sklearn.datasets import load_iris

# Connect to MLflow server
mlflow.set_tracking_uri("http://localhost:5000")

# Load model from registry using alias
model = mlflow.pyfunc.load_model(
    "models:/toy-model@champion"
)

# Load iris dataset
iris = load_iris()

# Take one sample
sample = iris.data[:1]

# Predict
prediction = model.predict(sample)

# Print prediction
print("Prediction:", prediction)