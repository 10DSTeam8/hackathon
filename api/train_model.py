#!/usr/bin/env python3
"""
Training script for the patient attendance prediction model
"""

import os
import sys
import logging
from attendance_model import AttendancePredictor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main training function"""
    
    # Check if CSV file path is provided
    if len(sys.argv) < 2:
        print("Usage: python train_model.py <path_to_csv_file>")
        print("Example: python train_model.py data/training_data.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    # Validate CSV file exists
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    try:
        # Initialize the predictor
        predictor = AttendancePredictor()
        
        logger.info(f"Starting training with data from: {csv_path}")
        
        # Train the model
        training_results = predictor.train(
            csv_path=csv_path,
            validation_split=0.2,
            epochs=100,
            batch_size=32,
            verbose=1
        )
        
        # Print training results
        logger.info("Training completed successfully!")
        logger.info(f"Training Results:")
        logger.info(f"  Final Loss: {training_results['final_loss']:.4f}")
        logger.info(f"  Final Accuracy: {training_results['final_accuracy']:.4f}")
        logger.info(f"  Final Validation Loss: {training_results['final_val_loss']:.4f}")
        logger.info(f"  Final Validation Accuracy: {training_results['final_val_accuracy']:.4f}")
        logger.info(f"  Epochs Trained: {training_results['epochs_trained']}")
        
        # Test a single prediction
        logger.info("Testing a single prediction...")
        test_result = predictor.predict(
            sex=1,  # Female
            date_of_appointment="16/09/2024",  # Monday
            age=35  # 35 years old
        )
        
        logger.info(f"Test Prediction Result: {test_result}")
        
        print("\n" + "="*50)
        print("TRAINING COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Model saved to: {predictor.model_path}")
        print(f"Data processor saved to: {predictor.processor_path}")
        print(f"Final validation accuracy: {training_results['final_val_accuracy']:.2%}")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()