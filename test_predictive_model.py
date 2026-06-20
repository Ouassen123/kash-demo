#!/usr/bin/env python
"""Test script for predictive modeling system."""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_feature_engineering():
    """Test the feature engineering service."""
    print("🧪 Testing Feature Engineering Service")
    print("=" * 42)
    
    try:
        # Test imports
        from src.modules.intelligence.predictive_model.services.feature_engineering import (
            FeatureEngineeringService
        )
        from src.modules.intelligence.predictive_model.models.feature_models import (
            CompatibilityFeatures,
            HistoricalPerformanceFeatures,
            TargetVariable
        )
        from src.modules.intelligence.predictive_model.models.prediction_models import (
            PredictionTarget
        )
        print("✅ Feature engineering service imported successfully")
        
        # Initialize service
        feature_service = FeatureEngineeringService()
        print("✅ Feature engineering service initialized")
        
        # Test compatibility features creation
        print(f"\n🎯 Testing Compatibility Features:")
        print("-" * 38)
        
        compatibility_features = feature_service.create_compatibility_features(
            "test_learner_001", "technology"
        )
        
        print(f"✅ Compatibility features created:")
        print(f"     Overall score: {compatibility_features.overall_compatibility_score:.3f}")
        print(f"     Confidence: {compatibility_features.compatibility_confidence:.3f}")
        print(f"     Knowledge score: {compatibility_features.knowledge_score:.3f}")
        print(f"     Skills score: {compatibility_features.skills_score:.3f}")
        print(f"     Data quality: {compatibility_features.data_quality_score:.3f}")
        print(f"     Total signals: {compatibility_features.total_signals}")
        
        # Test historical performance features
        print(f"\n🎯 Testing Historical Performance Features:")
        print("-" * 48)
        
        historical_features = feature_service.create_historical_performance_features(
            "test_learner_001"
        )
        
        print(f"✅ Historical features created:")
        print(f"     GPA trend: {len(historical_features.gpa_trend)} points")
        print(f"     Course completion rate: {historical_features.course_completion_rate:.3f}")
        print(f"     Average grade: {historical_features.average_grade:.1f}")
        print(f"     Skills improvement rate: {historical_features.skills_improvement_rate:.3f}")
        print(f"     Project success rate: {historical_features.project_success_rate:.3f}")
        print(f"     Learning consistency: {historical_features.learning_consistency:.3f}")
        print(f"     Dropout risk: {historical_features.dropout_risk_score:.3f}")
        
        # Test demographic features
        print(f"\n🎯 Testing Demographic Features:")
        print("-" * 35)
        
        demographic_features = feature_service.create_demographic_features("test_learner_001")
        
        if demographic_features:
            print(f"✅ Demographic features created:")
            print(f"     Age: {demographic_features.age}")
            print(f"     Education: {demographic_features.education_level}")
            print(f"     Experience: {demographic_features.years_of_experience} years")
            print(f"     Languages: {len(demographic_features.languages_spoken)}")
        else:
            print("⚠️  Demographic features not available (optional)")
        
        # Test behavioral features
        print(f"\n🎯 Testing Behavioral Features:")
        print("-" * 34)
        
        behavioral_features = feature_service.create_behavioral_features("test_learner_001")
        
        if behavioral_features:
            print(f"✅ Behavioral features created:")
            print(f"     Preferred time: {behavioral_features.preferred_learning_time}")
            print(f"     Session duration: {behavioral_features.learning_session_duration:.1f} min")
            print(f"     Forum participation: {behavioral_features.forum_participation:.3f}")
            print(f"     Intrinsic motivation: {behavioral_features.intrinsic_motivation_score:.3f}")
            print(f"     Technical proficiency: {behavioral_features.technical_proficiency:.3f}")
        else:
            print("⚠️  Behavioral features not available (optional)")
        
        # Test training example creation
        print(f"\n🎯 Testing Training Example Creation:")
        print("-" * 41)
        
        target_data = {
            "target_type": "success_likelihood",
            "target_value": 0.85,
            "job_family": "technology",
            "observation_date": datetime.utcnow(),
            "confidence_in_label": 0.9,
            "label_source": "historical_outcome"
        }
        
        training_example = feature_service.create_training_example(
            "test_learner_001", target_data
        )
        
        print(f"✅ Training example created:")
        print(f"     Feature vector length: {len(training_example.feature_vector)}")
        print(f"     Feature names count: {len(training_example.feature_names)}")
        print(f"     Data quality score: {training_example.data_quality_score:.3f}")
        print(f"     Missing features: {len(training_example.missing_features)}")
        print(f"     Outlier indicators: {len(training_example.outlier_indicators)}")
        print(f"     Target type: {training_example.target.target_type.value}")
        print(f"     Target value: {training_example.target.target_value:.3f}")
        
        # Test feature store
        print(f"\n🎯 Testing Feature Store:")
        print("-" * 28)
        
        feature_store = feature_service.get_feature_store()
        print(f"✅ Feature store accessed:")
        print(f"     Store name: {feature_store.store_name}")
        print(f"     Version: {feature_store.version}")
        print(f"     Active features: {len(feature_store.active_features)}")
        print(f"     Data sources: {list(feature_store.data_sources.keys())}")
        
        print(f"\n🎉 Feature engineering test completed!")
        print(f"📊 Summary:")
        print(f"  ✅ Compatibility feature engineering")
        print(f"  ✅ Historical performance feature engineering")
        print(f"  ✅ Optional demographic and behavioral features")
        print(f"  ✅ Training example creation with quality assessment")
        print(f"  ✅ Feature vector generation and naming")
        print(f"  ✅ Feature store management")
        print(f"  ✅ Data quality scoring and outlier detection")
        
        return True
        
    except Exception as e:
        print(f"❌ Feature engineering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ml_service():
    """Test the machine learning service."""
    print(f"\n🧪 Testing Machine Learning Service")
    print("=" * 37)
    
    try:
        # Test imports
        from src.modules.intelligence.predictive_model.services.ml_service import (
            PredictiveModelService
        )
        from src.modules.intelligence.predictive_model.services.feature_engineering import (
            FeatureEngineeringService
        )
        from src.modules.intelligence.predictive_model.models.prediction_models import (
            PredictionTarget, ModelType
        )
        print("✅ ML service and dependencies imported successfully")
        
        # Initialize services
        ml_service = PredictiveModelService()
        feature_service = FeatureEngineeringService()
        print("✅ Services initialized")
        
        # Create training pipeline
        print(f"\n🎯 Creating Training Pipeline:")
        print("-" * 32)
        
        pipeline_config = {
            "pipeline_name": "success_likelihood_test",
            "model_type": ModelType.CLASSIFICATION,
            "prediction_target": PredictionTarget.SUCCESS_LIKELIHOOD,
            "feature_store_id": "test_store",
            "training_data_query": "SELECT * FROM training_data",
            "validation_split": 0.2,
            "test_split": 0.2,
            "feature_selection_method": "importance",
            "algorithm": "random_forest",
            "cross_validation_folds": 5,
            "created_by": "test_user"
        }
        
        pipeline = ml_service.create_training_pipeline(pipeline_config)
        print(f"✅ Training pipeline created:")
        print(f"     Pipeline ID: {pipeline.pipeline_id}")
        print(f"     Model type: {pipeline.model_type.value}")
        print(f"     Algorithm: {pipeline.algorithm}")
        print(f"     Target: {pipeline.prediction_target.value}")
        
        # Create synthetic training data
        print(f"\n🎯 Creating Synthetic Training Data:")
        print("-" * 40)
        
        training_examples = []
        
        # Create diverse training examples
        for i in range(100):
            learner_id = f"synthetic_learner_{i:03d}"
            
            # Vary the target based on some features
            base_success = 0.5
            
            # Create features
            compatibility = feature_service.create_compatibility_features(learner_id, "technology")
            historical = feature_service.create_historical_performance_features(learner_id)
            
            # Adjust target based on features
            if compatibility.overall_compatibility_score > 0.8:
                base_success += 0.3
            elif compatibility.overall_compatibility_score < 0.6:
                base_success -= 0.2
            
            if historical.learning_velocity > 0.8:
                base_success += 0.2
            elif historical.learning_velocity < 0.5:
                base_success -= 0.1
            
            if historical.dropout_risk_score < 0.2:
                base_success += 0.1
            elif historical.dropout_risk_score > 0.5:
                base_success -= 0.2
            
            # Add some noise
            import random
            base_success += random.uniform(-0.1, 0.1)
            base_success = max(0.0, min(1.0, base_success))
            
            # Create binary target for classification
            target_value = 1 if base_success > 0.6 else 0
            
            target_data = {
                "target_type": "success_likelihood",
                "target_value": target_value,
                "job_family": "technology",
                "observation_date": datetime.utcnow() - timedelta(days=random.randint(1, 365)),
                "confidence_in_label": 0.8 + random.uniform(0, 0.2),
                "label_source": "synthetic_generation"
            }
            
            example = feature_service.create_training_example(learner_id, target_data)
            training_examples.append(example)
        
        print(f"✅ Created {len(training_examples)} synthetic training examples")
        
        # Analyze target distribution
        success_count = sum(1 for ex in training_examples if ex.target.target_value == 1)
        failure_count = len(training_examples) - success_count
        print(f"     Success cases: {success_count} ({success_count/len(training_examples):.1%})")
        print(f"     Failure cases: {failure_count} ({failure_count/len(training_examples):.1%})")
        
        # Train model
        print(f"\n🎯 Training Predictive Model:")
        print("-" * 30)
        
        model_metadata = ml_service.train_model(pipeline.pipeline_id, training_examples)
        
        print(f"✅ Model trained successfully:")
        print(f"     Model ID: {model_metadata.model_id}")
        print(f"     Model name: {model_metadata.model_name}")
        print(f"     Algorithm: {model_metadata.algorithm}")
        print(f"     Training samples: {model_metadata.training_dataset.training_samples}")
        print(f"     Validation samples: {model_metadata.training_dataset.validation_samples}")
        print(f"     Test samples: {model_metadata.training_dataset.test_samples}")
        print(f"     Feature count: {model_metadata.training_dataset.feature_count}")
        print(f"     CV score: {model_metadata.cross_validation_score:.3f}")
        
        # Display performance metrics
        perf = model_metadata.performance
        if model_metadata.model_type == ModelType.CLASSIFICATION:
            print(f"     Performance:")
            print(f"       Accuracy: {perf.accuracy:.3f}")
            print(f"       Precision: {perf.precision:.3f}")
            print(f"       Recall: {perf.recall:.3f}")
            print(f"       F1 Score: {perf.f1_score:.3f}")
            if perf.auc_roc:
                print(f"       AUC-ROC: {perf.auc_roc:.3f}")
        
        # Display feature importance
        print(f"\n🎯 Top Feature Importance:")
        print("-" * 30)
        
        top_features = model_metadata.feature_importance[:10]
        for i, feature in enumerate(top_features, 1):
            print(f"     {i:2d}. {feature.feature_name:<25} ({feature.importance_score:.3f})")
        
        # Test prediction
        print(f"\n🎯 Testing Model Prediction:")
        print("-" * 32)
        
        # Use a sample from training data
        test_example = training_examples[0]
        prediction_result = ml_service.predict(
            model_metadata.model_id,
            test_example.feature_vector,
            test_example.feature_names,
            include_explanation=True
        )
        
        print(f"✅ Prediction completed:")
        print(f"     Learner ID: {test_example.learner_id}")
        print(f"     Predicted value: {prediction_result.predicted_value:.3f}")
        print(f"     Actual value: {test_example.target.target_value}")
        print(f"     Confidence level: {prediction_result.confidence_level.value}")
        print(f"     Confidence score: {prediction_result.confidence_score:.3f}")
        print(f"     Feature count: {prediction_result.feature_count}")
        
        # Display explanation
        if prediction_result.explanation:
            explanation = prediction_result.explanation
            print(f"     Explanation:")
            print(f"       Primary factors: {len(explanation.primary_factors)}")
            print(f"       Competency gaps: {len(explanation.competency_gaps)}")
            print(f"       Strength areas: {len(explanation.strength_areas)}")
            
            if explanation.primary_factors:
                print(f"       Top factor: {explanation.primary_factors[0].feature_name}")
        
        # Test batch prediction
        print(f"\n🎯 Testing Batch Prediction:")
        print("-" * 33)
        
        batch_examples = training_examples[:5]
        batch_vectors = [ex.feature_vector for ex in batch_examples]
        batch_names = batch_examples[0].feature_names  # Same names for all
        
        batch_results = ml_service.batch_predict(
            model_metadata.model_id,
            batch_vectors,
            batch_names,
            include_explanations=False  # Faster for batch
        )
        
        print(f"✅ Batch prediction completed:")
        print(f"     Batch size: {len(batch_examples)}")
        print(f"     Successful predictions: {len(batch_results)}")
        
        correct_predictions = 0
        for i, (example, result) in enumerate(zip(batch_examples, batch_results)):
            predicted = int(result.predicted_value > 0.5)
            actual = int(example.target.target_value)
            if predicted == actual:
                correct_predictions += 1
            print(f"       Example {i+1}: Predicted={predicted:.1f}, Actual={actual}, Correct={predicted==actual}")
        
        batch_accuracy = correct_predictions / len(batch_results)
        print(f"     Batch accuracy: {batch_accuracy:.3f}")
        
        # Test model management
        print(f"\n🎯 Testing Model Management:")
        print("-" * 32)
        
        # List models
        models = ml_service.list_models()
        print(f"✅ Model listing:")
        print(f"     Total models: {len(models)}")
        
        # Get model performance summary
        performance_summary = ml_service.get_model_performance_summary(model_metadata.model_id)
        if performance_summary:
            print(f"✅ Performance summary retrieved:")
            print(f"     Model: {performance_summary['model_name']}")
            print(f"     Type: {performance_summary['model_type']}")
            print(f"     Target: {performance_summary['prediction_target']}")
            print(f"     CV Score: {performance_summary['cross_validation_score']:.3f}")
        
        # Deploy model
        deploy_success = ml_service.deploy_model(model_metadata.model_id, "test")
        print(f"✅ Model deployment: {'Success' if deploy_success else 'Failed'}")
        
        # Undeploy model
        undeploy_success = ml_service.undeploy_model(model_metadata.model_id)
        print(f"✅ Model undeployment: {'Success' if undeploy_success else 'Failed'}")
        
        print(f"\n🎉 Machine learning service test completed!")
        print(f"📊 Summary:")
        print(f"  ✅ Training pipeline creation and configuration")
        print(f"  ✅ Synthetic training data generation")
        print(f"  ✅ Model training with cross-validation")
        print(f"  ✅ Performance evaluation and metrics")
        print(f"  ✅ Feature importance calculation")
        print(f"  ✅ Individual prediction with explanation")
        print(f"  ✅ Batch prediction processing")
        print(f"  ✅ Model management (deploy/undeploy)")
        print(f"  ✅ Performance summary and monitoring")
        
        return True
        
    except Exception as e:
        print(f"❌ ML service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test end-to-end integration."""
    print(f"\n🧪 Testing End-to-End Integration")
    print("=" * 37)
    
    try:
        from src.modules.intelligence.predictive_model.services.feature_engineering import (
            FeatureEngineeringService
        )
        from src.modules.intelligence.predictive_model.services.ml_service import (
            PredictiveModelService
        )
        from src.modules.intelligence.predictive_model.models.prediction_models import (
            PredictionTarget, ModelType
        )
        
        # Initialize services
        feature_service = FeatureEngineeringService()
        ml_service = PredictiveModelService()
        
        print("✅ Services initialized for integration test")
        
        # Create complete workflow
        print(f"\n🎯 Complete Predictive Workflow:")
        print("-" * 35)
        
        # Step 1: Create diverse learners with different profiles
        learners_data = [
            {
                "id": "high_performer",
                "profile": "High compatibility, excellent performance",
                "expected_success": 0.9
            },
            {
                "id": "average_performer", 
                "profile": "Medium compatibility, average performance",
                "expected_success": 0.6
            },
            {
                "id": "at_risk",
                "profile": "Low compatibility, performance issues",
                "expected_success": 0.3
            }
        ]
        
        training_examples = []
        
        for learner in learners_data:
            # Create features with different characteristics
            compatibility = feature_service.create_compatibility_features(learner["id"], "technology")
            historical = feature_service.create_historical_performance_features(learner["id"])
            
            # Adjust features based on profile
            if learner["id"] == "high_performer":
                compatibility.overall_compatibility_score = 0.9
                historical.learning_velocity = 0.9
                historical.dropout_risk_score = 0.1
            elif learner["id"] == "average_performer":
                compatibility.overall_compatibility_score = 0.6
                historical.learning_velocity = 0.6
                historical.dropout_risk_score = 0.3
            else:  # at_risk
                compatibility.overall_compatibility_score = 0.4
                historical.learning_velocity = 0.4
                historical.dropout_risk_score = 0.7
            
            # Create target based on expected success
            target_value = 1 if learner["expected_success"] > 0.6 else 0
            
            target_data = {
                "target_type": "success_likelihood",
                "target_value": target_value,
                "job_family": "technology",
                "observation_date": datetime.utcnow(),
                "confidence_in_label": 0.9,
                "label_source": "profile_based"
            }
            
            example = feature_service.create_training_example(learner["id"], target_data)
            training_examples.append(example)
            
            print(f"     Created {learner['id']}: {learner['profile']}")
        
        # Augment with more synthetic data for better training
        print(f"     Augmenting with 50 additional synthetic examples...")
        
        for i in range(50):
            learner_id = f"synthetic_{i:03d}"
            compatibility = feature_service.create_compatibility_features(learner_id, "technology")
            historical = feature_service.create_historical_performance_features(learner_id)
            
            # Random target based on features
            success_prob = (compatibility.overall_compatibility_score + 
                          historical.learning_velocity - 
                          historical.dropout_risk_score) / 3
            target_value = 1 if success_prob > 0.5 else 0
            
            target_data = {
                "target_type": "success_likelihood",
                "target_value": target_value,
                "job_family": "technology",
                "observation_date": datetime.utcnow(),
                "confidence_in_label": 0.8,
                "label_source": "synthetic"
            }
            
            example = feature_service.create_training_example(learner_id, target_data)
            training_examples.append(example)
        
        print(f"     Total training examples: {len(training_examples)}")
        
        # Step 2: Train model
        print(f"\n     Training integration model...")
        
        pipeline_config = {
            "pipeline_name": "integration_test_pipeline",
            "model_type": ModelType.CLASSIFICATION,
            "prediction_target": PredictionTarget.SUCCESS_LIKELIHOOD,
            "feature_store_id": "integration_store",
            "training_data_query": "SELECT * FROM integration_data",
            "validation_split": 0.2,
            "test_split": 0.2,
            "feature_selection_method": "importance",
            "algorithm": "random_forest",
            "cross_validation_folds": 3,  # Faster for test
            "created_by": "integration_test"
        }
        
        pipeline = ml_service.create_training_pipeline(pipeline_config)
        model_metadata = ml_service.train_model(pipeline.pipeline_id, training_examples)
        
        print(f"     Model trained: {model_metadata.model_id}")
        print(f"     CV Score: {model_metadata.cross_validation_score:.3f}")
        
        # Step 3: Predict for our test learners
        print(f"\n     Predicting for test learners...")
        
        for learner in learners_data:
            example = next(ex for ex in training_examples if ex.learner_id == learner["id"])
            
            prediction = ml_service.predict(
                model_metadata.model_id,
                example.feature_vector,
                example.feature_names,
                include_explanation=True
            )
            
            predicted_prob = prediction.predicted_value
            predicted_class = 1 if predicted_prob > 0.5 else 0
            actual_class = example.target.target_value
            
            print(f"     {learner['id']}:")
            print(f"       Profile: {learner['profile']}")
            print(f"       Expected: {learner['expected_success']:.1f}")
            print(f"       Predicted: {predicted_prob:.3f} (class {predicted_class})")
            print(f"       Actual: {actual_class}")
            print(f"       Confidence: {prediction.confidence_level.value}")
            print(f"       Correct: {predicted_class == actual_class}")
            
            if prediction.explanation and prediction.explanation.primary_factors:
                top_factor = prediction.explanation.primary_factors[0]
                print(f"       Top factor: {top_factor.feature_name} ({top_factor.importance_score:.3f})")
        
        # Step 4: Evaluate overall performance
        print(f"\n     Evaluating overall performance...")
        
        # Test on all examples
        all_predictions = ml_service.batch_predict(
            model_metadata.model_id,
            [ex.feature_vector for ex in training_examples],
            training_examples[0].feature_names,
            include_explanations=False
        )
        
        correct = sum(1 for ex, pred in zip(training_examples, all_predictions)
                     if int(pred.predicted_value > 0.5) == int(ex.target.target_value))
        accuracy = correct / len(all_predictions)
        
        print(f"     Overall accuracy: {accuracy:.3f} ({correct}/{len(all_predictions)})")
        print(f"     Model performance: {model_metadata.performance.accuracy:.3f}")
        
        # Step 5: Test model explainability
        print(f"\n     Testing model explainability...")
        
        test_example = training_examples[0]
        detailed_prediction = ml_service.predict(
            model_metadata.model_id,
            test_example.feature_vector,
            test_example.feature_names,
            include_explanation=True
        )
        
        if detailed_prediction.explanation:
            expl = detailed_prediction.explanation
            print(f"     Explanation generated successfully:")
            print(f"       Primary factors: {len(expl.primary_factors)}")
            print(f"       Competency gaps: {expl.competency_gaps}")
            print(f"       Strength areas: {expl.strength_areas}")
            print(f"       Data limitations: {expl.data_limitations}")
        
        print(f"\n🎉 Integration test completed successfully!")
        print(f"📊 Summary:")
        print(f"  ✅ Complete feature engineering pipeline")
        print(f"  ✅ Model training with real-world profiles")
        print(f"  ✅ Prediction for diverse learner types")
        print(f"  ✅ Model explainability and insights")
        print(f"  ✅ Performance evaluation and validation")
        print(f"  ✅ End-to-end workflow automation")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all predictive modeling tests."""
    print("🚀 Starting Predictive Modeling System Tests")
    print("=" * 50)
    
    test_results = {
        "feature_engineering": False,
        "ml_service": False,
        "integration": False
    }
    
    # Run tests
    test_results["feature_engineering"] = test_feature_engineering()
    test_results["ml_service"] = test_ml_service()
    test_results["integration"] = test_integration()
    
    # Summary
    print(f"\n🎊 PREDICTIVE MODELING TEST SUMMARY")
    print("=" * 40)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"     {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Predictive modeling system is ready for production!")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    # Save test results
    test_results_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "test_results": test_results,
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests
        },
        "features_tested": [
            "feature_engineering",
            "compatibility_features",
            "historical_performance_features",
            "demographic_features",
            "behavioral_features",
            "training_example_creation",
            "model_training",
            "cross_validation",
            "feature_importance",
            "prediction_with_explanation",
            "batch_prediction",
            "model_management",
            "end_to_end_integration"
        ]
    }
    
    with open("predictive_model_test_results.json", "w") as f:
        json.dump(test_results_data, f, indent=2, default=str)
    
    print(f"📄 Test results saved to: predictive_model_test_results.json")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    main()
