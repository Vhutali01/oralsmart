"""
Risk calculation utilities for rule-based classification.
This provides standalone risk calculation logic without dependency on ML models.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Field categories for feature preparation
DENTAL_BINARY_FIELDS = [
    'sa_citizen', 'special_needs', 'caregiver_treatment',
    'appliance', 'plaque', 'dry_mouth', 'enamel_defects',
    'fluoride_water', 'fluoride_toothpaste', 'topical_fluoride',
    'regular_checkups', 'sealed_pits', 'restorative_procedures',
    'enamel_change', 'dentin_discoloration', 'white_spot_lesions',
    'cavitated_lesions', 'multiple_restorations', 'missing_teeth'
]

DIETARY_YES_NO_FIELDS = [
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

DIETARY_TEXT_FIELDS = [
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


def encode_frequency_quantity(value):
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


def calculate_dmft_score(teeth_data):
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


def prepare_features(dental_data=None, dietary_data=None):
    """
    Prepare features from dental and dietary data for rule-based classification.
    
    Args:
        dental_data: Optional object containing dental assessment data
        dietary_data: Optional object containing dietary assessment data
        
    Returns:
        dict: Feature dictionary with encoded values
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
            for field in DENTAL_BINARY_FIELDS:
                value = getattr(dental_data, field, 'no')
                features[field] = 1 if value == 'yes' else 0

            # DMFT score from teeth_data
            dmft_result = calculate_dmft_score(dental_data.teeth_data)
            features['total_dmft_score'] = dmft_result['dmft']
        else:
            # Set all dental fields to 0 if no dental data provided
            for field in DENTAL_BINARY_FIELDS:
                features[field] = 0
            
            # Set DMFT scores to 0
            features['total_dmft_score'] = 0

        # Handle dietary data (can be None)
        if dietary_data:
            # Process yes/no dietary fields
            for field in DIETARY_YES_NO_FIELDS:
                value = getattr(dietary_data, field, 'no')
                features[field] = 1 if value == 'yes' else 0
            
            # Process text/quantity fields
            for field in DIETARY_TEXT_FIELDS:
                value = getattr(dietary_data, field, None)
                features[field] = encode_frequency_quantity(value)
                
        else:
            # Set all dietary fields to 0 if no dietary data provided
            for field in DIETARY_YES_NO_FIELDS + DIETARY_TEXT_FIELDS:
                features[field] = 0

        return features
    
    except Exception as e:
        logger.error(f"Error preparing features: {str(e)}")
        raise ValueError(f"Failed to prepare features: {str(e)}")


def calculate_risk_level_for_patient(patient, dental_screening=None, dietary_screening=None, min_dmft=None, risk_threshold=None):
    """
    Calculate risk level for a patient with their assessment data using rule-based classification.
    
    Args:
        patient: Patient model instance
        dental_screening: DentalScreening model instance (optional)
        dietary_screening: DietaryScreening model instance (optional)
        min_dmft: Minimum DMFT for high risk classification (optional)
        risk_threshold: Custom high-risk threshold (optional)
        
    Returns:
        str: 'low', 'medium', or 'high'
    """
    try:
        # Convert model instances to feature dictionary
        feature_dict = prepare_features(dental_screening, dietary_screening)
        
        # Use the same risk calculation logic as the export command
        return _calculate_risk_level_from_features(feature_dict, min_dmft, risk_threshold)
        
    except Exception as e:
        # Fallback to simple calculation if feature extraction fails
        return _simple_risk_calculation(patient, dental_screening, dietary_screening)


def get_risk_prediction(dental_data, dietary_data):
    """
    Get rule-based risk prediction for a patient - replacement for ML prediction.
    
    Args:
        dental_data: DentalScreening model instance or None
        dietary_data: DietaryScreening model instance or None
        
    Returns:
        dict: Risk prediction result with same format as ML predictor
    """
    try:
        # Prepare features using rule-based encoding
        feature_dict = prepare_features(dental_data, dietary_data)
        
        # Calculate risk level using rule-based logic
        risk_level = _calculate_risk_level_from_features(feature_dict)
        
        # Simulate confidence and probability scores (rule-based doesn't have real probabilities)
        if risk_level == 'high':
            confidence = 0.85
            prob_high, prob_medium, prob_low = 0.85, 0.10, 0.05
        elif risk_level == 'medium':
            confidence = 0.75
            prob_high, prob_medium, prob_low = 0.15, 0.75, 0.10
        else:  # low risk
            confidence = 0.80
            prob_high, prob_medium, prob_low = 0.05, 0.15, 0.80
        
        # Get top risk factors for explanation
        risk_factors = _get_top_risk_factors(feature_dict)
        
        return {
            'risk_level': risk_level,
            'confidence': confidence,
            'probability_low_risk': prob_low,
            'probability_medium_risk': prob_medium,
            'probability_high_risk': prob_high,
            'top_risk_factors': risk_factors,
            'available': True,
            'error': None,
            'method': 'rule-based'
        }
        
    except Exception as e:
        logger.error(f"Rule-based prediction error: {e}")
        return {
            'risk_level': 'Error',
            'confidence': 0.0,
            'probability_low_risk': 0.0,
            'probability_medium_risk': 0.0,
            'probability_high_risk': 0.0,
            'top_risk_factors': [],
            'error': str(e),
            'available': False,
            'method': 'rule-based'
        }


def _get_top_risk_factors(feature_dict, top_n=5):
    """
    Identify the top risk factors contributing to the risk score.
    
    Args:
        feature_dict: Dictionary of encoded features
        top_n: Number of top factors to return
        
    Returns:
        list: List of top risk factor names
    """
    risk_factors = []
    
    # High-weight clinical factors
    clinical_factors = [
        ('cavitated_lesions', 'Cavitated Lesions'),
        ('multiple_restorations', 'Multiple Restorations'),
        ('missing_teeth', 'Missing Teeth'),
        ('enamel_change', 'Enamel Changes'),
        ('dentin_discoloration', 'Dentin Discoloration'),
        ('white_spot_lesions', 'White Spot Lesions')
    ]
    
    for field, display_name in clinical_factors:
        if feature_dict.get(field, 0) == 1:
            risk_factors.append(display_name)
    
    # DMFT score factor
    dmft_score = feature_dict.get('total_dmft_score', 0)
    if dmft_score > 5:
        risk_factors.append(f'High DMFT Score ({dmft_score})')
    elif dmft_score > 2:
        risk_factors.append(f'Moderate DMFT Score ({dmft_score})')
    
    # High-frequency dietary factors
    dietary_risk_factors = [
        ('sweet_sugary_foods', 'sweet_sugary_foods_daily', 'High Sugar Intake'),
        ('cold_drinks_juices', 'cold_drinks_juices_daily', 'Frequent Sugary Drinks'),
        ('processed_fruit', 'processed_fruit_daily', 'Processed Fruit Consumption'),
        ('added_sugars', 'added_sugars_daily', 'Added Sugar Consumption')
    ]
    
    for main_field, freq_field, display_name in dietary_risk_factors:
        if feature_dict.get(main_field, 0) == 1 and feature_dict.get(freq_field, 0) >= 3:
            risk_factors.append(display_name)
    
    # Social risk factors
    if feature_dict.get('special_needs', 0) == 1:
        risk_factors.append('Special Needs')
    if feature_dict.get('caregiver_treatment', 0) == 0:
        risk_factors.append('No Caregiver Treatment')
    
    # Return top factors
    return risk_factors[:top_n]


def _calculate_risk_level_from_features(feature_dict, min_dmft=None, risk_threshold=None):
    """
    Calculate risk level based on feature values - matches export command logic.
    """
    # DMFT score risk factor
    dmft_score = feature_dict.get('total_dmft_score', 0)
    
    # Use custom DMFT threshold if provided
    if min_dmft is not None and dmft_score >= min_dmft:
        return 'high'
    
    # Calculate composite risk score (same as export command)
    risk_score = 0
    
    # Clinical findings (major risk factors - 2 points each)
    clinical_factors = ['cavitated_lesions', 'multiple_restorations', 'missing_teeth', 
                       'enamel_change', 'dentin_discoloration', 'white_spot_lesions']
    
    for factor in clinical_factors:
        if feature_dict.get(factor, 0) == 1:
            risk_score += 2
    
    # Protective factors (subtract 1 point each)
    protective_factors = ['fluoride_water', 'fluoride_toothpaste', 'topical_fluoride',
                         'regular_checkups', 'sealed_pits']
    
    for factor in protective_factors:
        if feature_dict.get(factor, 0) == 1:
            risk_score -= 1
    
    # Dietary risk factors
    dietary_factors = ['sweet_sugary_foods', 'takeaways_processed_foods', 
                      'cold_drinks_juices', 'processed_fruit', 'added_sugars']
    
    for factor in dietary_factors:
        if feature_dict.get(factor, 0) == 1:
            risk_score += 1
    
    # High frequency dietary factors (3+ times daily)
    frequency_factors = ['sweet_sugary_foods_daily', 'takeaways_processed_foods_daily',
                        'cold_drinks_juices_daily', 'processed_fruit_daily', 'added_sugars_daily']
    
    for factor in frequency_factors:
        freq_value = feature_dict.get(factor, 0)
        if freq_value >= 3:  # High frequency
            risk_score += 1
    
    # Social risk factors
    if feature_dict.get('special_needs', 0) == 1:
        risk_score += 2
    
    if feature_dict.get('caregiver_treatment', 0) == 0:  # No caregiver treatment
        risk_score += 1
    
    # DMFT contribution
    risk_score += dmft_score * 0.5  # Each DMFT point adds 0.5 to risk
    
    # Data availability penalty (uncertainty increases risk threshold)
    has_dental = feature_dict.get('has_dental_data', 0)
    has_dietary = feature_dict.get('has_dietary_data', 0)
    data_completeness = has_dental + has_dietary
    
    # Use custom thresholds if provided, otherwise calculate based on data completeness
    if risk_threshold is not None:
        # For 3-class system, treat risk_threshold as the high threshold
        # Medium threshold is typically 60-70% of high threshold
        high_threshold = risk_threshold
        medium_threshold = risk_threshold * 0.5  # 65% of high threshold
    else:
        # More conservative thresholds when data is incomplete
        base_high_threshold = 8
        if data_completeness == 2:  # Both assessments
            high_threshold = base_high_threshold
            medium_threshold = base_high_threshold * 0.65  # ~5.2
        elif data_completeness == 1:  # Only one assessment
            high_threshold = base_high_threshold - 2  # 6
            medium_threshold = (base_high_threshold - 2) * 0.65  # ~3.9
        else:  # No assessments (shouldn't happen if validation works)
            high_threshold = base_high_threshold - 4  # 4
            medium_threshold = (base_high_threshold - 4) * 0.65  # ~2.6
    
    # Return 3-class risk level
    if risk_score >= high_threshold:
        return 'high'
    elif risk_score >= medium_threshold:
        return 'medium'
    else:
        return 'low'


def _simple_risk_calculation(patient, dental_screening=None, dietary_screening=None):
    """
    Simplified risk calculation as fallback when feature extraction fails.
    """
    risk_score = 0
    
    if dental_screening:
        # Count dental risk factors
        if getattr(dental_screening, 'cavitated_lesions', None) == 'yes':
            risk_score += 2
        if getattr(dental_screening, 'multiple_restorations', None) == 'yes':
            risk_score += 2
        if getattr(dental_screening, 'missing_teeth', None) == 'yes':
            risk_score += 2
        if getattr(dental_screening, 'plaque', None) == 'yes':
            risk_score += 1
        
        # Subtract protective factors
        if getattr(dental_screening, 'fluoride_toothpaste', None) == 'yes':
            risk_score -= 1
        if getattr(dental_screening, 'regular_checkups', None) == 'yes':
            risk_score -= 1
    
    if dietary_screening:
        # Count dietary risk factors
        if getattr(dietary_screening, 'sweet_sugary_foods', None) == 'yes':
            risk_score += 1
        if getattr(dietary_screening, 'cold_drinks_juices', None) == 'yes':
            risk_score += 1
    
    # Simple 3-class thresholds
    if risk_score >= 6:
        return 'high'
    elif risk_score >= 3:
        return 'medium'
    else:
        return 'low'
