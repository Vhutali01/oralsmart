import numpy as np
import pandas as pd
import pickle
import joblib
import os
import logging
from typing import Optional, Dict, Any, Tuple
import os
import pickle
import logging
import numpy as np
import pandas as pd
import random
import re
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.ensemble import RandomForestClassifier
from django.db import models
from django.conf import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check GPU availability
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logger.info(f"Using device: {device}")
if torch.cuda.is_available():
    logger.info(f"GPU: {torch.cuda.get_device_name()}")
    logger.info(f"PyTorch version: {torch.__version__}")

class MLPNet(nn.Module):
    """
    PyTorch GPU-accelerated Multi-Layer Perceptron for oral health risk prediction.
    """
    def __init__(self, input_size, hidden_sizes, num_classes=3, dropout=0.2):
        super(MLPNet, self).__init__()
        layers = []
        
        # Input layer
        layers.append(nn.Linear(input_size, hidden_sizes[0]))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(dropout))
        
        # Hidden layers
        for i in range(len(hidden_sizes) - 1):
            layers.append(nn.Linear(hidden_sizes[i], hidden_sizes[i + 1]))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
        
        # Output layer
        layers.append(nn.Linear(hidden_sizes[-1], num_classes))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)

class MLPRiskPredictor:
    """
    Multi-Layer Perceptron (MLP) Neural Network for oral health risk prediction.
    
    This class implements a neural network model that predicts risk levels (low/medium/high) 
    based on dental assessment data, dietary information, and patient demographics.
    
    The model can work with:
    - Only dental data
    - Only dietary data  
    - Both dental and dietary data
    - Partial/missing data combinations
    
    Features include data availability indicators to help the model understand
    when certain types of data are missing.
    """
    def __init__(self) -> None:
        self.model = None
        self.pytorch_model = None  # GPU-accelerated PyTorch model
        self.scaler = None
        self.is_trained = False
        self.use_gpu = torch.cuda.is_available()
        self.device = device
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'saved_models', 'risk_predictor.pkl')
        self.pytorch_model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'saved_models', 'risk_predictor.pth')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'ml_models', 'saved_models', 'scaler.pkl')
        
        # Define field categories as class attributes for reuse
        self.dental_binary_fields = [
            'sa_citizen', 'special_needs', 'caregiver_treatment',
            'appliance', 'plaque', 'dry_mouth', 'enamel_defects',
            'fluoride_water', 'fluoride_toothpaste', 'topical_fluoride',
            'regular_checkups', 'sealed_pits', 'restorative_procedures',
            'enamel_change', 'dentin_discoloration', 'white_spot_lesions',
            'cavitated_lesions', 'multiple_restorations', 'missing_teeth'
        ]
        
        self.dietary_yes_no_fields = [
            'sweet_sugary_foods', 'sweet_sugary_foods_bedtime',
            'takeaways_processed_foods',
            'fresh_fruit', 'fresh_fruit_bedtime',
            'cold_drinks_juices', 'cold_drinks_juices_bedtime',
            'processed_fruit', 'processed_fruit_bedtime',
            'spreads', 'spreads_bedtime',
            'added_sugars', 'added_sugars_bedtime',
            'salty_snacks',
            'dairy_products',
            'vegetables',
            'water'
        ]
        
        self.dietary_text_fields = [
            'sweet_sugary_foods_daily', 'sweet_sugary_foods_weekly', 'sweet_sugary_foods_timing',
            'takeaways_processed_foods_daily', 'takeaways_processed_foods_weekly',
            'fresh_fruit_daily', 'fresh_fruit_weekly', 'fresh_fruit_timing',
            'cold_drinks_juices_daily', 'cold_drinks_juices_weekly', 'cold_drinks_juices_timing',
            'processed_fruit_daily', 'processed_fruit_weekly', 'processed_fruit_timing',
            'spreads_daily', 'spreads_weekly', 'spreads_timing',
            'added_sugars_daily', 'added_sugars_weekly', 'added_sugars_timing',
            'salty_snacks_daily', 'salty_snacks_weekly', 'salty_snacks_timing',
            'dairy_products_daily', 'dairy_products_weekly',
            'vegetables_daily', 'vegetables_weekly',
            'water_timing', 'water_glasses'
        ]
        
        # Feature names mapping to assessment model fields
        # DentalScreening model fields + calculated DMFT score + DietaryScreening model fields
        self.feature_names = [
            # Section 1 - DentalScreening Demographics
            'sa_citizen', 'special_needs', 'caregiver_treatment',      

            # Section 2 - DentalScreening Oral Health Status
            'appliance', 'plaque', 'dry_mouth', 'enamel_defects',       

            # Section 3 - DentalScreening Fluoride Exposure
            'fluoride_water', 'fluoride_toothpaste', 'topical_fluoride', 'regular_checkups',
            
            # Section 4 - DentalScreening Clinical Findings
            'sealed_pits', 'restorative_procedures',
            'enamel_change', 'dentin_discoloration', 'white_spot_lesions',
            'cavitated_lesions', 'multiple_restorations', 'missing_teeth',

            # Section 5 - DentalScreening Teeth Data (calculated DMFT score)
            'total_dmft_score',

            # DietaryScreening fields
            # Section 1: Sweet/Sugary Foods
            'sweet_sugary_foods', 'sweet_sugary_foods_daily', 'sweet_sugary_foods_weekly', 
            'sweet_sugary_foods_timing', 'sweet_sugary_foods_bedtime',
            
            # Section 2: Take-aways and Processed Foods
            'takeaways_processed_foods', 'takeaways_processed_foods_daily', 'takeaways_processed_foods_weekly',
            
            # Section 3: Fresh Fruit
            'fresh_fruit', 'fresh_fruit_daily', 'fresh_fruit_weekly', 
            'fresh_fruit_timing', 'fresh_fruit_bedtime',
            
            # Section 4: Cold Drinks, Juices and Flavoured Water and Milk
            'cold_drinks_juices', 'cold_drinks_juices_daily', 'cold_drinks_juices_weekly',
            'cold_drinks_juices_timing', 'cold_drinks_juices_bedtime',
            
            # Section 5: Processed Fruit
            'processed_fruit', 'processed_fruit_daily', 'processed_fruit_weekly',
            'processed_fruit_timing', 'processed_fruit_bedtime',
            
            # Section 6: Spreads
            'spreads', 'spreads_daily', 'spreads_weekly', 'spreads_timing', 'spreads_bedtime',
            
            # Section 7: Added Sugars
            'added_sugars', 'added_sugars_daily', 'added_sugars_weekly',
            'added_sugars_timing', 'added_sugars_bedtime',
            
            # Section 8: Salty Snacks
            'salty_snacks', 'salty_snacks_daily', 'salty_snacks_weekly', 'salty_snacks_timing',
            
            # Section 9: Dairy Products
            'dairy_products', 'dairy_products_daily', 'dairy_products_weekly',
            
            # Section 10: Vegetables
            'vegetables', 'vegetables_daily', 'vegetables_weekly',
            
            # Section 11: Water
            'water', 'water_timing', 'water_glasses',
            
            # Data availability indicators
            'has_dental_data', 'has_dietary_data'
        ]
        
        # Try to load existing model
        self.load_model()

    def prepare_features(self, dental_data=None, dietary_data=None):
        """
        Prepare features from dental and dietary data for ML prediction.
        
        Args:
            dental_data: Optional object containing dental assessment data
            dietary_data: Optional object containing dietary assessment data
            
        Returns:
            numpy array: Feature vector ready for model prediction
        """
        try:
            features = {}

            # Data availability indicators
            has_dental_data = dental_data is not None
            has_dietary_data = dietary_data is not None
            features['has_dental_data'] = 1 if has_dental_data else 0
            features['has_dietary_data'] = 1 if has_dietary_data else 0

            # Handle dental data (can be None)
            if dental_data:
                for field in self.dental_binary_fields:
                    value = getattr(dental_data, field, 'no')
                    features[field] = 1 if value == 'yes' else 0

                # DMFT score from teeth_data
                dmft_result = self.calculate_dmft_score(dental_data.teeth_data)
                features['total_dmft_score'] = dmft_result['dmft']
            else:
                # Set all dental fields to 0 if no dental data provided
                for field in self.dental_binary_fields:
                    features[field] = 0
                
                # Set DMFT scores to 0
                features['total_dmft_score'] = 0

            # Handle dietary data (can be None)
            if dietary_data:
                # Process yes/no dietary fields
                for field in self.dietary_yes_no_fields:
                    value = getattr(dietary_data, field, 'no')
                    features[field] = 1 if value == 'yes' else 0
                
                # Process text/quantity fields
                for field in self.dietary_text_fields:
                    value = getattr(dietary_data, field, None)
                    features[field] = self._encode_frequency_quantity(value)
                    
            else:
                # Set all dietary fields to 0 if no dietary data provided
                for field in self.dietary_yes_no_fields + self.dietary_text_fields:
                    features[field] = 0

            # Convert to vector
            return np.array([features.get(f, 0) for f in self.feature_names]).reshape(1, -1)
        
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            raise ValueError(f"Failed to prepare features: {str(e)}")
        

    def calculate_dmft_score(self, teeth_data):
        """
        Calculate DMFT (Decayed, Missing, Filled Teeth) score with components.
        
        Args:
            teeth_data: Dictionary containing teeth status data (can be None)
            
        Returns:
            dict: {'d': decayed_count, 'm': missing_count, 'f': filled_count, 'dmft': total}
        """
        try:
            d = m = f = 0  # Initialize decayed, missing, filled
            
            if not teeth_data:
                return {'d': 0, 'm': 0, 'f': 0, 'dmft': 0}

            for tooth, status in teeth_data.items():
                if status in ['1', 'B']:  # Decayed
                    d += 1
                elif status in ['2', 'C']:  # Filled
                    f += 1
                elif status in ['3', '4', 'D', 'E']:  # Missing
                    m += 1

            dmft = d + m + f
            return {
                'd': d,
                'm': m,
                'f': f,
                'dmft': dmft
            }
        
        except Exception as e:
            logger.error(f"Error calculating DMFT score: {str(e)}")
            return {'d': 0, 'm': 0, 'f': 0, 'dmft': 0}

    def perform_feature_selection(self, X, y, method='importance', k_features=50):
        """
        Perform feature selection using various methods.
        
        Args:
            X: Features dataframe
            y: Target variable
            method: Method to use ('importance', 'kbest', 'rfe')
            k_features: Number of features to select
            
        Returns:
            Tuple containing (selected_features_mask, feature_importance_scores, selected_feature_names)
        """
        try:
            logger.info(f"Performing feature selection using {method} method...")
            
            if method == 'importance':
                # Use Random Forest feature importance
                rf = RandomForestClassifier(n_estimators=100, random_state=42)
                rf.fit(X, y)
                
                # Get feature importance scores
                importance_scores = rf.feature_importances_
                
                # Select top k features
                feature_indices = np.argsort(importance_scores)[::-1][:k_features]
                selected_mask = np.zeros(len(self.feature_names), dtype=bool)
                selected_mask[feature_indices] = True
                
                selected_features = [self.feature_names[i] for i in feature_indices]
                
                logger.info(f"Selected {k_features} features using Random Forest importance")
                
            elif method == 'kbest':
                # Use K-best features based on ANOVA F-statistic
                selector = SelectKBest(score_func=f_classif, k=k_features)
                selector.fit(X, y)
                
                selected_mask = selector.get_support()
                importance_scores = selector.scores_
                selected_features = [self.feature_names[i] for i, selected in enumerate(selected_mask) if selected]
                
                logger.info(f"Selected {k_features} features using K-best ANOVA F-statistic")
                
            elif method == 'rfe':
                # Use Recursive Feature Elimination
                estimator = RandomForestClassifier(n_estimators=50, random_state=42)
                selector = RFE(estimator, n_features_to_select=k_features)
                selector.fit(X, y)
                
                selected_mask = selector.support_
                importance_scores = selector.ranking_
                selected_features = [self.feature_names[i] for i, selected in enumerate(selected_mask) if selected]
                
                logger.info(f"Selected {k_features} features using Recursive Feature Elimination")
                
            else:
                raise ValueError(f"Unknown feature selection method: {method}")
            
            return selected_mask, importance_scores, selected_features
            
        except Exception as e:
            logger.error(f"Error in feature selection: {str(e)}")
            raise
    
    def perform_hyperparameter_tuning(self, X_train, y_train):
        """
        Perform hyperparameter tuning using GridSearchCV.
        
        Args:
            X_train: Training features
            y_train: Training targets
            
        Returns:
            Best parameters and best estimator
        """
        try:
            logger.info("Starting hyperparameter tuning with GridSearchCV...")
            
            # Define parameter grid for MLPClassifier
            # Testing multiple solvers: Adam (best for high-dim data), SGD (good for large datasets)
            # L-BFGS excluded as it doesn't converge well with many features (68+)
            param_grid = {
                'hidden_layer_sizes': [
                    (64, 32),
                    (64, 32, 16),
                    (100, 50),
                    (128, 64, 32),
                    (64, 64),
                    (128, 64)
                ],
                'alpha': [0.0001, 0.001, 0.01, 0.0005, 0.005, 0.05],
                'learning_rate_init': [0.005, 0.05, 0.5, 0.001, 0.01, 0.1],
                'activation': ['relu', 'tanh', 'logistic'],
                'solver': ['adam', 'sgd'],  # Test both Adam and SGD solvers
                'max_iter': [1000, 2000, 3000]  # Increased iterations for better convergence
            }
            
            # Create base model
            mlp = MLPClassifier(
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1,
                n_iter_no_change=15,  # Increased patience
                tol=1e-4             # Tolerance for optimization
            )
            
            # Create GridSearchCV with 5-fold cross-validation
            grid_search = GridSearchCV(
                estimator=mlp,
                param_grid=param_grid,
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
                scoring='accuracy',
                n_jobs=-1,
                verbose=1
            )
            
            # Fit grid search
            logger.info("Fitting GridSearchCV (this may take a while)...")
            grid_search.fit(X_train, y_train)
            
            logger.info(f"Best parameters: {grid_search.best_params_}")
            logger.info(f"Best cross-validation score: {grid_search.best_score_:.4f}")
            
            return grid_search.best_params_, grid_search.best_estimator_
            
        except Exception as e:
            logger.error(f"Error in hyperparameter tuning: {str(e)}")
            raise
    
    def perform_gpu_hyperparameter_tuning(self, X_train, y_train):
        """
        Perform GPU-accelerated hyperparameter tuning using PyTorch.
        
        Args:
            X_train: Training features (numpy array or pandas DataFrame)
            y_train: Training targets (numpy array or pandas Series)
            
        Returns:
            Best parameters and trained PyTorch model
        """
        try:
            import time
            start_time = time.time()
            
            logger.info("Starting GPU-accelerated hyperparameter tuning with PyTorch...")
            
            # Convert data to PyTorch tensors
            if hasattr(X_train, 'values'):
                X_tensor = torch.FloatTensor(X_train.values).to(self.device)
            else:
                # X_train is already a numpy array
                X_tensor = torch.FloatTensor(X_train).to(self.device)
            
            if hasattr(y_train, 'values'):
                y_tensor = torch.LongTensor(y_train.values).to(self.device)
            else:
                # y_train is already a numpy array
                y_tensor = torch.LongTensor(y_train).to(self.device)
            
            # Define parameter grid for PyTorch model
            param_grid = {
                'hidden_sizes': [
                    [64, 32],
                    [64, 32, 16],
                    # [100, 50],
                    # [128, 64, 32],
                    # # [64, 64],
                    [128, 64]
                ],
                'learning_rate': [0.001, 0.01, 0.1],
                'dropout': [0.2, 0.1],
                'batch_size': [128],
                'epochs': [150],
                'optimizer': ['adam', "adamw"] # 'optimizer': ['adam', 'adamw']  # Test both Adam and AdamW optimizers
            }
            
            # Calculate total combinations
            total_combinations = (len(param_grid['hidden_sizes']) * 
                                len(param_grid['learning_rate']) * 
                                len(param_grid['dropout']) * 
                                len(param_grid['batch_size']) * 
                                len(param_grid['epochs']) *
                                len(param_grid['optimizer']))
            
            logger.info(f"🎯 Testing {total_combinations} parameter combinations on GPU")
            
            best_score = 0
            best_params = None
            best_model = None
            
            combination_count = 0
            
            # Grid search with 5-fold cross-validation
            for hidden_sizes in param_grid['hidden_sizes']:
                for lr in param_grid['learning_rate']:
                    for dropout in param_grid['dropout']:
                        for batch_size in param_grid['batch_size']:
                            for epochs in param_grid['epochs']:
                                for optimizer_name in param_grid['optimizer']:
                                    combination_count += 1
                                    
                                    # 5-fold cross-validation
                                    cv_scores = []
                                    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                                    
                                    for train_idx, val_idx in kf.split(X_train, y_train):
                                        # Split data for this fold
                                        X_fold_train = X_tensor[train_idx]
                                        X_fold_val = X_tensor[val_idx]
                                        y_fold_train = y_tensor[train_idx]
                                        y_fold_val = y_tensor[val_idx]
                                        
                                        # Create and train model
                                        input_size = X_tensor.shape[1]
                                        model = MLPNet(input_size, hidden_sizes, dropout=dropout).to(self.device)
                                        criterion = nn.CrossEntropyLoss()
                                        
                                        # Create optimizer based on parameter
                                        if optimizer_name == 'adam':
                                            optimizer = optim.Adam(model.parameters(), lr=lr)
                                        elif optimizer_name == 'adamw':
                                            optimizer = optim.AdamW(model.parameters(), lr=lr)
                                        else:
                                            optimizer = optim.Adam(model.parameters(), lr=lr)  # fallback
                                        
                                        # Create data loader
                                        train_dataset = TensorDataset(X_fold_train, y_fold_train)
                                        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
                                        
                                        # Training loop
                                        model.train()
                                        for epoch in range(epochs):
                                            for batch_X, batch_y in train_loader:
                                                optimizer.zero_grad()
                                                outputs = model(batch_X)
                                                loss = criterion(outputs, batch_y)
                                                loss.backward()
                                                optimizer.step()
                                            
                                            # Early stopping check (every 100 epochs)
                                            if epoch % 100 == 0:
                                                model.eval()
                                                with torch.no_grad():
                                                    val_outputs = model(X_fold_val)
                                                    val_loss = criterion(val_outputs, y_fold_val)
                                                    if val_loss.item() < 0.01:  # Good enough, stop early
                                                        break
                                                model.train()
                                        
                                        # Evaluate on validation set
                                        model.eval()
                                        with torch.no_grad():
                                            val_outputs = model(X_fold_val)
                                            _, val_predicted = torch.max(val_outputs.data, 1)
                                            val_accuracy = (val_predicted == y_fold_val).float().mean().item()
                                            cv_scores.append(val_accuracy)
                                    
                                    # Calculate mean CV score for this parameter combination
                                    mean_cv_score = sum(cv_scores) / len(cv_scores)
                                    
                                    # Update best parameters if this is better
                                    if mean_cv_score > best_score:
                                        best_score = mean_cv_score
                                        best_params = {
                                            'hidden_sizes': hidden_sizes,
                                            'learning_rate': lr,
                                            'dropout': dropout,
                                            'batch_size': batch_size,
                                            'epochs': epochs,
                                            'optimizer': optimizer_name
                                        }
                                        
                                        # Train final model with best parameters
                                        input_size = X_tensor.shape[1]
                                        best_model = MLPNet(input_size, hidden_sizes, dropout=dropout).to(self.device)
                                        criterion = nn.CrossEntropyLoss()
                                        
                                        # Create optimizer for final model
                                        if optimizer_name == 'adam':
                                            optimizer = optim.Adam(best_model.parameters(), lr=lr)
                                        elif optimizer_name == 'adamw':
                                            optimizer = optim.AdamW(best_model.parameters(), lr=lr)
                                        else:
                                            optimizer = optim.Adam(best_model.parameters(), lr=lr)
                                        
                                        # Train final model with full dataset
                                        train_dataset = TensorDataset(X_tensor, y_tensor)
                                        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
                                        
                                        best_model.train()
                                        for epoch in range(epochs):
                                            for batch_X, batch_y in train_loader:
                                                optimizer.zero_grad()
                                                outputs = best_model(batch_X)
                                                loss = criterion(outputs, batch_y)
                                                loss.backward()
                                                optimizer.step()
                                    
                                    # Progress logging
                                    if combination_count % 5 == 0:  # Log more frequently since we have fewer combinations
                                        elapsed_time = time.time() - start_time
                                        logger.info(f"⚡ Progress: {combination_count}/{total_combinations} "
                                                  f"({combination_count/total_combinations*100:.1f}%) "
                                                  f"Best score: {best_score:.4f} "
                                                  f"Time: {elapsed_time/60:.1f}m")
            
            end_time = time.time()
            total_time = end_time - start_time
            
            logger.info(f"🏁 GPU hyperparameter tuning completed!")
            logger.info(f"Total time: {total_time/3600:.2f} hours ({total_time/60:.1f} minutes)")
            logger.info(f"🎯 Best parameters: {best_params}")
            logger.info(f"Best CV score: {best_score:.4f}")
            logger.info(f"GPU performance: {total_combinations*5/total_time:.2f} models/second")
            
            return best_params, best_model
            
        except Exception as e:
            logger.error(f"Error in GPU hyperparameter tuning: {str(e)}")
            # Fallback to CPU if GPU fails
            logger.info("Falling back to CPU hyperparameter tuning...")
            return self.perform_hyperparameter_tuning(X_train, y_train)
    
    def perform_cross_validation(self, X, y, model, cv_folds=5):
        """
        Perform k-fold cross-validation.
        
        Args:
            X: Features
            y: Target variable
            model: Model to validate
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary containing CV results
        """
        try:
            logger.info(f"Performing {cv_folds}-fold cross-validation...")
            
            # Create stratified k-fold
            skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
            
            # Perform cross-validation
            cv_scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy')
            
            cv_results = {
                'cv_scores': cv_scores.tolist(),
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'cv_min': cv_scores.min(),
                'cv_max': cv_scores.max()
            }
            
            logger.info(f"Cross-validation results:")
            logger.info(f"  Mean accuracy: {cv_results['cv_mean']:.4f} (+/- {cv_results['cv_std'] * 2:.4f})")
            logger.info(f"  Min accuracy: {cv_results['cv_min']:.4f}")
            logger.info(f"  Max accuracy: {cv_results['cv_max']:.4f}")
            
            return cv_results
            
        except Exception as e:
            logger.error(f"Error in cross-validation: {str(e)}")
            raise
    
    def display_feature_importance(self, feature_importance_scores, selected_features, method='importance', top_n=20):
        """
        Display feature importance results in a readable format.
        
        Args:
            feature_importance_scores: Array of importance scores
            selected_features: List of selected feature names
            method: Method used for feature selection
            top_n: Number of top features to display
        """
        try:
            if feature_importance_scores is None or selected_features is None:
                logger.info("No feature importance data available")
                return
            
            logger.info(f"\n=== TOP {top_n} FEATURES ({method.upper()}) ===")
            
            # Create feature-score pairs and sort based on method
            feature_scores = list(zip(selected_features, feature_importance_scores))
            
            if method in ['importance', 'kbest']:
                # For Random Forest importance and ANOVA F-statistic, higher is better
                feature_scores.sort(key=lambda x: x[1], reverse=True)
            elif method == 'rfe':
                # For RFE, lower ranking is better (1 is best)
                feature_scores.sort(key=lambda x: x[1])
            
            # Display top features
            for i, (feature, score) in enumerate(feature_scores[:top_n], 1):
                if method == 'rfe':
                    logger.info(f"{i:2d}. {feature:<30} (Rank: {score})")
                else:
                    logger.info(f"{i:2d}. {feature:<30} (Score: {score:.4f})")
            
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Error displaying feature importance: {str(e)}")
    
    def get_model_validation_summary(self, results):
        """
        Generate a comprehensive validation summary.
        
        Args:
            results: Training results dictionary
            
        Returns:
            Formatted validation summary string
        """
        try:
            summary = []
            summary.append("=" * 60)
            summary.append("MODEL VALIDATION SUMMARY")
            summary.append("=" * 60)
            
            # Basic metrics
            summary.append(f"Training Accuracy:     {results['train_accuracy']:.4f}")
            summary.append(f"Test Accuracy:         {results['test_accuracy']:.4f}")
            
            # Cross-validation metrics
            if 'cross_validation' in results:
                cv = results['cross_validation']
                summary.append(f"CV Mean Accuracy:      {cv['cv_mean']:.4f} (+/- {cv['cv_std'] * 2:.4f})")
                summary.append(f"CV Min Accuracy:       {cv['cv_min']:.4f}")
                summary.append(f"CV Max Accuracy:       {cv['cv_max']:.4f}")
            
            # Data info
            summary.append(f"Training Samples:      {results['train_samples']}")
            summary.append(f"Test Samples:          {results['test_samples']}")
            
            # Feature info
            if results.get('selected_features'):
                summary.append(f"Original Features:     {results['original_features']}")
                summary.append(f"Selected Features:     {results['features_used']}")
                summary.append(f"Feature Reduction:     {(1 - results['features_used']/results['original_features'])*100:.1f}%")
            else:
                summary.append(f"Features Used:         {results['features_used']}")
            
            # Model info
            summary.append(f"Model Type:            {results['model_type']}")
            summary.append(f"Training Iterations:   {results.get('iterations', 'N/A')}")
            
            # Hyperparameter tuning
            if results.get('hyperparameter_tuning_used'):
                summary.append("Hyperparameter Tuning: Enabled")
                if results.get('best_params'):
                    summary.append("Best Parameters:")
                    for param, value in results['best_params'].items():
                        summary.append(f"  {param}: {value}")
            else:
                summary.append("Hyperparameter Tuning: Disabled")
            
            # Feature selection
            if results.get('feature_selection_method'):
                summary.append(f"Feature Selection:     {results['feature_selection_method']}")
            else:
                summary.append("Feature Selection:     None")
            
            summary.append("=" * 60)
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Error generating validation summary: {str(e)}")
            return "Error generating validation summary"

    def train_from_csv(self, csv_file_path: str, target_column: str = 'risk_level', 
                      use_feature_selection: bool = True, use_hyperparameter_tuning: bool = True,
                      feature_selection_method: str = 'importance', n_features: int = 50) -> Dict[str, Any]:
        """
        Train the model using data from a CSV file with enhanced validation, feature selection, and hyperparameter tuning.
        
        Args:
            csv_file_path: Path to the CSV file containing training data
            target_column: Name of the column containing the target variable (risk levels)
            use_feature_selection: Whether to perform feature selection
            use_hyperparameter_tuning: Whether to perform hyperparameter tuning
            feature_selection_method: Method for feature selection ('importance', 'kbest', 'rfe')
            n_features: Number of features to select
            
        Returns:
            Dict containing training metrics and model information
        """
        try:
            logger.info(f"Loading training data from {csv_file_path}")
            
            # Load data
            df = pd.read_csv(csv_file_path)
            
            # Validate required columns
            missing_features = set(self.feature_names) - set(df.columns)
            if missing_features:
                logger.warning(f"Missing features in CSV: {missing_features}")
            
            if target_column not in df.columns:
                raise ValueError(f"Target column '{target_column}' not found in CSV")
            
            # Prepare features and target
            X = df[self.feature_names].fillna(0)  # Fill missing values with 0
            y = df[target_column]
            
            # Convert target to 3-class if needed (low=0, medium=1, high=2)
            if y.dtype == 'object':
                y = y.map({
                    'low': 0, 'Low': 0,
                    'medium': 1, 'Medium': 1,
                    'high': 2, 'High': 2
                })
            
            logger.info(f"Dataset shape: {X.shape}")
            logger.info(f"Class distribution: {y.value_counts().to_dict()}")
            
            # Feature Selection
            selected_features = None
            feature_importance_scores = None
            if use_feature_selection and n_features < len(self.feature_names):
                logger.info(f"Performing feature selection...")
                selected_mask, importance_scores, selected_feature_names = self.perform_feature_selection(
                    X, y, method=feature_selection_method, k_features=n_features
                )
                
                # Update features to use only selected ones
                X = X.iloc[:, selected_mask]
                selected_features = selected_feature_names
                feature_importance_scores = importance_scores
                
                logger.info(f"Reduced features from {len(self.feature_names)} to {len(selected_features)}")
                logger.info(f"Top 10 selected features: {selected_features[:10]}")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features (crucial for neural networks)
            self.scaler = StandardScaler()
            x_train_scaled = self.scaler.fit_transform(X_train)
            x_test_scaled = self.scaler.transform(X_test)
            
            # Hyperparameter Tuning
            best_params = None
            if use_hyperparameter_tuning:
                if self.use_gpu:
                    logger.info("Using GPU-accelerated hyperparameter tuning...")
                    best_params, best_pytorch_model = self.perform_gpu_hyperparameter_tuning(x_train_scaled, y_train)
                    self.pytorch_model = best_pytorch_model
                    
                    # Create equivalent sklearn model for compatibility
                    self.model = MLPClassifier(
                        hidden_layer_sizes=tuple(best_params['hidden_sizes']),
                        learning_rate_init=best_params['learning_rate'],
                        random_state=42,
                        max_iter=best_params['epochs']
                    )
                    # Fit sklearn model for compatibility with existing code
                    self.model.fit(x_train_scaled, y_train)
                else:
                    logger.info("Using CPU hyperparameter tuning...")
                    best_params, best_model = self.perform_hyperparameter_tuning(x_train_scaled, y_train)
                    self.model = best_model
            else:
                # Use default parameters
                logger.info("Using default parameters...")
                self.model = MLPClassifier(
                    hidden_layer_sizes=(64, 32, 16),  # 3 hidden layers
                    activation='relu',                 # ReLU activation
                    solver='adam',                     # Adam optimizer (better for large datasets)
                    alpha=0.001,                      # L2 regularization
                    batch_size='auto',                # Automatic batch size
                    learning_rate='adaptive',         # Adaptive learning rate
                    learning_rate_init=0.001,         # Initial learning rate
                    max_iter=2000,                    # Increased maximum iterations
                    random_state=42,                  # Reproducibility
                    early_stopping=True,              # Early stopping
                    validation_fraction=0.1,          # Validation set size
                    n_iter_no_change=15,              # Increased patience for early stopping
                    tol=1e-4                          # Tolerance for optimization
                )
                
                logger.info("Training MLP model with default parameters...")
                self.model.fit(x_train_scaled, y_train)
            
            # Cross-validation on the full training set
            logger.info("Performing 5-fold cross-validation...")
            cv_results = self.perform_cross_validation(x_train_scaled, y_train, self.model, cv_folds=5)
            
            # Final evaluation on test set
            train_pred = self.model.predict(x_train_scaled)
            test_pred = self.model.predict(x_test_scaled)
            
            train_accuracy = accuracy_score(y_train, train_pred)
            test_accuracy = accuracy_score(y_test, test_pred)
            
            # Update feature names if feature selection was used
            if use_feature_selection and selected_features:
                self.feature_names = selected_features
            
            # Save model and scaler
            self.save_model()
            self.is_trained = True
            
            # Convert feature importance scores to list for JSON serialization
            feature_importance_list = None
            if feature_importance_scores is not None:
                try:
                    # Convert numpy array or similar to list
                    feature_importance_list = np.array(feature_importance_scores).tolist()
                except Exception as e:
                    logger.warning(f"Could not convert feature importance scores to list: {e}")
                    feature_importance_list = None
            
            # Get classification report as dict for precision, recall, f1
            classification_report_str = classification_report(y_test, test_pred)
            classification_report_dict = classification_report(y_test, test_pred, output_dict=True)

            results = {
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'original_features': len(df[self.feature_names].columns) if not use_feature_selection else len(df.columns) - 1,
                'features_used': len(self.feature_names),
                'selected_features': selected_features if use_feature_selection else None,
                'feature_importance_scores': feature_importance_list,
                'best_params': best_params,
                'cross_validation': cv_results,
                'classification_report': classification_report_str,
                'classification_report_dict': classification_report_dict,
                'confusion_matrix': confusion_matrix(y_test, test_pred).tolist(),
                'model_type': 'MLPClassifier',
                'iterations': self.model.n_iter_,
                'loss': self.model.loss_,
                'feature_selection_method': feature_selection_method if use_feature_selection else None,
                'hyperparameter_tuning_used': use_hyperparameter_tuning
            }
            
            logger.info(f"Model training completed successfully!")
            logger.info(f"Final test accuracy: {test_accuracy:.4f}")
            logger.info(f"Cross-validation mean accuracy: {cv_results['cv_mean']:.4f} (+/- {cv_results['cv_std'] * 2:.4f})")
            if use_feature_selection:
                logger.info(f"Feature selection reduced features from {results['original_features']} to {results['features_used']}")
                # Display top features
                self.display_feature_importance(feature_importance_scores, selected_features, feature_selection_method)
            if use_hyperparameter_tuning:
                logger.info(f"Best hyperparameters: {best_params}")
            
            # Display comprehensive validation summary
            validation_summary = self.get_model_validation_summary(results)
            logger.info(f"\n{validation_summary}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error training model from CSV: {str(e)}")
            raise ValueError(f"Failed to train model: {str(e)}")
    
    def predict_risk(self, dental_data=None, dietary_data=None) -> Dict[str, Any]:
        """
        Predict risk level for given patient data.
        
        Args:
            dental_data: Optional object containing dental assessment data
            dietary_data: Optional object containing dietary assessment data
            
        Returns:
            Dict containing prediction results
        """
        try:
            if not self.is_trained or (self.model is None and self.pytorch_model is None):
                raise ValueError("Model is not trained. Please train the model first.")
            
            # Check that at least one type of data is provided
            if dental_data is None and dietary_data is None:
                raise ValueError("At least one of dental_data or dietary_data must be provided.")
            
            # Prepare features
            features = self.prepare_features(dental_data, dietary_data)
            
            # Scale features
            if self.scaler is None:
                raise ValueError("Scaler not available. Please retrain the model.")
            
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            if self.use_gpu and self.pytorch_model is not None:
                # Use GPU PyTorch model
                features_tensor = torch.FloatTensor(features_scaled).to(self.device)
                self.pytorch_model.eval()
                with torch.no_grad():
                    outputs = self.pytorch_model(features_tensor)
                    prediction_proba = torch.softmax(outputs, dim=1).cpu().numpy()[0]
                    prediction = prediction_proba.argmax()
                logger.info("Using GPU PyTorch model for prediction")
            elif self.model is not None:
                # Use CPU sklearn model
                prediction = self.model.predict(features_scaled)[0]
                prediction_proba = self.model.predict_proba(features_scaled)[0]
                logger.info("Using CPU sklearn model for prediction")
            else:
                raise ValueError("No prediction model available")
            
            # Get feature importance (different approaches for different models)
            feature_importance = {}
            top_features = []
            
            # Check model type and use appropriate method
            if self.model is not None:
                model_type = self.model.__class__.__name__
                
                if model_type == 'MLPClassifier':
                    # MLP: Use first layer weights as proxy for feature importance
                    try:
                        # Use getattr to safely access coefs_ attribute
                        coefs = getattr(self.model, 'coefs_', None)
                        if coefs is not None and len(coefs) > 0:
                            # Get weights from input layer to first hidden layer
                            first_layer_weights = coefs[0]
                            # Calculate mean absolute weight for each feature
                            feature_importance_scores = np.mean(np.abs(first_layer_weights), axis=1)
                            feature_importance = dict(zip(self.feature_names, feature_importance_scores))
                            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
                            logger.info("Using first layer weights as feature importance proxy")
                        else:
                            top_features = [("Feature importance not available", 0.0)]
                    except Exception as e:
                        logger.warning(f"Could not calculate feature importance proxy: {str(e)}")
                        top_features = [("Feature importance calculation failed", 0.0)]
                else:
                    # Other models
                    logger.info("Model type doesn't provide feature importance scores")
                    top_features = [("Feature importance not available for this model type", 0.0)]
            else:
                # PyTorch model - for now, just indicate not available
                top_features = [("Feature importance not available for PyTorch model", 0.0)]
            
            # Map prediction back to risk level
            risk_levels = ['low', 'medium', 'high']
            risk_level = risk_levels[prediction]
            
            result = {
                'risk_level': risk_level,
                'confidence': float(max(prediction_proba)),
                'probability_low_risk': float(prediction_proba[0]),
                'probability_medium_risk': float(prediction_proba[1] if len(prediction_proba) > 1 else 0),
                'probability_high_risk': float(prediction_proba[2] if len(prediction_proba) > 2 else 0),
                'top_risk_factors': top_features
            }
            
            logger.info(f"Prediction made: {result['risk_level']} risk with {result['confidence']:.4f} confidence")
            return result
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            raise ValueError(f"Failed to make prediction: {str(e)}")
    
    def save_model(self):
        """Save the trained model, scaler, and feature names to disk."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Save sklearn model
            if self.model is not None:
                with open(self.model_path, 'wb') as f:
                    pickle.dump(self.model, f)
                logger.info(f"sklearn model saved to {self.model_path}")
            
            # Save PyTorch model
            if self.pytorch_model is not None:
                torch.save(self.pytorch_model.state_dict(), self.pytorch_model_path)
                logger.info(f"PyTorch model saved to {self.pytorch_model_path}")
            
            # Save scaler
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            # Save feature names (important for feature selection)
            feature_names_path = os.path.join(settings.BASE_DIR, 'ml_models', 'saved_models', 'feature_names.pkl')
            with open(feature_names_path, 'wb') as f:
                pickle.dump(self.feature_names, f)
            
            # Save model metadata
            metadata_path = os.path.join(settings.BASE_DIR, 'ml_models', 'saved_models', 'model_metadata.pkl')
            metadata = {
                'use_gpu': self.use_gpu,
                'has_pytorch_model': self.pytorch_model is not None,
                'has_sklearn_model': self.model is not None,
                'feature_count': len(self.feature_names)
            }
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info("Model metadata saved")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise ValueError(f"Failed to save model: {str(e)}")
    
    def load_model(self):
        """Load the trained model, scaler, and feature names from disk."""
        try:
            feature_names_path = os.path.join(settings.BASE_DIR, 'ml_models', 'saved_models', 'feature_names.pkl')
            metadata_path = os.path.join(settings.BASE_DIR, 'ml_models', 'saved_models', 'model_metadata.pkl')
            
            # Try to load sklearn model first
            sklearn_loaded = False
            if os.path.exists(self.model_path):
                try:
                    with open(self.model_path, 'rb') as f:
                        loaded_data = pickle.load(f)
                    
                    # Check if it's a sklearn model or a PyTorch checkpoint
                    if hasattr(loaded_data, 'predict'):
                        # It's a proper sklearn model
                        self.model = loaded_data
                        sklearn_loaded = True
                        logger.info("Sklearn model loaded successfully")
                    elif isinstance(loaded_data, dict) and 'model_state_dict' in loaded_data:
                        # It's a PyTorch checkpoint saved as .pkl - ignore it here
                        logger.warning("Found PyTorch checkpoint in .pkl file - will load from .pth file instead")
                        self.model = None
                    else:
                        logger.warning(f"Unknown model format in .pkl file: {type(loaded_data)}")
                        self.model = None
                except Exception as e:
                    logger.warning(f"Could not load sklearn model: {e}")
                    self.model = None
            
            # Try to load scaler
            scaler_loaded = False
            if os.path.exists(self.scaler_path):
                try:
                    # Try pickle first
                    with open(self.scaler_path, 'rb') as f:
                        self.scaler = pickle.load(f)
                    scaler_loaded = True
                    logger.info("Scaler loaded successfully with pickle")
                except Exception as e:
                    logger.warning(f"Could not load scaler with pickle: {e}")
                    try:
                        # Try joblib
                        self.scaler = joblib.load(self.scaler_path)
                        scaler_loaded = True
                        logger.info("Scaler loaded successfully with joblib")
                    except Exception as e2:
                        logger.warning(f"Could not load scaler with joblib: {e2}")
                        self.scaler = None
            
            # Load feature names if available
            if os.path.exists(feature_names_path):
                with open(feature_names_path, 'rb') as f:
                    self.feature_names = pickle.load(f)
                logger.info(f"Loaded {len(self.feature_names)} features from saved model")
            
            # Try to load PyTorch model
            pytorch_loaded = False
            if os.path.exists(self.pytorch_model_path):
                try:
                    # Load checkpoint to inspect structure
                    checkpoint = torch.load(self.pytorch_model_path, map_location=self.device)
                    
                    if 'model_state_dict' in checkpoint and 'params' in checkpoint:
                        # This is a checkpoint format with metadata
                        model_state_dict = checkpoint['model_state_dict']
                        params = checkpoint['params']
                        
                        # Check if feature count matches
                        first_layer_key = '0.weight'
                        if first_layer_key in model_state_dict:
                            expected_features = model_state_dict[first_layer_key].shape[1]
                            current_features = len(self.feature_names)
                            
                            if expected_features == current_features:
                                # Feature count matches - load normally
                                hidden_sizes = params.get('hidden_sizes', [64])
                                self.pytorch_model = MLPNet(current_features, hidden_sizes).to(self.device)
                                
                                # Remap keys if needed
                                first_key = list(model_state_dict.keys())[0]
                                if not first_key.startswith('network.'):
                                    new_state_dict = {}
                                    for old_key, value in model_state_dict.items():
                                        new_key = f'network.{old_key}'
                                        new_state_dict[new_key] = value
                                    model_state_dict = new_state_dict
                                
                                self.pytorch_model.load_state_dict(model_state_dict)
                                self.pytorch_model.eval()
                                pytorch_loaded = True
                                logger.info(f"PyTorch model loaded successfully with {current_features} features")
                            else:
                                logger.warning(f"Feature mismatch: model expects {expected_features}, but we have {current_features}")
                                # For now, skip loading the mismatched model
                                self.pytorch_model = None
                        
                        if pytorch_loaded and 'test_metrics' in checkpoint:
                            metrics = checkpoint['test_metrics']
                            logger.info(f"Model accuracy: {metrics.get('accuracy', 'N/A')}")
                    else:
                        # Legacy format - direct state dict
                        first_key = list(checkpoint.keys())[0]
                        if first_key.startswith('network.'):
                            # Extract input size from the first layer
                            first_layer_weight = None
                            for key, value in checkpoint.items():
                                if key.endswith('.weight') and len(value.shape) == 2:
                                    first_layer_weight = value
                                    break
                            
                            if first_layer_weight is not None:
                                expected_features = first_layer_weight.shape[1]
                                current_features = len(self.feature_names)
                                
                                if expected_features == current_features:
                                    hidden_sizes = [128, 64, 32]  # Default architecture
                                    self.pytorch_model = MLPNet(current_features, hidden_sizes).to(self.device)
                                    self.pytorch_model.load_state_dict(checkpoint)
                                    self.pytorch_model.eval()
                                    pytorch_loaded = True
                                    logger.info("PyTorch model loaded successfully (legacy format)")
                        
                except Exception as e:
                    logger.warning(f"Could not load PyTorch model: {e}")
                    self.pytorch_model = None
            
            # Load metadata if available
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'rb') as f:
                        metadata = pickle.load(f)
                        logger.info(f"Model metadata: {metadata}")
                except Exception as e:
                    logger.warning(f"Could not load metadata: {e}")
            
            # Mark as trained if we have at least one model and scaler
            if (sklearn_loaded or pytorch_loaded) and scaler_loaded:
                self.is_trained = True
                logger.info("Model loaded successfully from disk")
            else:
                logger.info("No complete model found. Model needs to be trained.")
                self.is_trained = False
                
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None
            self.pytorch_model = None
            self.scaler = None
            self.is_trained = False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if not self.is_trained:
            return {'status': 'not_trained', 'message': 'Model has not been trained yet.'}
        
        model_type = type(self.model).__name__ if self.model else 'Unknown'
        
        info = {
            'status': 'trained',
            'model_type': model_type,
            'feature_count': len(self.feature_names),
            'features': self.feature_names,
            'model_path': self.model_path,
            'scaler_path': self.scaler_path,
            'gpu_available': torch.cuda.is_available(),
            'gpu_enabled': self.use_gpu,
            'has_pytorch_model': self.pytorch_model is not None,
            'has_sklearn_model': self.model is not None
        }
        
        if torch.cuda.is_available():
            info['gpu_name'] = torch.cuda.get_device_name()
            info['gpu_memory'] = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB"
        
        return info
    
    def retrain_with_new_data(self, new_csv_path: str, target_column: str = 'risk_level') -> Dict[str, Any]:
        """
        Retrain the model with new data while preserving existing knowledge.
        
        Args:
            new_csv_path: Path to CSV file with new training data
            target_column: Name of the target column
            
        Returns:
            Dict containing retraining results
        """
        try:
            logger.info("Retraining model with new data...")
            
            # Load new data
            new_df = pd.read_csv(new_csv_path)
            
            # Validate columns
            if target_column not in new_df.columns:
                raise ValueError(f"Target column '{target_column}' not found in new data")
            
            # Prepare features
            X_new = new_df[self.feature_names].fillna(0)
            y_new = new_df[target_column]
            
            # Convert target to 3-class if needed
            if y_new.dtype == 'object':
                y_new = y_new.map({
                    'low': 0, 'Low': 0,
                    'medium': 1, 'Medium': 1,
                    'high': 2, 'High': 2
                })
            
            # If we have an existing model, we can either:
            # 1. Retrain from scratch with combined data
            # 2. Use online learning (if supported by the algorithm)
            
            # For now, we'll retrain from scratch
            return self.train_from_csv(new_csv_path, target_column)
            
        except Exception as e:
            logger.error(f"Error retraining model: {str(e)}")
            raise ValueError(f"Failed to retrain model: {str(e)}")
    
    def create_sample_training_data(self, output_path: str, num_samples: int = 1000):
        """
        Create a sample CSV file with the expected format for training.
        
        Args:
            output_path: Path where to save the sample CSV
            num_samples: Number of sample records to generate
        """
        try:
            import random
            
            # Generate sample data
            data = []
            for _ in range(num_samples):
                record = {}
                
                # Handle different types of features
                for feature in self.feature_names:
                    if feature == 'total_dmft_score':
                        # Generate realistic DMFT values based on age distribution
                        dmft_total = random.choices([0, 1, 2, 3, 4, 5, 6], weights=[0.3, 0.25, 0.2, 0.15, 0.05, 0.03, 0.02], k=1)[0]
                        record[feature] = dmft_total
                    elif feature == 'decayed_teeth':
                        # Decayed teeth usually 0-3 for healthy populations
                        dmft_total = record.get('total_dmft_score', 0)
                        max_d = min(dmft_total, 3)  # Cap at 3 decayed teeth
                        record[feature] = random.randint(0, max_d)
                    elif feature == 'filled_teeth':
                        # Filled teeth based on remaining DMFT after decayed
                        dmft_total = record.get('total_dmft_score', 0)
                        decayed = record.get('decayed_teeth', 0)
                        remaining_dmft = dmft_total - decayed
                        max_f = max(0, remaining_dmft)
                        record[feature] = random.randint(0, max_f) if max_f > 0 else 0
                    elif feature == 'missing_teeth_count':
                        # Missing teeth based on remaining DMFT after decayed and filled
                        dmft_total = record.get('total_dmft_score', 0)
                        decayed = record.get('decayed_teeth', 0)
                        filled = record.get('filled_teeth', 0)
                        missing = dmft_total - decayed - filled
                        record[feature] = max(0, missing)
                    elif feature in ['has_dental_data', 'has_dietary_data']:
                        # Data availability indicators - simulate realistic scenarios
                        if feature == 'has_dental_data':
                            record[feature] = random.choice([0, 1])  # 50/50 chance
                        else:  # has_dietary_data
                            record[feature] = random.choice([0, 1])  # 50/50 chance
                    elif any(suffix in feature for suffix in ['_daily', '_weekly', '_timing', '_glasses']):
                        # Frequency/quantity fields (0-4 scale)
                        record[feature] = random.randint(0, 4)
                    else:
                        # Binary yes/no fields (0 or 1)
                        record[feature] = random.choice([0, 1])
                
                # Add target variable (risk level)
                # Updated rule considering frequency fields and data availability
                binary_risk_factors = sum([record[f] for f in self.feature_names 
                                         if f != 'total_dmft_score' and 
                                         f not in ['has_dental_data', 'has_dietary_data'] and
                                         not any(suffix in f for suffix in ['_daily', '_weekly', '_timing', '_glasses'])])
                frequency_risk_factors = sum([record[f] for f in self.feature_names 
                                            if any(suffix in f for suffix in ['_daily', '_weekly', '_timing', '_glasses'])])
                
                # Consider data completeness in risk calculation
                data_completeness = record['has_dental_data'] + record['has_dietary_data']
                
                total_risk_score = record['total_dmft_score'] + binary_risk_factors + (frequency_risk_factors * 0.5)
                
                # Higher threshold if less data is available (uncertainty factor)
                risk_threshold = 20 if data_completeness == 2 else 15
                
                if record['total_dmft_score'] > 15 or total_risk_score > risk_threshold:
                    record['risk_level'] = 'high'
                else:
                    record['risk_level'] = 'low'
                
                data.append(record)
            
            # Create DataFrame and save
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            
            logger.info(f"Sample training data created at {output_path}")
            logger.info(f"Generated {num_samples} samples with {len(df.columns)} columns")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {str(e)}")
            raise ValueError(f"Failed to create sample data: {str(e)}")
    
    def _encode_frequency_quantity(self, value):
        """
        Encode frequency/quantity text fields to numeric values.
        
        Args:
            value: Text value representing frequency or quantity
            
        Returns:
            int: Numeric encoding of the frequency/quantity
        """
        if not value or value is None or value == '':
            return 0
        
        value = str(value).lower().strip()
        
        # Frequency mappings
        frequency_map = {
            # Form template values - Daily frequencies (from dietary_screening_new.html)
            '1-3_day': 2,  # 1-3 servings/day -> moderate frequency
            '3-4_day': 3,  # 3-4 servings/day -> high frequency
            '4-6_day': 4,  # 4-6 servings/day -> very high frequency
            
            # Form template values - Weekly frequencies (from dietary_screening_new.html)
            '1-3_week': 1,  # 1-3 times/week -> low frequency
            '3-4_week': 2,  # 3-4 times/week -> moderate frequency
            '4-6_week': 3,  # 4-6 times/week -> high frequency
            
            # Form template values - Timing (from dietary_screening_new.html)
            'with_meals': 1,        # With meals -> lower risk
            'between_meals': 2,     # Between meals -> moderate risk
            'both': 3,              # Both -> higher risk
            'after_sweets': 2,      # After eating sweets/snacks -> moderate risk
            'before_bedtime': 3,    # Before bedtime -> higher risk
            
            # Form template values - Water glasses (from dietary_screening_new.html)
            '<2': 1,     # Less than 2 glasses -> low intake
            '2-4': 2,    # 2-4 glasses -> moderate intake
            '5+': 3,     # 5+ glasses -> high intake
            
            # Numeric strings for direct numeric input
            '0': 0,
            '1': 1,
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5,
        }
        
        # Try exact match first
        if value in frequency_map:
            return frequency_map[value]
        
        # Try to extract numbers for any numeric input
        import re
        numbers = re.findall(r'\d+', value)
        if numbers:
            num = int(numbers[0])
            if num == 0:
                return 0
            elif num <= 2:
                return 1
            elif num <= 4:
                return 2
            elif num <= 6:
                return 3
            else:
                return 4
        
        # Default to low frequency if we can't parse
        return 1
