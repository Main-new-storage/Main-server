"""
Enhanced model testing with real training data from Dropbox.

This module loads real training data from the Dropbox database and tests
the base model to ensure it works correctly with user's actual data.
"""

import logging
import sqlite3
import pandas as pd
import random
import time
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from io import BytesIO

import config

# Configure logging
logger = logging.getLogger(__name__)

def test_model_with_real_data(model=None, sample_size=100) -> Dict[str, Any]:
    """
    Test the intent classifier model with real training data from the database.
    
    Args:
        model: Optional pre-loaded CoreML model. If None, the base model will be loaded.
        sample_size: Number of samples to test from the database (max)
        
    Returns:
        Dict with test results
    """
    start_time = time.time()
    
    # Create results dictionary
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "model_loaded": False,
        "data_loaded": False,
        "errors": [],
        "warnings": [],
        "stats": {
            "total_samples": 0,
            "successful_predictions": 0,
            "failed_predictions": 0,
            "accuracy": 0.0,
            "duration_seconds": 0
        },
        "intent_performance": {},
        "samples_tested": []
    }
    
    # Step 1: Load the model if not provided
    if model is None:
        try:
            # Try to import coremltools safely
            try:
                import coremltools as ct
            except ImportError:
                error = "CoreMLTools not installed - cannot test model"
                test_results["errors"].append(error)
                logger.error(error)
                return test_results
                
            # Get the base model
            try:
                from utils.model_download import get_base_model_buffer
                model_buffer = get_base_model_buffer()
                
                if model_buffer is None:
                    error = f"Base model {config.BASE_MODEL_NAME} not found"
                    test_results["errors"].append(error)
                    logger.error(error)
                    return test_results
                
                # Load the model
                model = ct.models.MLModel(model_buffer)
                test_results["model_loaded"] = True
                logger.info(f"Successfully loaded base model for testing")
                
            except Exception as e:
                error = f"Error loading base model: {str(e)}"
                test_results["errors"].append(error)
                logger.error(error)
                return test_results
        
        except Exception as e:
            error = f"Error preparing model for testing: {str(e)}"
            test_results["errors"].append(error)
            logger.error(error)
            return test_results
    else:
        test_results["model_loaded"] = True
        logger.info("Using provided model for testing")
    
    # Step 2: Get training data from the database
    try:
        # Load interaction data from the database
        interactions_df = load_interaction_data(sample_size)
        
        if interactions_df is None or len(interactions_df) == 0:
            warning = "No interaction data found for testing"
            test_results["warnings"].append(warning)
            logger.warning(warning)
            test_results["data_loaded"] = False
            
            # Create some synthetic test data as fallback
            interactions_df = create_synthetic_test_data()
            
            if interactions_df is None or len(interactions_df) == 0:
                error = "Could not create synthetic test data"
                test_results["errors"].append(error)
                logger.error(error)
                return test_results
                
            logger.info(f"Created synthetic test data with {len(interactions_df)} samples")
            test_results["data_source"] = "synthetic"
        else:
            logger.info(f"Loaded {len(interactions_df)} interaction samples for testing")
            test_results["data_loaded"] = True
            test_results["data_source"] = "database"
            
        # Set total samples
        test_results["stats"]["total_samples"] = len(interactions_df)
        
        # Track intents for performance metrics
        intents_metrics = {}
        
        # Step 3: Test each sample
        for idx, row in interactions_df.iterrows():
            user_message = row.get('user_message')
            expected_intent = row.get('detected_intent')
            
            # Skip if no message or intent
            if not user_message or not expected_intent:
                continue
                
            # Create sample result
            sample_result = {
                "user_message": user_message,
                "expected_intent": expected_intent,
                "success": False,
                "predicted_intent": None,
                "confidence": None,
                "error": None
            }
            
            # Initialize intent metrics if needed
            if expected_intent not in intents_metrics:
                intents_metrics[expected_intent] = {
                    "total": 0,
                    "correct": 0,
                    "accuracy": 0.0
                }
            
            intents_metrics[expected_intent]["total"] += 1
            
            # Make prediction
            try:
                prediction = model.predict({"text": user_message})
                
                # Extract result
                predicted_intent = None
                confidence = 0.0
                
                # Handle different output formats
                if isinstance(prediction, dict):
                    # Extract intent and confidence based on available keys
                    if 'intent' in prediction:
                        predicted_intent = prediction['intent']
                        
                        # Try to find confidence
                        if 'probabilities' in prediction:
                            probs = prediction['probabilities']
                            if isinstance(probs, dict) and predicted_intent in probs:
                                confidence = probs[predicted_intent]
                            elif isinstance(probs, list) and hasattr(model, 'classes_'):
                                try:
                                    idx = model.classes_.index(predicted_intent)
                                    confidence = probs[idx]
                                except (ValueError, IndexError):
                                    pass
                
                # Check if prediction matches expected
                if predicted_intent and predicted_intent == expected_intent:
                    sample_result["success"] = True
                    test_results["stats"]["successful_predictions"] += 1
                    intents_metrics[expected_intent]["correct"] += 1
                else:
                    test_results["stats"]["failed_predictions"] += 1
                
                sample_result["predicted_intent"] = predicted_intent
                sample_result["confidence"] = confidence
                
            except Exception as e:
                sample_result["error"] = str(e)
                test_results["stats"]["failed_predictions"] += 1
            
            # Add to samples tested (limit to 20 for size reasons)
            if len(test_results["samples_tested"]) < 20:
                test_results["samples_tested"].append(sample_result)
        
        # Calculate intent-specific metrics
        for intent, metrics in intents_metrics.items():
            if metrics["total"] > 0:
                metrics["accuracy"] = metrics["correct"] / metrics["total"]
        
        test_results["intent_performance"] = intents_metrics
        
        # Calculate overall accuracy
        total_samples = test_results["stats"]["successful_predictions"] + test_results["stats"]["failed_predictions"]
        if total_samples > 0:
            test_results["stats"]["accuracy"] = test_results["stats"]["successful_predictions"] / total_samples
        
        test_results["success"] = test_results["model_loaded"] and (test_results["stats"]["accuracy"] > 0.6 or test_results["stats"]["successful_predictions"] > 10)
        
        # Calculate duration
        test_results["stats"]["duration_seconds"] = time.time() - start_time
        
        logger.info(f"Model testing completed with {test_results['stats']['accuracy']:.2f} accuracy on {total_samples} samples")
    
    except Exception as e:
        error = f"Error testing model with real data: {str(e)}"
        test_results["errors"].append(error)
        logger.error(error)
    
    return test_results

def load_interaction_data(sample_size=100) -> Optional[pd.DataFrame]:
    """
    Load interaction data from the database.
    
    Args:
        sample_size: Maximum number of samples to load
        
    Returns:
        DataFrame of interaction data or None if failed
    """
    try:
        # If Dropbox is enabled, get data from memory DB
        if config.DROPBOX_ENABLED:
            try:
                from utils.memory_db import get_memory_db_connection
                conn = get_memory_db_connection()
                
                # Query to get latest interactions with detected intent
                query = """
                    SELECT user_message, detected_intent, confidence, created_at
                    FROM interactions
                    WHERE detected_intent IS NOT NULL AND user_message IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                
                df = pd.read_sql_query(query, conn, params=(sample_size,))
                
                if len(df) > 0:
                    logger.info(f"Loaded {len(df)} interactions from in-memory database")
                    return df
                else:
                    logger.warning("No valid interactions found in in-memory database")
                    
                    # Try to find interactions without detected intent
                    query_no_intent = """
                        SELECT user_message, intent_override AS detected_intent, 1.0 AS confidence, created_at
                        FROM interactions
                        WHERE intent_override IS NOT NULL AND user_message IS NOT NULL
                        ORDER BY created_at DESC
                        LIMIT ?
                    """
                    
                    df = pd.read_sql_query(query_no_intent, conn, params=(sample_size,))
                    
                    if len(df) > 0:
                        logger.info(f"Loaded {len(df)} interactions with intent_override")
                        return df
                    
                    logger.warning("No interactions with intent_override found")
                    return None
                
            except ImportError:
                logger.warning("Could not import memory_db module - falling back to direct database")
                
            except Exception as e:
                logger.error(f"Error loading interactions from memory DB: {e}")
                logger.warning("Falling back to direct database access")
        
        # Fall back to direct database access
        try:
            from utils.db_helpers import get_connection
            conn = get_connection(config.DB_PATH)
            
            # Query to get latest interactions with detected intent
            query = """
                SELECT user_message, detected_intent, confidence, created_at
                FROM interactions
                WHERE detected_intent IS NOT NULL AND user_message IS NOT NULL
                ORDER BY created_at DESC
                LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=(sample_size,))
            conn.close()
            
            if len(df) > 0:
                logger.info(f"Loaded {len(df)} interactions from database file")
                return df
            else:
                logger.warning("No valid interactions found in database file")
                return None
                
        except Exception as e:
            logger.error(f"Error loading interactions from database file: {e}")
            return None
    
    except Exception as e:
        logger.error(f"Error in load_interaction_data: {e}")
        return None

def create_synthetic_test_data() -> pd.DataFrame:
    """
    Create synthetic test data for model testing when no real data is available.
    
    Returns:
        DataFrame of synthetic test data
    """
    try:
        # Define common intents and example messages
        intent_examples = {
            "greeting": [
                "hello there", "hi", "hey", "good morning", "hello",
                "greetings", "hi there", "hello bot", "hey there"
            ],
            "goodbye": [
                "bye", "goodbye", "see you later", "good night", "bye bye",
                "talk to you later", "I'm leaving", "have to go now", "farewell"
            ],
            "thanks": [
                "thank you", "thanks", "appreciate it", "thanks a lot", "thank you so much",
                "thanks for your help", "many thanks", "I appreciate your assistance"
            ],
            "help": [
                "help me", "I need help", "can you help", "assist me", "support please",
                "I'm stuck", "need assistance", "how can I", "how do I"
            ],
            "weather": [
                "what's the weather like", "is it going to rain", "temperature today",
                "weather forecast", "will it be sunny", "weather report"
            ]
        }
        
        # Create synthetic data
        data = []
        for intent, examples in intent_examples.items():
            for example in examples:
                data.append({
                    "user_message": example,
                    "detected_intent": intent,
                    "confidence": 1.0,
                    "created_at": datetime.now().isoformat()
                })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        return df
    
    except Exception as e:
        logger.error(f"Error creating synthetic test data: {e}")
        return None

def comprehensive_base_model_test() -> Dict[str, Any]:
    """
    Run a comprehensive test of the base model with real data.
    
    This function:
    1. Loads and validates the model structure
    2. Tests the model with real data from the database
    3. Stores test results in Dropbox
    
    Returns:
        Dict with test results
    """
    logger.info("Starting comprehensive base model test")
    
    # First validate the model structure
    try:
        from utils.model_validator import validate_base_model
        validation_results = validate_base_model()
        
        if not validation_results.get('success', False):
            logger.error("Base model validation failed!")
            return validation_results
            
        logger.info("Base model structure validation successful")
    except Exception as e:
        logger.error(f"Error validating base model structure: {e}")
        return {
            "success": False,
            "errors": [f"Structure validation failed: {str(e)}"]
        }
    
    # Now test with real data
    try:
        # Check if we already have a model loaded
        model = None
        if validation_results.get('model_loaded', False):
            model = validation_results.get('model')
            
        # Run the real data test
        test_results = test_model_with_real_data(model)
        
        # Combine the results
        combined_results = {
            "timestamp": datetime.now().isoformat(),
            "success": validation_results.get('success', False) and test_results.get('success', False),
            "structure_validation": validation_results,
            "performance_testing": test_results,
            "errors": validation_results.get('errors', []) + test_results.get('errors', []),
            "warnings": validation_results.get('warnings', []) + test_results.get('warnings', [])
        }
        
        # Log overview
        accuracy = test_results.get('stats', {}).get('accuracy', 0)
        samples = test_results.get('stats', {}).get('total_samples', 0)
        
        if combined_results['success']:
            logger.info(f"Comprehensive base model test successful - {accuracy:.2f} accuracy on {samples} samples")
        else:
            logger.warning(f"Comprehensive base model test had issues - {accuracy:.2f} accuracy on {samples} samples")
            logger.warning(f"Errors: {combined_results['errors']}")
            logger.warning(f"Warnings: {combined_results['warnings']}")
        
        # Store results in Dropbox if enabled
        store_test_results(combined_results)
        
        return combined_results
        
    except Exception as e:
        logger.error(f"Error in comprehensive base model test: {e}")
        return {
            "success": False,
            "errors": [f"Comprehensive testing failed: {str(e)}"]
        }

def store_test_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store test results in Dropbox.
    
    Args:
        results: Test results dictionary
        
    Returns:
        Updated results with storage information
    """
    # Only store in Dropbox if enabled
    if not config.DROPBOX_ENABLED:
        results["storage"] = {
            "location": "local_only",
            "reason": "Dropbox storage not enabled"
        }
        return results
    
    try:
        import json
        from io import BytesIO
        
        # Import Dropbox storage
        from utils.dropbox_storage import get_dropbox_storage
        dropbox_storage = get_dropbox_storage()
        
        # Create test results folder if needed
        test_folder = "model_testing"
        try:
            folder_path = f"/{test_folder}"
            try:
                dropbox_storage.dbx.files_get_metadata(folder_path)
            except Exception:
                # Create folder if it doesn't exist
                logger.info(f"Creating test results folder: {folder_path}")
                dropbox_storage.dbx.files_create_folder_v2(folder_path)
        except Exception as e:
            logger.warning(f"Error ensuring test folder exists: {e}")
            results["storage"] = {
                "location": "local_only",
                "reason": f"Dropbox folder creation failed: {str(e)}"
            }
            return results
        
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        # Convert results to JSON
        json_data = json.dumps(results, indent=2)
        buffer = BytesIO(json_data.encode('utf-8'))
        
        # Upload to Dropbox
        upload_result = dropbox_storage.upload_model(
            buffer,
            filename,
            test_folder
        )
        
        if upload_result and upload_result.get('success'):
            # Add storage info to results
            results["storage"] = {
                "location": "dropbox",
                "path": upload_result.get('path'),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Stored test results in Dropbox: {test_folder}/{filename}")
            
            # Also save as latest test result
            try:
                latest_buffer = BytesIO(json_data.encode('utf-8'))
                latest_result = dropbox_storage.upload_model(
                    latest_buffer,
                    "latest_test_results.json",
                    test_folder
                )
                if latest_result and latest_result.get('success'):
                    logger.info("Updated latest test results in Dropbox")
            except Exception as e:
                logger.warning(f"Error updating latest test results: {e}")
                
        else:
            # Handle upload failure
            error = upload_result.get('error', 'Unknown error')
            results["storage"] = {
                "location": "local_only",
                "reason": f"Dropbox upload failed: {error}"
            }
            logger.warning(f"Failed to upload test results: {error}")
    
    except Exception as e:
        # Handle any exceptions
        results["storage"] = {
            "location": "local_only",
            "reason": f"Error: {str(e)}"
        }
        logger.error(f"Error storing test results: {e}")
    
    return results
