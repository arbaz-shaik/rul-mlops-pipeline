from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import mlflow 
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV

#load the dataset
iris = load_iris()
X, y = iris.data, iris.target

#clean data, not reuired for this dataset

#feature engineering not required for this dataset

#splitiing the data

x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)








# Hyperparameter Tuning
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 10, None],
    'min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(
    estimator=RandomForestClassifier(random_state=42),
    param_grid=param_grid,
    cv=5,
    scoring='accuracy'
)

grid_search.fit(x_train, y_train)

best_model = grid_search.best_estimator_

print("Best Parameters:", grid_search.best_params_)

#predicting the model
model = best_model

y_pred = model.predict(x_test)


#accuracy
accuracy = accuracy_score(y_test, y_pred)







#save the model


#mlflow logging
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Iris_Classification")
with mlflow.start_run():
    mlflow.log_param("n_estimators", grid_search.best_params_['n_estimators'])
    mlflow.log_param("max_depth", grid_search.best_params_['max_depth'])
    mlflow.log_param("min_samples_split", grid_search.best_params_['min_samples_split'])
    mlflow.log_metric("accuracy", accuracy)
    mlflow.sklearn.log_model(model, "Iris_Classifier_Model", registered_model_name="toy-model")