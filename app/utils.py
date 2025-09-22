"""
Utility functions for the Kenyan Real Estate AI Agent
"""
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
import os


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )


def extract_property_details(query: str) -> Dict[str, Any]:
    """Extract property details from a natural language query"""
    details = {}
    
    # Extract property type
    property_types = {
        'house': ['house', 'home', 'villa', 'mansion', 'bungalow'],
        'apartment': ['apartment', 'flat', 'condo', 'unit'],
        'commercial': ['office', 'shop', 'retail', 'commercial', 'warehouse', 'industrial'],
        'land': ['land', 'plot', 'acre', 'parcel']
    }
    
    query_lower = query.lower()
    for prop_type, keywords in property_types.items():
        if any(keyword in query_lower for keyword in keywords):
            details['property_type'] = prop_type
            break
    
    # Extract bedroom count
    bedroom_patterns = [
        r'(\d+)\s*bedroom',
        r'(\d+)\s*br',
        r'(\d+)br',
        r'(\d+)\s*bed'
    ]
    
    for pattern in bedroom_patterns:
        match = re.search(pattern, query_lower)
        if match:
            details['bedrooms'] = int(match.group(1))
            break
    
    # Extract budget/price range
    price_patterns = [
        r'ksh?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|m)',
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|m)',
        r'ksh?\s*(\d+(?:,\d{3})*)',
        r'budget.*?(\d+(?:,\d{3})*)',
        r'price.*?(\d+(?:,\d{3})*)'
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            try:
                # Convert to numbers and determine if it's in millions
                prices = []
                for match in matches:
                    price_str = match.replace(',', '')
                    price = float(price_str)
                    
                    # If the original query mentioned "million", multiply by 1M
                    if 'million' in query_lower or 'm' in query_lower:
                        price *= 1_000_000
                    
                    prices.append(price)
                
                if len(prices) == 1:
                    details['budget_max'] = prices[0]
                elif len(prices) >= 2:
                    details['budget_min'] = min(prices)
                    details['budget_max'] = max(prices)
            except ValueError:
                pass
            break
    
    # Extract locations (common Kenyan locations)
    kenyan_locations = [
        # Nairobi areas
        'karen', 'runda', 'muthaiga', 'westlands', 'kilimani', 'kileleshwa', 
        'lavington', 'parklands', 'kasarani', 'githurai', 'syokimau', 'kitengela',
        'ongata rongai', 'pipeline', 'embakasi', 'south b', 'south c', 'langata',
        
        # Major cities
        'nairobi', 'mombasa', 'kisumu', 'nakuru', 'eldoret', 'thika', 'ruiru',
        'machakos', 'kitui', 'garissa', 'isiolo', 'nyeri', 'meru',
        
        # Counties
        'kiambu', 'kajiado', 'muranga', 'kirinyaga', 'laikipia'
    ]
    
    for location in kenyan_locations:
        if location in query_lower:
            details['location'] = location.title()
            break
    
    # Extract transaction type
    if any(word in query_lower for word in ['rent', 'rental', 'lease']):
        details['transaction_type'] = 'rent'
    elif any(word in query_lower for word in ['buy', 'purchase', 'sale']):
        details['transaction_type'] = 'buy'
    elif any(word in query_lower for word in ['invest', 'investment', 'roi']):
        details['transaction_type'] = 'invest'
    
    return details


def format_price(amount: float, currency: str = "KSH") -> str:
    """Format price with proper currency and units"""
    if amount >= 1_000_000:
        return f"{currency} {amount / 1_000_000:.1f} million"
    elif amount >= 1_000:
        return f"{currency} {amount / 1_000:.0f}K"
    else:
        return f"{currency} {amount:,.0f}"


def calculate_affordability(income: float, property_price: float, deposit_percent: float = 20) -> Dict[str, Any]:
    """Calculate property affordability based on income"""
    monthly_income = income / 12
    deposit_required = property_price * (deposit_percent / 100)
    loan_amount = property_price - deposit_required
    
    # Assuming 12% interest rate and 20-year loan
    interest_rate = 0.12 / 12  # Monthly rate
    num_payments = 20 * 12    # Total months
    
    if interest_rate > 0:
        monthly_payment = loan_amount * (interest_rate * (1 + interest_rate)**num_payments) / ((1 + interest_rate)**num_payments - 1)
    else:
        monthly_payment = loan_amount / num_payments
    
    debt_to_income = (monthly_payment / monthly_income) * 100
    
    return {
        'deposit_required': deposit_required,
        'loan_amount': loan_amount,
        'monthly_payment': monthly_payment,
        'debt_to_income_ratio': debt_to_income,
        'affordable': debt_to_income <= 30,  # 30% DTI rule
        'recommendation': 'Affordable' if debt_to_income <= 30 else 'Consider lower price range'
    }


def get_market_trends(area: str) -> Dict[str, Any]:
    """Get market trends for a specific area (placeholder function)"""
    # This would typically connect to a real estate API or database
    # For now, returning sample trend data
    trends = {
        'price_change_1year': 8.5,
        'rental_yield': 6.2,
        'demand_level': 'High',
        'supply_level': 'Moderate',
        'investment_score': 7.5,
        'growth_projection': 'Positive'
    }
    return trends


def validate_kenyan_phone(phone: str) -> bool:
    """Validate Kenyan phone number format"""
    # Remove spaces and special characters
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check for valid Kenyan phone patterns
    patterns = [
        r'^254[17]\d{8}$',  # +254 format
        r'^0[17]\d{8}$',    # 0 format
        r'^[17]\d{8}$'      # Without country code
    ]
    
    return any(re.match(pattern, clean_phone) for pattern in patterns)


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\';]', '', text)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized.strip()


def get_system_health() -> Dict[str, Any]:
    """Get system health metrics"""
    try:
        if not HAS_PSUTIL:
            return {
                'status': 'healthy',
                'cpu_usage': 'unknown',
                'memory_usage': 'unknown',
                'memory_available': 'unknown',
                'disk_usage': 'unknown',
                'disk_free': 'unknown',
                'note': 'psutil not available - install for detailed metrics'
            }
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'memory_available': memory.available / (1024**3),  # GB
            'disk_usage': disk.percent,
            'disk_free': disk.free / (1024**3),  # GB
            'status': 'healthy' if cpu_percent < 80 and memory.percent < 85 else 'degraded'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


async def rate_limiter(key: str, limit: int = 60, window: int = 60) -> bool:
    """Simple rate limiter (in production, use Redis)"""
    # This is a basic implementation - use Redis or similar in production
    current_time = datetime.utcnow().timestamp()
    
    # For demo purposes, always return True
    # In production, implement proper rate limiting
    return True


def generate_property_report(property_data: Dict[str, Any]) -> str:
    """Generate a formatted property report"""
    report_parts = []
    
    if 'location' in property_data:
        report_parts.append(f"📍 Location: {property_data['location']}")
    
    if 'property_type' in property_data:
        report_parts.append(f"🏠 Type: {property_data['property_type'].title()}")
    
    if 'price' in property_data:
        formatted_price = format_price(property_data['price'])
        report_parts.append(f"💰 Price: {formatted_price}")
    
    if 'bedrooms' in property_data:
        report_parts.append(f"🛏️ Bedrooms: {property_data['bedrooms']}")
    
    if 'amenities' in property_data:
        amenities = ', '.join(property_data['amenities'])
        report_parts.append(f"✨ Amenities: {amenities}")
    
    return '\n'.join(report_parts)


class PropertyMatcher:
    """Match user requirements with property data"""
    
    @staticmethod
    def calculate_match_score(user_requirements: Dict[str, Any], property_data: Dict[str, Any]) -> float:
        """Calculate how well a property matches user requirements"""
        score = 0.0
        max_score = 0.0
        
        # Location match (30% weight)
        max_score += 30
        if 'location' in user_requirements and 'location' in property_data:
            if user_requirements['location'].lower() in property_data['location'].lower():
                score += 30
            elif any(word in property_data['location'].lower() 
                    for word in user_requirements['location'].lower().split()):
                score += 15
        
        # Price range match (25% weight)
        max_score += 25
        if 'price' in property_data:
            price = property_data['price']
            budget_min = user_requirements.get('budget_min', 0)
            budget_max = user_requirements.get('budget_max', float('inf'))
            
            if budget_min <= price <= budget_max:
                score += 25
            elif price < budget_min:
                # Price below budget - still good
                score += 20
            else:
                # Price above budget - partial score based on how much over
                over_ratio = price / budget_max
                if over_ratio <= 1.2:  # Within 20% over budget
                    score += 10
        
        # Property type match (20% weight)
        max_score += 20
        if 'property_type' in user_requirements and 'property_type' in property_data:
            if user_requirements['property_type'] == property_data['property_type']:
                score += 20
        
        # Bedroom match (15% weight)
        max_score += 15
        if 'bedrooms' in user_requirements and 'bedrooms' in property_data:
            required_bedrooms = user_requirements['bedrooms']
            available_bedrooms = property_data['bedrooms']
            
            if available_bedrooms == required_bedrooms:
                score += 15
            elif available_bedrooms == required_bedrooms - 1:
                score += 10
            elif available_bedrooms == required_bedrooms + 1:
                score += 12
        
        # Transaction type match (10% weight)
        max_score += 10
        if 'transaction_type' in user_requirements and 'transaction_type' in property_data:
            if user_requirements['transaction_type'] == property_data['transaction_type']:
                score += 10
        
        return (score / max_score) if max_score > 0 else 0.0


def create_sample_env_content() -> str:
    """Create sample environment file content"""
    return """# Kenyan Real Estate AI Agent Configuration

# Together AI Configuration
TOGETHER_API_KEY=0ead0c7716c61be64bc13c4a0aea90147e4ddb56a7ac5d437fe15f57b758ea3f
TOGETHER_MODEL=deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Knowledge Base Configuration
KNOWLEDGE_BASE_PATH=./knowledgebase
MAX_CONTEXT_LENGTH=4000

# Application Settings
APP_NAME=Kenyan Real Estate AI Agent
APP_VERSION=1.0.0
CORS_ORIGINS=["*"]
"""
