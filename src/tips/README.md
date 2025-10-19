# Health Tips Module for OralSmart

## Overview

The Health Tips module implements an evidence-based health information system specifically designed for the South African healthcare context. It enforces academic rigor and legal compliance while maintaining accessibility for low-literacy users.

## Features

### Models
- **TipCategory**: Organizes tips into categories linked to SA burden of disease
- **HealthTip**: Core model for verified health advice with academic compliance

### Key Compliance Features
- Grade 8 reading level text requirement
- Mandatory source citation from SA health authorities (NDOH, SAMRC, NICD)
- Audio file support for low-literacy users
- Critical tip flagging for emergency information
- Legal disclaimer integration

### South African Health Authority Sources
- NDOH (National Department of Health)
- SAMRC (South African Medical Research Council)  
- NICD (National Institute for Communicable Diseases)
- HPCSA (Health Professions Council of South Africa)
- SA Food-Based Dietary Guidelines (FBDG)

## Installation & Setup

### 1. Add to Django Settings

The `tips` app has already been added to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps
    'tips.apps.TipsConfig',
]
```

### 2. Run Migrations (when database is available)

```bash
python manage.py makemigrations tips
python manage.py migrate
```

### 3. Populate Sample Data

```bash
python manage.py populate_tips
```

### 5. Fix Existing URLs (if needed)

```bash
python manage.py fix_tip_urls
```

### 4. Access the Tips

- **Public URL** (accessible from landing page): `/tips/`
- Landing page integration: Users can access tips via "View Tips and Dental Advice" button

## URL Configuration

URLs have been added to the main `oralsmart/urls.py`:

```python
path('tips/', include('tips.urls')),
```

## Public Access Design

The tips module is designed for **public access** without authentication requirements:
- No login required to view health tips
- Accessible directly from the landing page
- Provides verified health information to the general public
- Maintains legal disclaimers for liability protection

## Templates

### Available Templates
1. **`tips/templates/tips/tips_list.html`** - Standalone template with full Bootstrap
2. **`templates/tips/tips.html`** - Template that extends base.html (if available)

### Template Features
- Responsive Bootstrap design
- Accordion interface for easy navigation
- Audio player integration
- Accessibility enhancements
- Legal disclaimer prominence
- Source citation display

## Admin Interface

Access via Django admin at `/admin/`:
- **Tip Categories**: Manage categories with icons
- **Health Tips**: Full content management with verification tracking

### Admin Features
- Organized fieldsets for content vs compliance
- Search and filtering capabilities
- Automatic timestamp tracking

## Content Guidelines

### Text Requirements
- Maximum Grade 8 reading level
- Simple, actionable titles (150 chars max)
- Clear summaries (250 chars max)
- Unambiguous full text

### Source Requirements
- Must cite official SA health authority
- Links to official websites when available (NDOH, HPCSA, NICD)
- Some tips may only include citation without URL link
- Academic rigour in content selection

### Audio Requirements  
- Recommended for all tips (accessibility)
- Supports MP3/WAV formats
- Located in `media/tip_audio/` directory

## Usage Examples

### Adding New Categories

```python
from tips.models import TipCategory

category = TipCategory.objects.create(
    name="Mental Health",
    description="Guidelines for mental health and wellbeing",
    icon_class="fa-brain"
)
```

### Adding New Tips

```python
from tips.models import HealthTip, TipCategory

category = TipCategory.objects.get(name="Oral Health")
tip = HealthTip.objects.create(
    category=category,
    title="Fluoride Toothpaste Benefits",
    summary="Use fluoride toothpaste to strengthen teeth and prevent cavities.",
    full_text="Fluoride helps remineralize tooth enamel...",
    citation_source="NDOH Oral Health Guidelines 2023",
    citation_url="https://www.health.gov.za/guidelines",
    is_critical=False
)
```

## Legal Compliance

### Disclaimer
The system includes prominent legal disclaimers stating that:
- Information is for educational purposes only
- Not a substitute for professional medical advice
- Users should consult registered healthcare professionals

### Source Verification
All tips must include:
- Primary source citation
- Authority verification
- Update timestamps
- Quality assurance tracking

## Development Notes

### Database Independence
- Views include fallback error handling
- Can operate without immediate database setup
- Graceful degradation when migrations pending

### Integration Points
- Follows OralSmart authentication patterns
- Uses existing static file structure
- Compatible with existing admin interface
- Extends current URL patterns

## Testing

The tips are publicly accessible from the landing page:
```
http://localhost:8000/tips/
```

Users can access tips by clicking "View Tips and Dental Advice" on the landing page.

## Integration Points

### Landing Page Integration
- Tips button added to landing page
- Public access design for community health education
- No authentication barriers for health information access

## Future Enhancements

1. **Multi-language Support**: Add support for SA official languages
2. **Content Versioning**: Track changes to health guidelines
3. **User Ratings**: Allow healthcare professionals to rate tip usefulness
4. **Search Functionality**: Full-text search across tips
5. **API Integration**: REST API for mobile app integration
6. **Offline Support**: PWA capabilities for low-connectivity areas