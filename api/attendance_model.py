import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
import os
import joblib
import logging
from data_preprocessing import AttendanceDataProcessor

logger = logging.getLogger(__name__)

class AttendancePredictor:
    """
    TensorFlow neural network model for predicting patient attendance
    """
    
    def __init__(self, model_path: str = "models/attendance_model.h5", 
                 processor_path: str = "models/data_processor.pkl"):
        self.model_path = model_path
        self.processor_path = processor_path
        self.model = None
        self.processor = None
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    def create_model(self, input_shape: int) -> keras.Model:
        """
        Create a neural network model for binary classification
        """
        model = keras.Sequential([
            # Input layer
            layers.Dense(64, activation='relu', input_shape=(input_shape,)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Hidden layers
            layers.Dense(32, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            layers.Dense(16, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            # Output layer for binary classification
            layers.Dense(1, activation='sigmoid')
        ])
        
        # Compile the model
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        logger.info("Model created successfully")
        logger.info(f"Model summary:\n{model.summary()}")
        
        return model
    
    def train(self, csv_path: str, validation_split: float = 0.2, epochs: int = 100, 
              batch_size: int = 32, verbose: int = 1) -> dict:
        """
        Train the model using CSV data
        """
        try:
            # Initialize data processor
            self.processor = AttendanceDataProcessor()
            
            # Load and preprocess data
            df = self.processor.load_csv(csv_path)
            X, y = self.processor.prepare_features_and_target(df)
            
            # Create model
            self.model = self.create_model(input_shape=X.shape[1])
            
            # Set up callbacks
            callbacks = [
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7
                )
            ]
            
            # Train the model
            history = self.model.fit(
                X, y,
                validation_split=validation_split,
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks,
                verbose=verbose
            )
            
            # Save the model and processor
            self.save_model()
            
            logger.info("Training completed successfully")
            
            # Return training history
            return {
                'final_loss': history.history['loss'][-1],
                'final_accuracy': history.history['accuracy'][-1],
                'final_val_loss': history.history['val_loss'][-1],
                'final_val_accuracy': history.history['val_accuracy'][-1],
                'epochs_trained': len(history.history['loss'])
            }
            
        except Exception as e:
            logger.error(f"Error during training: {str(e)}")
            raise
    
    def save_model(self):
        """Save the trained model and data processor"""
        try:
            if self.model is not None:
                self.model.save(self.model_path)
                logger.info(f"Model saved to {self.model_path}")
            
            if self.processor is not None:
                joblib.dump(self.processor, self.processor_path)
                logger.info(f"Data processor saved to {self.processor_path}")
                
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self):
        """Load the trained model and data processor"""
        try:
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                logger.info(f"Model loaded from {self.model_path}")
            else:
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            if os.path.exists(self.processor_path):
                self.processor = joblib.load(self.processor_path)
                logger.info(f"Data processor loaded from {self.processor_path}")
            else:
                raise FileNotFoundError(f"Processor file not found: {self.processor_path}")
                
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def predict(self, sex: int, date_of_appointment: str, age: int) -> dict:
        """
        Make a prediction for a single patient
        
        Args:
            sex: 0 for male, 1 for female
            date_of_appointment: Date in YYYY-MM-DD format
            age: Patient's age in years
            
        Returns:
            Dictionary with prediction probability and binary classification
        """
        try:
            # Load model if not already loaded
            if self.model is None or self.processor is None:
                self.load_model()
            
            # Preprocess the input data
            X = self.processor.prepare_single_prediction(sex, date_of_appointment, age)
            
            # Make prediction
            prediction_prob = self.model.predict(X, verbose=0)[0][0]
            prediction_binary = int(prediction_prob >= 0.5)
            
            result = {
                'will_attend_probability': float(prediction_prob),
                'predicted_attendance': prediction_binary,
                'confidence': float(max(prediction_prob, 1 - prediction_prob))
            }
            
            logger.info(f"Prediction made: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            raise
    
    def evaluate(self, csv_path: str) -> dict:
        """
        Evaluate the model on test data
        """
        try:
            if self.model is None or self.processor is None:
                self.load_model()
            
            # Load and preprocess test data
            df = self.processor.load_csv(csv_path)
            X, y = self.processor.prepare_features_and_target(df)
            
            # Evaluate model
            results = self.model.evaluate(X, y, verbose=0)
            
            evaluation = {
                'test_loss': results[0],
                'test_accuracy': results[1],
                'test_precision': results[2],
                'test_recall': results[3]
            }
            
            logger.info(f"Model evaluation: {evaluation}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise