import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AttendanceDataProcessor:
    """
    Data preprocessing class for patient attendance prediction model.
    Handles CSV data with columns: sex, date_of_appointment, age, attended_or_did_not_attend
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def load_csv(self, filepath: str) -> pd.DataFrame:
        """Load CSV data and validate required columns"""
        try:
            df = pd.read_csv(filepath)
            required_columns = ['sex', 'date_of_appointment', 'age', 'attended_or_did_not_attend']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
                
            logger.info(f"Loaded CSV with {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}")
            raise
    
    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply feature engineering transformations
        - sex: 0=male, 1=female (encoded from original values)
        - date_of_appointment: date in dd/mm/yyyy format
        - age: patient age in years (already provided)
        """
        df_processed = df.copy()
        
        # Handle sex encoding - map 3 to 0 (male), keep 1 as 1 (female)
        df_processed['sex'] = df_processed['sex'].map({1: 1, 3: 0})
        
        # Parse dates and create date-based features (expecting dd/mm/yyyy format)
        df_processed['date_of_appointment'] = pd.to_datetime(df_processed['date_of_appointment'], format='%d/%m/%Y')
        
        # Extract date components
        df_processed['day_of_week'] = df_processed['date_of_appointment'].dt.dayofweek  # 0=Monday, 6=Sunday
        df_processed['month'] = df_processed['date_of_appointment'].dt.month  # 1-12
        df_processed['day_of_month'] = df_processed['date_of_appointment'].dt.day  # 1-31
        
        # Create categorical features
        df_processed['is_weekend'] = (df_processed['day_of_week'] >= 5).astype(int)  # Saturday=5, Sunday=6
        df_processed['is_monday'] = (df_processed['day_of_week'] == 0).astype(int)
        df_processed['is_friday'] = (df_processed['day_of_week'] == 4).astype(int)
        
        # Validate data ranges after encoding
        if df_processed['sex'].isnull().any():
            raise ValueError("Sex values contain invalid entries - must be 1 (female) or 3 (male)")
            
        if (df_processed['sex'] < 0).any() or (df_processed['sex'] > 1).any():
            raise ValueError("Sex values must be 0 (male) or 1 (female) after encoding")
            
        if (df_processed['age'] < 0).any() or (df_processed['age'] > 150).any():
            raise ValueError("Calculated age is out of reasonable range")
            
        logger.info("Feature engineering completed successfully")
        return df_processed
    
    def prepare_features_and_target(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features (X) and target (y) arrays for model training
        """
        # Apply feature engineering
        df_processed = self.feature_engineering(df)
        
        # Select features for the model
        feature_columns = ['sex', 'day_of_week', 'month', 'day_of_month', 'age', 'is_weekend', 'is_monday', 'is_friday']
        X = df_processed[feature_columns].values
        
        # Target variable
        y = df_processed['attended_or_did_not_attend'].values
        
        # Fit scaler on training data
        if not self.is_fitted:
            X = self.scaler.fit_transform(X)
            self.is_fitted = True
        else:
            X = self.scaler.transform(X)
        
        logger.info(f"Prepared features shape: {X.shape}, target shape: {y.shape}")
        return X, y
    
    def prepare_single_prediction(self, sex: int, date_of_appointment: str, age: int) -> np.ndarray:
        """
        Prepare a single record for prediction
        Accepts standard API format: sex (0=male, 1=female)
        """
        if not self.is_fitted:
            raise ValueError("Processor must be fitted on training data first")
        
        # Convert API format (0=male, 1=female) to training data format (3=male, 1=female)
        training_sex = 1 if sex == 1 else 3
        
        # Create a DataFrame with single record using training data format
        data = {
            'sex': [training_sex],
            'date_of_appointment': [date_of_appointment],
            'age': [age],
            'attended_or_did_not_attend': [0]  # Dummy value, not used for prediction
        }
        df = pd.DataFrame(data)
        
        # Apply feature engineering
        df_processed = self.feature_engineering(df)
        
        # Select features
        feature_columns = ['sex', 'day_of_week', 'month', 'day_of_month', 'age', 'is_weekend', 'is_monday', 'is_friday']
        X = df_processed[feature_columns].values
        
        # Scale features
        X = self.scaler.transform(X)
        
        return X
    
    def get_feature_names(self) -> list:
        """Return the list of feature names used by the model"""
        return ['sex', 'day_of_week', 'month', 'day_of_month', 'age', 'is_weekend', 'is_monday', 'is_friday']