

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # infrastructure
    mlflow_tracking_uri: str = "http://mlflow:5000"
    mlflow_experiment_name: str = "rul-mlops"
    model_registry_name: str = "RULModel"      # matches the registry, verified
    model_alias: str = "production"
    serving_port: int = 8000
    log_level: str = "INFO"

    # model / training
    window_size: int = 30
    lstm_hidden_size_1: int = 64
    lstm_hidden_size_2: int = 32
    lstm_dropout: float = 0.2
    adam_lr: float = 0.001
    batch_size: int = 32
    early_stopping_patience: int = 10

    # drift
    psi_drift_threshold: float = 0.2
    residual_ema_threshold: float = 5.0

    # retraining
    retraining_blend_ratio: float = 0.3

    # shadow
    bootstrap_resamples: int = 1000
    bootstrap_ci_level: float = 0.95
    shadow_min_predictions: int = 500
    post_promotion_monitor_window: int = 200
    rollback_residual_delta: float = 3.0

    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    processed_data_dir: str = "data/processed"
    raw_data_dir: str = "data/raw"
    reference_data_path: str = "data/processed/reference_data.parquet"
# features
FEATURE_COLUMNS = ["s2", "s3", "s4", "s7", "s8", "s9", "s11",
                   "s12", "s13", "s14", "s15", "s17", "s20", "s21"]

settings = Settings()
