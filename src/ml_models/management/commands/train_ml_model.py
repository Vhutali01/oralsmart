from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ml_models.ml_predictor import MLPRiskPredictor
import os


class Command(BaseCommand):
    help = 'Train the enhanced MLP risk predictor model with validation, feature selection, and hyperparameter tuning'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing training data'
        )
        parser.add_argument(
            '--target-column',
            type=str,
            default='risk_level',
            help='Name of the target column (default: risk_level)'
        )
        parser.add_argument(
            '--create-sample',
            action='store_true',
            help='Create a sample training data file'
        )
        parser.add_argument(
            '--sample-size',
            type=int,
            default=1000,
            help='Number of samples to generate (default: 1000)'
        )
        # Enhanced ML features
        parser.add_argument(
            '--no-feature-selection',
            action='store_true',
            help='Disable feature selection (use all features)'
        )
        parser.add_argument(
            '--no-hyperparameter-tuning',
            action='store_true',
            help='Disable hyperparameter tuning (use default parameters for faster training)'
        )
        parser.add_argument(
            '--feature-selection-method',
            type=str,
            choices=['importance', 'kbest', 'rfe'],
            default='importance',
            help='Feature selection method: importance (Random Forest), kbest (ANOVA F-statistic), rfe (Recursive Feature Elimination)'
        )
        parser.add_argument(
            '--n-features',
            type=int,
            default=40,
            help='Number of features to select (default: 40)'
        )
        parser.add_argument(
            '--fast',
            action='store_true',
            help='Fast training mode: feature selection only, no hyperparameter tuning'
        )
        parser.add_argument(
            '--baseline',
            action='store_true',
            help='Baseline mode: no enhancements, traditional training'
        )

    def handle(self, *args, **options):
        predictor = MLPRiskPredictor()
        
        # Create sample data if requested
        if options['create_sample']:
            csv_file = options['csv_file']
            sample_size = options['sample_size']
            
            self.stdout.write(
                self.style.WARNING(f'Creating sample training data with {sample_size} samples...')
            )
            
            try:
                predictor.create_sample_training_data(csv_file, sample_size)
                self.stdout.write(
                    self.style.SUCCESS(f'Sample data created successfully at {csv_file}')
                )
                return
            except Exception as e:
                raise CommandError(f'Error creating sample data: {str(e)}')
        
        # Train the model with enhanced features
        csv_file = options['csv_file']
        target_column = options['target_column']
        
        # Check if file exists
        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')
        
        # Determine training configuration
        if options['fast']:
            use_feature_selection = True
            use_hyperparameter_tuning = False
            mode_description = "Fast Training (Feature Selection Only)"
        elif options['baseline']:
            use_feature_selection = False
            use_hyperparameter_tuning = False
            mode_description = "Baseline Training (No Enhancements)"
        else:
            use_feature_selection = not options['no_feature_selection']
            use_hyperparameter_tuning = not options['no_hyperparameter_tuning']
            mode_description = "Full Enhanced Training"
        
        feature_selection_method = options['feature_selection_method']
        n_features = options['n_features']
        
        # Display training configuration
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('ENHANCED ML MODEL TRAINING'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(f'📂 Data file: {csv_file}')
        self.stdout.write(f'🎯 Target column: {target_column}')
        self.stdout.write(f'Training mode: {mode_description}')
        self.stdout.write(f'Feature selection: {"✓" if use_feature_selection else "✗"}')
        if use_feature_selection:
            self.stdout.write(f'   └─ Method: {feature_selection_method}')
            self.stdout.write(f'   └─ Features to select: {n_features}')
        self.stdout.write(f'Hyperparameter tuning: {"✓" if use_hyperparameter_tuning else "✗"}')
        self.stdout.write('5-Fold cross-validation: ✓ (always enabled)')
        self.stdout.write('')
        
        if use_hyperparameter_tuning:
            self.stdout.write(
                self.style.WARNING('Hyperparameter tuning enabled - this may take 10-30 minutes...')
            )
        
        self.stdout.write(
            self.style.WARNING('Starting model training...')
        )
        
        try:
            # Train with enhanced features
            results = predictor.train_from_csv(
                csv_file_path=csv_file,
                target_column=target_column,
                use_feature_selection=use_feature_selection,
                use_hyperparameter_tuning=use_hyperparameter_tuning,
                feature_selection_method=feature_selection_method,
                n_features=n_features
            )
            
            # Display comprehensive results
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Model training completed successfully!'))
            self.stdout.write('')
            
            # Basic metrics
            self.stdout.write(self.style.HTTP_INFO('PERFORMANCE METRICS'))
            self.stdout.write('-' * 40)
            self.stdout.write(f'Training accuracy: {results["train_accuracy"]:.4f} ({results["train_accuracy"]*100:.2f}%)')
            self.stdout.write(f'🧪 Test accuracy: {results["test_accuracy"]:.4f} ({results["test_accuracy"]*100:.2f}%)')
            
            # Cross-validation results
            cv_results = results['cross_validation']
            self.stdout.write(f'CV mean accuracy: {cv_results["cv_mean"]:.4f} (±{cv_results["cv_std"]*2:.4f})')
            self.stdout.write(f'   ├─ Min: {cv_results["cv_min"]:.4f}')
            self.stdout.write(f'   └─ Max: {cv_results["cv_max"]:.4f}')
            
            # Data information
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('📁 DATA INFORMATION'))
            self.stdout.write('-' * 40)
            self.stdout.write(f'Training samples: {results["train_samples"]}')
            self.stdout.write(f'🧪 Test samples: {results["test_samples"]}')
            if use_feature_selection and 'original_features' in results:
                self.stdout.write(f'🔢 Original features: {results["original_features"]}')
                self.stdout.write(f'Selected features: {results["features_used"]}')
                reduction = (1 - results["features_used"] / results["original_features"]) * 100
                self.stdout.write(f'Feature reduction: {reduction:.1f}%')
            else:
                self.stdout.write(f'🔢 Features used: {results["features_used"]}')
            
            # Model information
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('MODEL INFORMATION'))
            self.stdout.write('-' * 40)
            self.stdout.write(f'🧠 Model type: {results["model_type"]}')
            self.stdout.write(f'Training iterations: {results["iterations"]}')
            
            # Feature selection results
            if use_feature_selection and results.get('selected_features'):
                self.stdout.write('')
                self.stdout.write(self.style.HTTP_INFO('\n🎯 FEATURE SELECTION RESULTS'))
                self.stdout.write('-' * 40)
                self.stdout.write(f'🔬 Method used: {feature_selection_method}')
                self.stdout.write('🏆 Top 10 selected features:')
                for i, feature in enumerate(results['selected_features'][:10], 1):
                    self.stdout.write(f'   {i:2d}. {feature}')

            # Feature selection results
            if use_feature_selection and results.get('selected_features'):
                self.stdout.write('')
                self.stdout.write(self.style.HTTP_INFO('\n🎯 FEATURE SELECTION RESULTS'))
                self.stdout.write('-' * 40)
                self.stdout.write(f'🔬 Method used: {feature_selection_method}')
                self.stdout.write('All selected features:')
                for i, feature in enumerate(results['selected_features'], 1):
                    self.stdout.write(f'   {i:2d}. {feature}')
            
            # Hyperparameter tuning results
            if use_hyperparameter_tuning and results.get('best_params'):
                self.stdout.write('')
                self.stdout.write(self.style.HTTP_INFO('HYPERPARAMETER TUNING RESULTS'))
                self.stdout.write('-' * 40)
                self.stdout.write('🏆 Best parameters found:')
                for param, value in results['best_params'].items():
                    self.stdout.write(f'   └─ {param}: {value}')
            
            # Model location
            model_info = predictor.get_model_info()
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('💾 MODEL STORAGE'))
            self.stdout.write('-' * 40)
            self.stdout.write(f'📁 Model saved to: {model_info["model_path"]}')
            self.stdout.write(f'📏 Scaler saved to: {model_info.get("scaler_path", "N/A")}')
            
            # Usage recommendations
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('RECOMMENDATIONS'))
            self.stdout.write('-' * 40)
            if cv_results["cv_std"] < 0.02:
                self.stdout.write('Model shows stable performance across folds')
            else:
                self.stdout.write('High variance detected - consider more data or regularization')
            
            if use_feature_selection:
                self.stdout.write('Feature selection reduced model complexity')
            
            if use_hyperparameter_tuning:
                self.stdout.write('Optimal hyperparameters found via grid search')
            
            # Test prediction capability
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('🔮 TESTING PREDICTION CAPABILITY'))
            self.stdout.write('-' * 40)
            try:
                # Create a simple test prediction with proper data structure
                class MockData:
                    def __init__(self, data_dict):
                        for key, value in data_dict.items():
                            setattr(self, key, value)
                
                dummy_dental = MockData({
                    'plaque': 'yes',
                    'dry_mouth': 'no',
                    'enamel_defects': 'yes',
                    'cavitated_lesions': 'yes',
                    'missing_teeth': 'no',
                    'sa_citizen': 'yes',
                    'special_needs': 'no',
                    'caregiver_treatment': 'yes',
                    'appliance': 'no',
                    'fluoride_water': 'yes',
                    'fluoride_toothpaste': 'yes',
                    'topical_fluoride': 'no',
                    'regular_checkups': 'yes',
                    'sealed_pits': 'yes',
                    'restorative_procedures': 'no',
                    'enamel_change': 'yes',
                    'dentin_discoloration': 'no',
                    'white_spot_lesions': 'yes',
                    'multiple_restorations': 'no',
                    'teeth_data': {'11': '1', '12': '0', '21': '2'}  # Sample teeth data
                })
                
                dummy_dietary = MockData({
                    'sweet_sugary_foods': 'yes',
                    'sweet_sugary_foods_daily': '3',
                    'sweet_sugary_foods_weekly': '5',
                    'cold_drinks_juices': 'yes',
                    'cold_drinks_juices_daily': '2',
                    'cold_drinks_juices_weekly': '4',
                    'processed_fruit': 'yes',
                    'processed_fruit_daily': '1',
                    'processed_fruit_weekly': '3',
                    'vegetables': 'yes',
                    'vegetables_daily': '2',
                    'vegetables_weekly': '6',
                    'dairy_products': 'yes',
                    'dairy_products_daily': '2',
                    'water': 'yes',
                    'water_glasses': '6'
                })
                
                prediction_result = predictor.predict_risk(
                    dental_data=dummy_dental,
                    dietary_data=dummy_dietary
                )
                
                self.stdout.write('Prediction test successful!')
                self.stdout.write(f'   └─ Sample prediction: {prediction_result["risk_level"]} risk')
                self.stdout.write(f'   └─ Confidence: {prediction_result["confidence"]:.2%}')
                
            except Exception as e:
                self.stdout.write(f'Prediction test failed: {str(e)}')
            
            # Final summary
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎯 TRAINING SUMMARY'))
            self.stdout.write('=' * 60)
            self.stdout.write(f'Model trained successfully with {results["test_accuracy"]:.2%} test accuracy')
            self.stdout.write(f'Cross-validation mean: {cv_results["cv_mean"]:.2%}')
            if use_feature_selection:
                self.stdout.write(f'Feature selection: {results["original_features"]} → {results["features_used"]} features')
            if use_hyperparameter_tuning:
                self.stdout.write('Hyperparameters optimized via GridSearchCV')
            self.stdout.write('Model ready for production use!')
            
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('Training failed!'))
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise CommandError(f'Error training model: {str(e)}')
