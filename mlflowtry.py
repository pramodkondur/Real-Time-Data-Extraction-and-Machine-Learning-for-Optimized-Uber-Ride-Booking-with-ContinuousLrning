import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import time
from sqlalchemy import text
import mlflow.pyfunc
import pickle
import os

def mlflow_run():
    mlflow.set_tracking_uri("/Users/pramodkondur/PycharmProjects/UberEndtoEnd/mlruns/")

    # MLflow experiment setup
    mlflow.set_experiment("Uber Ride Prediction With Distance")

    # Database connection parameters
    username = 'root'
    password = 'expert789'
    host = 'localhost'
    port = '3306'
    database = 'uber'

    def read_data_mysql():
        # Create a database connection
        engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}')
        # Create a connection
        with engine.connect() as connection:
            # Execute the query
            result = connection.execute(text("SELECT * FROM uber_details"))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

        return df

    df1 = read_data_mysql()

    def data_processing(df):
        # Convert ride_request_time to proper datetime
        df['ride_request_time'] = pd.to_datetime(df['ride_request_date'] + ' ' + df['ride_request_time'])

        # Drop unnecessary columns
        df = df.drop(columns=['id', 'ride_reaching_time'])

        # Convert 'ride_time' to total seconds and then to minutes
        df['ride_time_seconds'] = pd.to_timedelta(df['ride_time']).dt.total_seconds()
        df['ride_time_minutes'] = df['ride_time_seconds'] / 60

        # Create 'ride_time_request_clean' by rounding the ride_request_time to the nearest hour
        df['ride_time_request_clean'] = df['ride_request_time'].dt.round('H').dt.time

        # Group by 'route_from', 'route_to', 'ride_request_date', 'ride_time_request_clean', and 'ride_type'
        grouped = df.groupby(['route_from', 'route_to', 'ride_request_date', 'ride_time_request_clean', 'ride_type'],
                             as_index=False).agg({
            'ride_price': 'mean',
            'ride_max_persons': 'mean',
            'ride_waiting_time': 'mean',
            'ride_time_minutes': 'mean'  # Use ride_time_minutes for time-related calculations
        })

        # Convert 'ride_request_date' to datetime (date only)
        grouped['ride_request_date'] = pd.to_datetime(grouped['ride_request_date'], format='%Y-%m-%d')

        # Convert 'ride_time_request_clean' to a string (if it's not already)
        grouped['ride_time_request_clean'] = grouped['ride_time_request_clean'].astype(str)

        # Combine 'ride_request_date' and 'ride_time_request_clean'
        grouped['ride_datetime'] = pd.to_datetime(
            grouped['ride_request_date'].astype(str) + ' ' + grouped['ride_time_request_clean'])

        # Extract the hour from the combined datetime
        grouped['hour'] = grouped['ride_datetime'].dt.hour
        grouped['day_of_week'] = grouped['ride_datetime'].dt.dayofweek

        df = pd.DataFrame(grouped)

        df = df[['route_from', 'route_to', 'ride_type', 'ride_max_persons', 'hour', 'day_of_week', 'ride_waiting_time',
                 'ride_time_minutes', 'ride_price']]

        df_dist = pd.read_csv('route_distances.csv')

        # Create consistent key for df (route distances)
        df['route_key'] = df.apply(lambda x: tuple(sorted([x['route_from'], x['route_to']])), axis=1)

        # Create consistent key for df1 (ride data)
        df_dist['route_key'] = df_dist.apply(lambda x: tuple(sorted([x['route_from'], x['route_to']])), axis=1)

        # Merge df1 with df on route_key
        merged_df = pd.merge(df, df_dist[['route_key', 'distance_meters']], on='route_key', how='left')

        merged_df.drop('route_key',axis=1,inplace=True)

        df = merged_df.copy()

        df2 = pd.read_csv('locations_with_lat_lon.csv')

        # Merge df with df2 for route_from
        df = pd.merge(df, df2, how='left', left_on='route_from', right_on='name')
        df.rename(columns={'Latitude': 'lat_route_from', 'Longitude': 'lon_route_from'}, inplace=True)
        df.drop('name', axis=1, inplace=True)  # Drop the 'name' column after merging

        # Merge df with df2 for route_to
        df = pd.merge(df, df2, how='left', left_on='route_to', right_on='name')
        df.rename(columns={'Latitude': 'lat_route_to', 'Longitude': 'lon_route_to'}, inplace=True)
        df.drop('name', axis=1, inplace=True)  # Drop the 'name' column after merging

        return df

    df = data_processing(df1)

    def model_train_test(df):

        test_locations = ['PVR Ampa SkyOne', 'Marina Beach']

        df_train = df[~((df['route_from'].isin(test_locations)) & (df['route_to'].isin(test_locations)))]

        # Optional: Select the test set separately for later evaluation
        df_test = df[(df['route_from'].isin(test_locations)) & (df['route_to'].isin(test_locations))]

        # Step 1: Split the data into features (X) and targets (y)
        X_train = df_train.drop(
            columns=['route_from', 'route_to', 'ride_price', 'ride_waiting_time', 'ride_time_minutes'])
        X_test = df_test.drop(
            columns=['route_from', 'route_to', 'ride_price', 'ride_waiting_time', 'ride_time_minutes'])

        y_train_price = df_train['ride_price']
        y_train_waiting = df_train['ride_waiting_time']
        y_train_time = df_train['ride_time_minutes']

        y_test_price = df_test['ride_price']
        y_test_waiting = df_test['ride_waiting_time']
        y_test_time = df_test['ride_time_minutes']

        # Step 2: Define numerical and categorical columns
        numerical_features = ['ride_max_persons', 'hour', 'day_of_week', 'distance_meters', 'lat_route_from',
                              'lon_route_from', 'lat_route_to', 'lat_route_to']
        categorical_features = ['ride_type']

        # Step 3: Create preprocessing pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numerical_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
            ])

        # Step 4: Create pipelines for each target
        price_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', RandomForestRegressor(n_estimators=100, random_state=42))
        ])

        waiting_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', RandomForestRegressor(n_estimators=100, random_state=42))
        ])

        time_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', RandomForestRegressor(n_estimators=100, random_state=42))
        ])

        # Step 5: Fit the models
        price_pipeline.fit(X_train, y_train_price)
        waiting_pipeline.fit(X_train, y_train_waiting)
        time_pipeline.fit(X_train, y_train_time)

        # Step 6: Predict on the test data
        price_predictions = price_pipeline.predict(X_test)
        waiting_predictions = waiting_pipeline.predict(X_test)
        time_predictions = time_pipeline.predict(X_test)

        # Step 6: Evaluate the models
        # Step 6: Evaluate the models and log them with MLflow
        def log_and_evaluate_model(model_pipeline, X_test, y_test, y_predictions, model_name):
            with mlflow.start_run(run_name=model_name):
                # Log model
                mlflow.sklearn.log_model(model_pipeline, model_name)

                # Log parameters (you can log more model hyperparameters if needed)
                mlflow.log_param("n_estimators", 100)

                # Log metrics
                mae = mean_absolute_error(y_test, y_predictions)
                mse = mean_squared_error(y_test, y_predictions)
                r2 = r2_score(y_test, y_predictions)

                mlflow.log_metric("MAE", mae)
                mlflow.log_metric("MSE", mse)
                mlflow.log_metric("R2", r2)

                print(f"{model_name}: MAE: {mae}, MSE: {mse}, R²: {r2}")

                # Infer and log signature
                signature = infer_signature(X_test, y_predictions)
                mlflow.sklearn.log_model(model_pipeline, model_name, signature=signature)

        # Evaluate and log each pipeline
        log_and_evaluate_model(price_pipeline, X_test, y_test_price, price_predictions, "Price Prediction Model")
        log_and_evaluate_model(waiting_pipeline, X_test, y_test_waiting, waiting_predictions,
                               "Waiting Time Prediction Model")
        log_and_evaluate_model(time_pipeline, X_test, y_test_time, time_predictions, "Ride Time Prediction Model")

        return price_pipeline,waiting_pipeline,time_pipeline


    price_pipeline,waiting_pipeline,time_pipeline = model_train_test(df)


    print('models trained tested and mlflowed')
    # Save the best pipelines

    #joblib.dump(price_pipeline, 'price_pipeline.pkl')
    #joblib.dump(waiting_pipeline, 'waiting_pipeline.pkl')
    #joblib.dump(time_pipeline, 'time_pipeline.pkl')

    # Experiment name
    experiment_name = "Uber Ride Prediction With Distance"

    # Get experiment ID
    experiment = mlflow.get_experiment_by_name(experiment_name)
    experiment_id = experiment.experiment_id

    # Define model names
    model_names = ['Price Prediction Model', 'Waiting Time Prediction Model', 'Ride Time Prediction Model']

    # Dictionary to store the best run IDs for each model
    best_runs = {}

    # Get all runs for the experiment
    runs = mlflow.search_runs(experiment_ids=[experiment_id])

    # Find the best run for each model
    for model_name in model_names:
        # Filter runs for the current model
        model_runs = runs[runs['tags.mlflow.runName'].str.contains(model_name)]

        # Ensure there are runs available for the model
        if not model_runs.empty:
            # Find the best run based on a metric, e.g., 'R2'
            best_run = model_runs.sort_values(by='metrics.R2', ascending=False).iloc[0]
            best_run_id = best_run.run_id
            best_runs[model_name] = best_run_id
        else:
            print(f"No runs found for model {model_name}")

    # Dictionary to store loaded models
    models = {}

    # Load each model
    for model_name, run_id in best_runs.items():
        model_uri = f"runs:/{run_id}/{model_name}/"
        models[model_name] = mlflow.pyfunc.load_model(model_uri)

    # Create the directory if it doesn't exist
    os.makedirs('bestmodels', exist_ok=True)

    # Save each model as a .pkl file
    for model_name, model in models.items():
        file_path = f"bestmodels/{model_name}_pipeline.pkl"
        with open(file_path, 'wb') as file:
            pickle.dump(model, file)

    # Print to verify saving
    print(f"Models saved: {', '.join(models.keys())}")


mlflow_run()


