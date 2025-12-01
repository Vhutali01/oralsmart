from django.db import models
from django.core.exceptions import ValidationError
from patient.models import Patient

# Create your models here.


class DentalScreening(models.Model):

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='screenings')

    #Section 1
    sa_citizen = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    special_needs = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    caregiver_treatment = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])

    #Section 2
    appliance = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    plaque = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    dry_mouth = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    enamel_defects = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])

    #Section 3
    fluoride_water = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    fluoride_toothpaste = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    topical_fluoride = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    regular_checkups = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])

    #Section 4
    sealed_pits = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    restorative_procedures = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    enamel_change = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    dentin_discoloration = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    white_spot_lesions = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    cavitated_lesions = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    multiple_restorations = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    missing_teeth = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    
    #Section 5
    teeth_data = models.JSONField()  #stores all tooth values as a dict

    # Draft status for save-and-resume functionality
    is_draft = models.BooleanField(default=False, help_text="True if this is a saved draft, False if completed")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DietaryScreening(models.Model):

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='dietary_screenings')

    # Section 1: Sweet/Sugary Foods
    sweet_sugary_foods = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    sweet_sugary_foods_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    sweet_sugary_foods_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])
    sweet_sugary_foods_timing = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('with_meals', 'With meals'),
        ('between_meals', 'Between meals'),
        ('both', 'Both'),
    ])
    sweet_sugary_foods_bedtime = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)

    # Section 2: Take-aways and Processed Foods
    takeaways_processed_foods = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    takeaways_processed_foods_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    takeaways_processed_foods_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])

    # Section 3: Fresh Fruit
    fresh_fruit = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    fresh_fruit_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    fresh_fruit_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])
    fresh_fruit_timing = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('with_meals', 'With meals'),
        ('between_meals', 'Between meals'),
        ('both', 'Both'),
    ])
    fresh_fruit_bedtime = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)

    # Section 4: Cold Drinks, Juices and Flavoured Water and Milk
    cold_drinks_juices = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    cold_drinks_juices_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    cold_drinks_juices_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])
    cold_drinks_juices_timing = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('with_meals', 'With meals'),
        ('between_meals', 'Between meals'),
        ('both', 'Both'),
    ])
    cold_drinks_juices_bedtime = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)

    # Section 5: Processed Fruit
    processed_fruit = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    processed_fruit_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    processed_fruit_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])
    processed_fruit_timing = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('with_meals', 'With meals'),
        ('between_meals', 'Between meals'),
        ('both', 'Both'),
    ])
    processed_fruit_bedtime = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)

    # Section 6: Spreads
    spreads = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    spreads_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    spreads_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])
    spreads_timing = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('with_meals', 'With meals'),
        ('between_meals', 'Between meals'),
        ('both', 'Both'),
    ])
    spreads_bedtime = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)

    # Section 7: Added Sugars
    added_sugars = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    added_sugars_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    added_sugars_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])
    added_sugars_timing = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('with_meals', 'With meals'),
        ('between_meals', 'Between meals'),
        ('both', 'Both'),
    ])
    added_sugars_bedtime = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')], blank=True, null=True)

    # Section 8: Salty Snacks
    salty_snacks = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    salty_snacks_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    salty_snacks_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])
    salty_snacks_timing = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('with_meals', 'With meals'),
        ('between_meals', 'Between meals'),
        ('both', 'Both'),
    ])

    # Section 9: Dairy Products
    dairy_products = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    dairy_products_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    dairy_products_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])

    # Section 10: Vegetables
    vegetables = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    vegetables_daily = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_day', '1-3 times per day'),
        ('3-4_day', '3-4 times per day'),
        ('4-6_day', '4-6 times per day'),
    ])
    vegetables_weekly = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-3_week', '1-3 times per week'),
        ('3-4_week', '3-4 times per week'),
        ('4-6_week', '4-6 times per week'),
    ])

    # Section 11: Water
    water = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    water_timing = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('with_meals', 'With meals'),
        ('between_meals', 'Between meals'),
        ('after_sweets', 'After eating sweets'),
        ('before_bedtime', 'Before bedtime'),
    ])
    water_glasses = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('<2', 'Less than 2 glasses'),
        ('2-4', '2-4 glasses'),
        ('5+', '5 or more glasses'),
    ])

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """
        Custom validation to ensure that sub-fields are null when main field is 'no'
        """
        super().clean()
        
        # Define field groups with their main field and related sub-fields
        field_groups = [
            ('sweet_sugary_foods', ['sweet_sugary_foods_daily', 'sweet_sugary_foods_weekly', 'sweet_sugary_foods_timing', 'sweet_sugary_foods_bedtime']),
            ('takeaways_processed_foods', ['takeaways_processed_foods_daily', 'takeaways_processed_foods_weekly']),
            ('fresh_fruit', ['fresh_fruit_daily', 'fresh_fruit_weekly', 'fresh_fruit_timing', 'fresh_fruit_bedtime']),
            ('cold_drinks_juices', ['cold_drinks_juices_daily', 'cold_drinks_juices_weekly', 'cold_drinks_juices_timing', 'cold_drinks_juices_bedtime']),
            ('processed_fruit', ['processed_fruit_daily', 'processed_fruit_weekly', 'processed_fruit_timing', 'processed_fruit_bedtime']),
            ('spreads', ['spreads_daily', 'spreads_weekly', 'spreads_timing', 'spreads_bedtime']),
            ('added_sugars', ['added_sugars_daily', 'added_sugars_weekly', 'added_sugars_timing', 'added_sugars_bedtime']),
            ('salty_snacks', ['salty_snacks_daily', 'salty_snacks_weekly', 'salty_snacks_timing']),
            ('dairy_products', ['dairy_products_daily', 'dairy_products_weekly']),
            ('vegetables', ['vegetables_daily', 'vegetables_weekly']),
            ('water', ['water_timing', 'water_glasses']),
        ]
        
        for main_field, sub_fields in field_groups:
            main_value = getattr(self, main_field, None)
            
            if main_value == 'no':
                # Set all sub-fields to None when main field is 'no'
                for sub_field in sub_fields:
                    setattr(self, sub_field, None)

    def save(self, *args, **kwargs):
        """
        Override save to automatically clean the model before saving
        """
        self.full_clean()  # This calls clean() method
        super().save(*args, **kwargs)