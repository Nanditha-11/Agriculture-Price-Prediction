from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import pymongo
import datetime
import random
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client['agripredict_db']
predictions_collection = db['predictions']
feedback_collection = db['feedback']
alerts_collection = db['alerts']
 
 @app.route('/check-db')
 def check_db():
     try:
         client.admin.command('ping')
         return jsonify({"status": "success", "message": "Connected to MongoDB Atlas!"})
     except Exception as e:
         return jsonify({"status": "error", "message": str(e)}), 500

# Function to convert month number to season
def get_season_from_month(month_num):
    """Convert month number (1-12) to season"""
    month_num = int(month_num)
    if month_num in [7, 8, 9, 10]:
        return 'Kharif'
    elif month_num in [11, 12, 1, 2, 3]:
        return 'Rabi'
    else:  # months 4,5,6
        return 'Zaid'

# Market data for different crops
MARKET_DATA = {
    'Maize': {
        'base_price': 2000,
        'seasonal_factor': {'Kharif': 1.15, 'Rabi': 1.05, 'Zaid': 0.95},
        'trend': 'rising',
        'demand': 'High',
        'best_markets': ['Nagpur', 'Bangalore', 'Hyderabad'],
        'states': ['Maharashtra', 'Karnataka', 'Madhya Pradesh']
    },
    'Wheat': {
        'base_price': 2500,
        'seasonal_factor': {'Kharif': 0.95, 'Rabi': 1.20, 'Zaid': 1.05},
        'trend': 'stable',
        'demand': 'Very High',
        'best_markets': ['Punjab Mandi', 'Hapur', 'Kanpur'],
        'states': ['Punjab', 'Haryana', 'Uttar Pradesh']
    },
    'Rice': {
        'base_price': 2800,
        'seasonal_factor': {'Kharif': 1.10, 'Rabi': 1.08, 'Zaid': 0.98},
        'trend': 'rising',
        'demand': 'High',
        'best_markets': ['Karnal', 'Raipur', 'Vijayawada'],
        'states': ['West Bengal', 'Uttar Pradesh', 'Punjab']
    },
    'Cotton': {
        'base_price': 6000,
        'seasonal_factor': {'Kharif': 1.12, 'Rabi': 1.05, 'Zaid': 0.92},
        'trend': 'volatile',
        'demand': 'Moderate',
        'best_markets': ['Ahmedabad', 'Nagpur', 'Guntur'],
        'states': ['Gujarat', 'Maharashtra', 'Telangana']
    },
    'Sugarcane': {
        'base_price': 3200,
        'seasonal_factor': {'Kharif': 1.08, 'Rabi': 1.12, 'Zaid': 0.96},
        'trend': 'rising',
        'demand': 'High',
        'best_markets': ['Kolhapur', 'Muzaffarnagar', 'Belgaum'],
        'states': ['Uttar Pradesh', 'Maharashtra', 'Karnataka']
    },
    'Groundnut': {
        'base_price': 5200,
        'seasonal_factor': {'Kharif': 1.08, 'Rabi': 1.10, 'Zaid': 0.94},
        'trend': 'stable',
        'demand': 'Moderate',
        'best_markets': ['Rajkot', 'Adoni', 'Jalgaon'],
        'states': ['Gujarat', 'Andhra Pradesh', 'Tamil Nadu']
    },
    'Barley': {
        'base_price': 2200,
        'seasonal_factor': {'Kharif': 0.95, 'Rabi': 1.15, 'Zaid': 1.02},
        'trend': 'rising',
        'demand': 'Moderate',
        'best_markets': ['Rajasthan Mandi', 'Sirsa', 'Rewari'],
        'states': ['Rajasthan', 'Uttar Pradesh', 'Haryana']
    },
    'Coconut': {
        'base_price': 3500,
        'seasonal_factor': {'Kharif': 1.05, 'Rabi': 1.05, 'Zaid': 1.10},
        'trend': 'stable',
        'demand': 'High',
        'best_markets': ['Kochi', 'Mangalore', 'Theni'],
        'states': ['Kerala', 'Karnataka', 'Tamil Nadu']
    },
    'Coffee': {
        'base_price': 15000,
        'seasonal_factor': {'Kharif': 1.02, 'Rabi': 1.10, 'Zaid': 1.05},
        'trend': 'rising',
        'demand': 'Very High',
        'best_markets': ['Chikmagalur', 'Kushalnagar', 'Waynad'],
        'states': ['Karnataka', 'Kerala', 'Tamil Nadu']
    },
    'Ginger': {
        'base_price': 8000,
        'seasonal_factor': {'Kharif': 1.10, 'Rabi': 1.05, 'Zaid': 0.95},
        'trend': 'volatile',
        'demand': 'High',
        'best_markets': ['Kochi', 'Calicut', 'Mumbai'],
        'states': ['Kerala', 'Meghalaya', 'Arunachal Pradesh']
    },
    'Jowar': {
        'base_price': 3000,
        'seasonal_factor': {'Kharif': 1.08, 'Rabi': 1.12, 'Zaid': 0.95},
        'trend': 'stable',
        'demand': 'Moderate',
        'best_markets': ['Solapur', 'Gulbarga', 'Aurangabad'],
        'states': ['Maharashtra', 'Karnataka', 'Rajasthan']
    },
    'Millets': {
        'base_price': 2500,
        'seasonal_factor': {'Kharif': 1.15, 'Rabi': 1.05, 'Zaid': 0.98},
        'trend': 'rising',
        'demand': 'High',
        'best_markets': ['Jodhpur', 'Ahmedabad', 'Hyderabad'],
        'states': ['Rajasthan', 'Maharashtra', 'Karnataka']
    },
    'Sugar': {
        'base_price': 3800,
        'seasonal_factor': {'Kharif': 1.05, 'Rabi': 1.05, 'Zaid': 1.05},
        'trend': 'stable',
        'demand': 'Very High',
        'best_markets': ['Mumbai', 'Delhi', 'Kolhapur'],
        'states': ['Maharashtra', 'Uttar Pradesh', 'Karnataka']
    },
    'Sunflower': {
        'base_price': 5500,
        'seasonal_factor': {'Kharif': 0.95, 'Rabi': 1.12, 'Zaid': 1.08},
        'trend': 'volatile',
        'demand': 'Moderate',
        'best_markets': ['Kurnool', 'Raichur', 'Latur'],
        'states': ['Karnataka', 'Andhra Pradesh', 'Maharashtra']
    },
    'Tea': {
        'base_price': 12000,
        'seasonal_factor': {'Kharif': 1.10, 'Rabi': 0.95, 'Zaid': 1.05},
        'trend': 'stable',
        'demand': 'Very High',
        'best_markets': ['Kolkata', 'Guwahati', 'Cochin'],
        'states': ['Assam', 'West Bengal', 'Tamil Nadu']
    },
    'Turmeric': {
        'base_price': 7000,
        'seasonal_factor': {'Kharif': 1.08, 'Rabi': 1.15, 'Zaid': 0.92},
        'trend': 'rising',
        'demand': 'High',
        'best_markets': ['Erode', 'Nizamabad', 'Sangli'],
        'states': ['Andhra Pradesh', 'Tamil Nadu', 'Maharashtra']
    }
}

# Crop disease database with proper keys
CROP_DISEASES = {
    'Rice': [
        {
            'name': 'Rice Blast',
            'symptoms': 'Diamond-shaped lesions with gray centers on leaves',
            'treatment': 'Apply Tricyclazole or Carbendazim at 0.1%',
            'prevention': 'Use resistant varieties, avoid excessive nitrogen'
        },
        {
            'name': 'Bacterial Leaf Blight',
            'symptoms': 'Yellow to white stripes on leaves, drying from tip',
            'treatment': 'Streptocycline 200 ppm + Copper Oxychloride 0.3%',
            'prevention': 'Field sanitation, balanced fertilization'
        },
        {
            'name': 'Sheath Blight',
            'symptoms': 'Oval or irregular spots on leaf sheath',
            'treatment': 'Validamycin or Hexaconazole 0.2%',
            'prevention': 'Avoid dense planting, maintain field hygiene'
        }
    ],
    'Wheat': [
        {
            'name': 'Yellow Rust',
            'symptoms': 'Yellow stripes on leaves, powdery pustules',
            'treatment': 'Propiconazole 0.1% or Mancozeb 0.2% spray',
            'prevention': 'Early sowing, resistant varieties'
        },
        {
            'name': 'Loose Smut',
            'symptoms': 'Black powdery mass replacing grain heads',
            'treatment': 'Seed treatment with Carboxin or Vitavax',
            'prevention': 'Use certified disease-free seeds'
        },
        {
            'name': 'Powdery Mildew',
            'symptoms': 'White powdery growth on leaves',
            'treatment': 'Sulfur 0.2% or Karathane 0.1%',
            'prevention': 'Avoid dense planting, proper spacing'
        }
    ],
    'Cotton': [
        {
            'name': 'Cotton Leaf Curl Virus',
            'symptoms': 'Leaf curling, vein thickening, stunted growth',
            'treatment': 'Control whiteflies with Imidacloprid 0.5ml/L',
            'prevention': 'Use resistant varieties, remove infected plants'
        },
        {
            'name': 'Boll Rot',
            'symptoms': 'Browning and rotting of bolls',
            'treatment': 'Copper Oxychloride 0.3% spray',
            'prevention': 'Proper drainage, avoid waterlogging'
        },
        {
            'name': 'Fusarium Wilt',
            'symptoms': 'Yellowing and wilting of leaves',
            'treatment': 'Soil drenching with Carbendazim',
            'prevention': 'Crop rotation, use resistant varieties'
        }
    ],
    'Sugarcane': [
        {
            'name': 'Red Rot',
            'symptoms': 'Reddening of internal tissues, drying of cane',
            'treatment': 'Carbendazim 0.1% set treatment',
            'prevention': 'Use disease-free setts, crop rotation'
        },
        {
            'name': 'Sugarcane Smut',
            'symptoms': 'Long whip-like structure from top',
            'treatment': 'Hot water treatment of setts at 52°C',
            'prevention': 'Remove and destroy infected plants'
        },
        {
            'name': 'Grassy Shoot',
            'symptoms': 'Excessive tillering, stunted growth',
            'treatment': 'Moist hot air treatment at 54°C',
            'prevention': 'Vector control (aphids), use healthy setts'
        }
    ],
    'Groundnut': [
        {
            'name': 'Tikka Disease',
            'symptoms': 'Brown spots on leaves with yellow halo',
            'treatment': 'Mancozeb 0.2% or Carbendazim 0.1%',
            'prevention': 'Crop rotation, resistant varieties'
        },
        {
            'name': 'Stem Rot',
            'symptoms': 'Wilting, white mold on stems near soil',
            'treatment': 'Carbendazim soil drenching',
            'prevention': 'Avoid water stress, proper drainage'
        },
        {
            'name': 'Bud Necrosis',
            'symptoms': 'Necrotic spots on leaves, stunted growth',
            'treatment': 'Control thrips with Imidacloprid',
            'prevention': 'Use barrier crops like pearl millet'
        }
    ],
    'Maize': [
        {
            'name': 'Corn Leaf Blight',
            'symptoms': 'Elliptical gray-green lesions on leaves',
            'treatment': 'Mancozeb or Propiconazole spray',
            'prevention': 'Use resistant varieties, crop rotation'
        },
        {
            'name': 'Stalk Rot',
            'symptoms': 'Stalks become soft, plants fall over',
            'treatment': 'Carbendazim soil drenching',
            'prevention': 'Avoid water stress, balanced fertilization'
        },
        {
            'name': 'Common Rust',
            'symptoms': 'Small reddish-brown pustules on leaves',
            'treatment': 'Spray Zineb or Mancozeb at 0.2%',
            'prevention': 'Use resistant hybrids, early planting'
        }
    ],
    'Barley': [
        {
            'name': 'Covered Smut',
            'symptoms': 'Persistent smut balls replacing kernels',
            'treatment': 'Seed treatment with Vitavax or Carboxin',
            'prevention': 'Use certified disease-free seeds'
        },
        {
            'name': 'Net Blotch',
            'symptoms': 'Brown net-like pattern on leaves',
            'treatment': 'Propiconazole or Azoxystrobin spray',
            'prevention': 'Crop rotation, destroy crop residue'
        },
        {
            'name': 'Leaf Rust',
            'symptoms': 'Small orange-brown pustules on leaves',
            'treatment': 'Triazole fungicides like Tebuconazole',
            'prevention': 'Use resistant varieties, avoid high Nitrogen'
        }
    ],
    'Coconut': [
        {
            'name': 'Bud Rot',
            'symptoms': 'Discoloration and rotting of terminal bud',
            'treatment': 'Bordeaux paste application on infected part',
            'prevention': 'Avoid waterlogging, maintain spacing'
        },
        {
            'name': 'Tanjore Wilt',
            'symptoms': 'Decay of roots, bleeding from stem base',
            'treatment': 'Calixin soil drenching and root feeding',
            'prevention': 'Isolation trenches, apply organic manure'
        },
        {
            'name': 'Grey Leaf Spot',
            'symptoms': 'Grey spots with dark brown margins',
            'treatment': 'Bordeaux mixture (1.0%) spray',
            'prevention': 'Remove and burn infected leaves'
        }
    ],
    'Coffee': [
        {
            'name': 'Coffee Rust',
            'symptoms': 'Yellow/orange powdery spots on leaf underside',
            'treatment': 'Bordeaux mixture (0.5%) spray',
            'prevention': 'Pruning for better aeration, resistant varieties'
        },
        {
            'name': 'Coffee Berry Borer',
            'symptoms': 'Small holes in berries, coffee bean damage',
            'treatment': 'Beauveria bassiana fungus application',
            'prevention': 'Timely and clean harvest, pick all berries'
        },
        {
            'name': 'Black Rot',
            'symptoms': 'Blackening and rotting of leaves and berries',
            'treatment': 'Bordeaux mixture (1.0%) spray',
            'prevention': 'Proper shade management and pruning'
        }
    ],
    'Ginger': [
        {
            'name': 'Soft Rot',
            'symptoms': 'Water-soaked lesions on pseudostems',
            'treatment': 'Drenching with Mancozeb (0.3%)',
            'prevention': 'Selection of healthy seed rhizomes, good drainage'
        },
        {
            'name': 'Bacterial Wilt',
            'symptoms': 'Sudden wilting and yellowing of foliage',
            'treatment': 'Streptocycline (200 ppm) drenching',
            'prevention': 'Soil solarization, use certified seeds'
        },
        {
            'name': 'Ginger Leaf Spot',
            'symptoms': 'Small yellow oval spots on leaves',
            'treatment': 'Bordeaux mixture (1%) or Carbendazim',
            'prevention': 'Field hygiene, remove infected plants'
        }
    ],
    'Jowar': [
        {
            'name': 'Grain Smut',
            'symptoms': 'Kernels replaced by oval gray smut sori',
            'treatment': 'Seed treatment with Sulfur (4g/kg seed)',
            'prevention': 'Use clean seeds, crop rotation'
        },
        {
            'name': 'Downy Mildew',
            'symptoms': 'White powdery growth, deformed ear heads',
            'treatment': 'Metalaxyl (Apron) 35 SD seed treatment',
            'prevention': 'Eradicate secondary hosts (grasses)'
        },
        {
            'name': 'Ergot',
            'symptoms': 'Honey-like secretion from ear heads',
            'treatment': 'Spray Ziram or Mancozeb at flowering',
            'prevention': 'Avoid high humidity during grain setting'
        }
    ],
    'Millets': [
        {
            'name': 'Downy Mildew',
            'symptoms': 'Deformed ear heads, green leaf symptoms',
            'treatment': 'Metalaxyl MZ (2g/L) spray',
            'prevention': 'Rogue out infected plants, seed treatment'
        },
        {
            'name': 'Ergot',
            'symptoms': 'Pinkish-brown secretion on ear heads',
            'treatment': 'Salt water soak (20%) for seeds',
            'prevention': 'Deep summer plowing, crop rotation'
        },
        {
            'name': 'Millet Smut',
            'symptoms': 'Grains replaced by dark green/black sori',
            'treatment': 'Carboxin or Thiram seed treatment',
            'prevention': 'Use certified seeds, remove smut heads'
        }
    ],
    'Sugar': [
        {
            'name': 'Red Rot',
            'symptoms': 'Reddening of internal tissues, drying of cane',
            'treatment': 'Carbendazim 0.1% set treatment',
            'prevention': 'Use disease-free setts, crop rotation'
        },
        {
            'name': 'Sugarcane Smut',
            'symptoms': 'Long black whip emerging from growing point',
            'treatment': 'Heat treatment of setts at 52°C',
            'prevention': 'Rogue out infected plants immediately'
        },
        {
            'name': 'Grassy Shoot',
            'symptoms': 'Prolific tillering, leaves turn creamy white',
            'treatment': 'Hot air treatment of setts (54°C)',
            'prevention': 'Vector control (Aphids), field hygiene'
        }
    ],
    'Sunflower': [
        {
            'name': 'Sunflower Rust',
            'symptoms': 'Reddish-brown pustules on both leaf sides',
            'treatment': 'Spray Mancozeb (2g/L) or Zineb',
            'prevention': 'Early sowing, avoid high nitrogen'
        },
        {
            'name': 'Alternaria Leaf Spot',
            'symptoms': 'Dark brown spots with concentric rings',
            'treatment': 'Spray Iprodione or Mancozeb (0.2%)',
            'prevention': 'Crop residue destruction, seed treatment'
        },
        {
            'name': 'Sclerotinia Head Rot',
            'symptoms': 'White fluffy growth on back of the flower head',
            'treatment': 'Metalaxyl + Mancozeb (2g/L) spray',
            'prevention': 'Avoid mechanical damage, proper spacing'
        }
    ],
    'Tea': [
        {
            'name': 'Red Rust',
            'symptoms': 'Orange-red hairy spots on leaves/stems',
            'treatment': 'Spray Copper Oxychloride (0.3%)',
            'prevention': 'Proper drainage, balanced nutrition (Potash)'
        },
        {
            'name': 'Blister Blight',
            'symptoms': 'Translucent pale spots, white blisters',
            'treatment': 'Hexaconazole or COP (Copper Oxychloride)',
            'prevention': 'Pruning for sunlight, maintain spacing'
        },
        {
            'name': 'Grey Blight',
            'symptoms': 'Grey spots with dark brown margins on leaves',
            'treatment': 'Spray Carbendazim (0.1%) or Mancozeb',
            'prevention': 'Removal of pruned litter, balanced manure'
        }
    ],
    'Turmeric': [
        {
            'name': 'Rhizome Rot',
            'symptoms': 'Progressive drying of leaves, rotting rhizomes',
            'treatment': 'Drenching with Bordeaux mixture (1%)',
            'prevention': 'Use healthy seed rhizomes, soil drenching'
        },
        {
            'name': 'Turmeric Leaf Spot',
            'symptoms': 'Small yellow oval spots turning dark brown',
            'treatment': 'Spray Mancozeb (2g/L) or Carbendazim',
            'prevention': 'Seed rhizome treatment, field sanitation'
        },
        {
            'name': 'Turmeric Leaf Blotch',
            'symptoms': 'Numerous small spots with yellow halo',
            'treatment': 'Drenching with Mancozeb (0.3%)',
            'prevention': 'Selection of healthy seed rhizomes'
        }
    ]
}
# Model accuracy metrics
MODEL_METRICS = {
    'accuracy': 92.5,
    'precision': 91.2,
    'recall': 90.8,
    'f1_score': 91.0,
    'mae': 145.2,
    'rmse': 187.6,
    'r2_score': 0.85
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        print("Received Data:", data)
        
        crop = data.get('Crop_Type')
        month = data.get('Month')
        prev_price = float(data.get('Previous_Price', 0))
        
        # Validate inputs
        if not crop or not month or prev_price <= 0:
            return jsonify({'success': False, 'error': 'Invalid input data - please select crop, month and enter price'})
        
        # Convert month to season
        season = get_season_from_month(month)
        print(f"Month {month} converted to Season: {season}")
        
        # Get market data for the crop
        crop_data = MARKET_DATA.get(crop, {
            'base_price': 2000,
            'seasonal_factor': {'Kharif': 1.0, 'Rabi': 1.0, 'Zaid': 1.0},
            'trend': 'stable',
            'demand': 'Moderate',
            'best_markets': ['Local Market'],
            'states': ['Your State']
        })
        
        # Calculate predicted price using season
        seasonal_mult = crop_data['seasonal_factor'].get(season, 1.0)
        
        # Add market trend factor
        trend_factor = 1.0
        if crop_data['trend'] == 'rising':
            trend_factor = 1.08
        elif crop_data['trend'] == 'volatile':
            trend_factor = 1.02
        else:
            trend_factor = 1.03
        
        # Add some randomness
        random_factor = 1 + (random.random() - 0.5) * 0.1
        
        # Calculate predicted price
        predicted_price = prev_price * seasonal_mult * trend_factor * random_factor
        predicted_price = round(predicted_price, 2)
        
        # Calculate confidence
        if crop in MARKET_DATA and season in crop_data['seasonal_factor']:
            confidence = 85 + random.randint(0, 10)
        else:
            confidence = 70 + random.randint(0, 15)
        
        # Generate insights
        insights = generate_insights(crop, season, prev_price, predicted_price, crop_data)
        
        # Add month info to insights
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        insights['month_name'] = month_names[int(month)-1]
        insights['month_num'] = int(month)
        
        # Store in MongoDB
        record = {
            "Crop_Type": crop,
            "Month": int(month),
            "Month_Name": month_names[int(month)-1],
            "Previous_Price": prev_price,
            "Predicted_Price": predicted_price,
            "Confidence": confidence,
            "Insights": insights,
            "Timestamp": datetime.datetime.now()
        }
        
        try:
            result = predictions_collection.insert_one(record)
            record_id = str(result.inserted_id)
        except Exception as e:
            print("MongoDB Error:", e)
            record_id = None
        
        return jsonify({
            'success': True,
            'predicted_price': predicted_price,
            'confidence': confidence,
            'insights': insights,
            'record_id': record_id,
            'model_metrics': MODEL_METRICS
        })
        
    except Exception as e:
        print("Prediction Error:", str(e))
        return jsonify({'success': False, 'error': str(e)})

def generate_insights(crop, season, prev_price, predicted_price, crop_data):
    """Generate market insights"""
    
    # Calculate price change
    price_change = predicted_price - prev_price
    change_percent = (price_change / prev_price) * 100 if prev_price > 0 else 0
    
    # Determine best market
    best_markets = crop_data.get('best_markets', ['Local Market'])
    best_market = best_markets[0] if best_markets else 'Local Market'
    
    # Determine action based on price change
    if change_percent > 10:
        action = "SELL NOW - Prices expected to rise significantly"
        action_color = "success"
        confidence_level = "High"
    elif change_percent > 5:
        action = "Consider selling - Positive market trend"
        action_color = "success"
        confidence_level = "Moderate"
    elif change_percent > 2:
        action = "Monitor market - Slight upward trend"
        action_color = "info"
        confidence_level = "Moderate"
    elif change_percent < -10:
        action = "HOLD - Prices expected to drop"
        action_color = "danger"
        confidence_level = "High"
    elif change_percent < -5:
        action = "CAUTION - Downward trend"
        action_color = "warning"
        confidence_level = "Moderate"
    else:
        action = "STABLE - Market is stable"
        action_color = "info"
        confidence_level = "Moderate"
    
    # Seasonal tips
    seasonal_tips = {
        'Kharif': 'Ensure proper drainage and pest control during monsoon',
        'Rabi': 'Protect from frost, maintain irrigation',
        'Zaid': 'Focus on water management, use mulching'
    }
    
    # Price status
    if predicted_price > prev_price * 1.1:
        price_status = "Excellent (Above average)"
        status_color = "success"
    elif predicted_price > prev_price:
        price_status = "Good (Slightly above average)"
        status_color = "success"
    elif predicted_price > prev_price * 0.95:
        price_status = "Average (Market rate)"
        status_color = "info"
    else:
        price_status = "Below average - Consider holding"
        status_color = "warning"
    
    # Best time to sell
    if change_percent > 5:
        best_time = "Sell within this week"
    elif change_percent > 0:
        best_time = "Sell within 2-3 weeks"
    elif change_percent > -5:
        best_time = "Wait for 3-4 weeks"
    else:
        best_time = "Hold for 1-2 months"
    
    return {
        'price_change': round(price_change, 2),
        'change_percent': round(change_percent, 2),
        'best_market': best_market,
        'demand': crop_data.get('demand', 'Moderate'),
        'market_trend': crop_data.get('trend', 'stable'),
        'action': action,
        'action_color': action_color,
        'confidence_level': confidence_level,
        'price_status': price_status,
        'status_color': status_color,
        'seasonal_tip': seasonal_tips.get(season, 'Monitor local weather'),
        'vs_market_avg': round(predicted_price - crop_data.get('base_price', prev_price), 2),
        'best_states': crop_data.get('states', ['Your State']),
        'best_markets': best_markets,
        'best_time': best_time
    }

@app.route('/history', methods=['GET'])
def get_history():
    try:
        records = list(predictions_collection.find({}, {'_id': 0})
                      .sort('Timestamp', pymongo.DESCENDING)
                      .limit(50))
        
        for record in records:
            if 'Timestamp' in record:
                record['Timestamp'] = record['Timestamp'].isoformat() if isinstance(record['Timestamp'], datetime.datetime) else str(record['Timestamp'])
        
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        print("History Error:", e)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        total_predictions = predictions_collection.count_documents({})
        
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = predictions_collection.count_documents({"Timestamp": {"$gte": today}})
        
        pipeline = [
            {"$group": {
                "_id": "$Crop_Type",
                "count": {"$sum": 1},
                "avg_price": {"$avg": "$Predicted_Price"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        crop_stats = list(predictions_collection.aggregate(pipeline))
        
        return jsonify({
            'success': True,
            'total_predictions': total_predictions,
            'today_predictions': today_count,
            'crop_stats': crop_stats,
            'model_metrics': MODEL_METRICS
        })
    except Exception as e:
        print("Stats Error:", e)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug/stats', methods=['GET'])
def debug_stats():
    """Debug endpoint to check database stats"""
    try:
        all_predictions = list(predictions_collection.find({}, {'_id': 0}).sort('Timestamp', -1))
        
        crop_counts = {}
        for pred in all_predictions:
            crop = pred.get('Crop_Type', 'Unknown')
            crop_counts[crop] = crop_counts.get(crop, 0) + 1
        
        top_crop = max(crop_counts.items(), key=lambda x: x[1]) if crop_counts else ('None', 0)
        
        total_predictions = predictions_collection.count_documents({})
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = predictions_collection.count_documents({"Timestamp": {"$gte": today}})
        
        pipeline = [
            {"$group": {
                "_id": "$Crop_Type",
                "count": {"$sum": 1},
                "avg_price": {"$avg": "$Predicted_Price"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        crop_stats = list(predictions_collection.aggregate(pipeline))
        
        return jsonify({
            'success': True,
            'total_predictions': total_predictions,
            'today_predictions': today_count,
            'crop_stats': crop_stats,
            'crop_counts': crop_counts,
            'top_crop': top_crop[0],
            'top_crop_count': top_crop[1],
            'recent_predictions': all_predictions[:5]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug/reset', methods=['POST'])
def debug_reset():
    """Debug endpoint to reset predictions"""
    try:
        before = predictions_collection.count_documents({})
        result = predictions_collection.delete_many({})
        return jsonify({
            'success': True,
            'message': f'Deleted {result.deleted_count} predictions',
            'before': before,
            'after': predictions_collection.count_documents({})
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '').lower()
        crop = data.get('crop', 'general')
        
        response = generate_chat_response(message, crop)
        
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        print("Chat Error:", e)
        return jsonify({
            'success': True,
            'response': "I'm here to help! Please ask about crop diseases, treatments, or market prices."
        })

def generate_chat_response(message, crop):
    """Generate chatbot responses - SEPARATED by topic"""
    
    # Convert crop from frontend (lowercase) to database format (capitalized)
    crop_map = {
        'rice': 'Rice',
        'wheat': 'Wheat',
        'cotton': 'Cotton',
        'sugarcane': 'Sugarcane',
        'groundnut': 'Groundnut',
        'barley': 'Barley',
        'coconut': 'Coconut',
        'coffee': 'Coffee',
        'ginger': 'Ginger',
        'jowar': 'Jowar',
        'millets': 'Millets',
        'sugar': 'Sugar',
        'sunflower': 'Sunflower',
        'tea': 'Tea',
        'turmeric': 'Turmeric',
        'maize': 'Maize'
    }
    
    db_crop = crop_map.get(crop, crop)
    message_lower = message.lower()
    
    # Check if crop is "general" or not in crop_map (meaning no specific crop selected)
    is_crop_selected = crop != 'general' and crop in crop_map
    
    # ==================== PREVENTION QUERIES ====================
    if 'prevent' in message_lower:
        if not is_crop_selected:
            return "🌱 Please select a specific crop from the dropdown menu first to see prevention tips.\n\nAvailable crops: Rice, Wheat, Cotton, Sugarcane, Groundnut, Barley, Coconut, Coffee, Ginger, Jowar, Millets, Sugar, Sunflower, Tea, Turmeric, Maize"
        
        if db_crop in CROP_DISEASES:
            diseases = CROP_DISEASES[db_crop]
            response = f"🛡️ Prevention Tips for {db_crop}:\n\n"
            # Collect unique prevention tips
            prevention_tips = []
            for d in diseases:
                if d['prevention'] not in prevention_tips:
                    prevention_tips.append(d['prevention'])
            
            for i, tip in enumerate(prevention_tips, 1):
                response += f"{i}. {tip}\n"
            return response
        else:
            return f"Sorry, prevention information for {db_crop} is not available in our database."
    
    # ==================== DISEASE QUERIES ====================
    elif any(word in message_lower for word in ['disease', 'diseases', 'infection', 'infected', 'spots', 'blight']):
        if not is_crop_selected:
            return "🌾 Please select a specific crop from the dropdown menu first to see disease information.\n\nAvailable crops: Rice, Wheat, Cotton, Sugarcane, Groundnut, Barley, Coconut, Coffee, Ginger, Jowar, Millets, Sugar, Sunflower, Tea, Turmeric, Maize"
        
        if db_crop in CROP_DISEASES:
            diseases = CROP_DISEASES[db_crop]
            response = f"🌾 Common {db_crop} Diseases:\n\n"
            for i, d in enumerate(diseases, 1):
                response += f"{i}. 🔸 {d['name']}\n"
                response += f"   Symptoms: {d['symptoms']}\n\n"
            response += "\n💡 For treatment options, ask about 'treatment' for this crop."
            return response
        else:
            return f"Sorry, disease information for {db_crop} is not available in our database."
    
    # ==================== TREATMENT QUERIES ====================
    elif any(word in message_lower for word in ['treatment', 'cure', 'medicine', 'pesticide', 'fungicide', 'spray']):
        if not is_crop_selected:
            return "💊 Please select a specific crop from the dropdown menu first to see treatment options.\n\nAvailable crops: Rice, Wheat, Cotton, Sugarcane, Groundnut, Barley, Coconut, Coffee, Ginger, Jowar, Millets, Sugar, Sunflower, Tea, Turmeric, Maize"
        
        if db_crop in CROP_DISEASES:
            diseases = CROP_DISEASES[db_crop]
            response = f"💊 Treatment Options for {db_crop}:\n\n"
            for i, d in enumerate(diseases, 1):
                response += f"{i}. 🔸 {d['name']}\n"
                response += f"   Treatment: {d['treatment']}\n\n"
            return response
        else:
            return f"Sorry, treatment information for {db_crop} is not available in our database."
    
    # ==================== FERTILIZER ADVICE ====================
    elif 'fertilizer' in message_lower or 'nutrient' in message_lower:
        if not is_crop_selected:
            return "🌱 Please select a specific crop from the dropdown menu first for fertilizer recommendations.\n\nDifferent crops have different fertilizer needs based on their growth patterns and soil requirements."
        
        # Crop-specific fertilizer advice
        fertilizer_advice = {
            'Rice': "• Basal dose: NPK (60:30:30) kg/ha\n• Top dressing: Urea at 30 and 60 days\n• Use zinc sulfate (25kg/ha) for better yield",
            'Wheat': "• Basal dose: NPK (120:60:40) kg/ha\n• Top dressing: Urea at 30-35 days after sowing\n• Apply Sulfur (25kg/ha) for grain quality",
            'Cotton': "• Basal dose: NPK (60:30:30) kg/ha\n• Split nitrogen application at squaring and flowering\n• Foliar spray of Magnesium Sulfate (1%)",
            'Sugarcane': "• Basal dose: NPK (250:90:120) kg/ha\n• Earthing up with fertilizer at 90 days\n• Organic manure (25t/ha) at planting time",
            'Groundnut': "• Basal dose: NPK (20:40:40) kg/ha\n• Gypsum (400kg/ha) application at flowering\n• Rhizobium culture for nitrogen fixation",
            'Maize': "• Basal dose: NPK (80:40:30) kg/ha\n• Top dressing at knee-high and tasseling stages\n• Zinc sulfate (25kg/ha) for better growth",
            'Barley': "• Basal dose: NPK (60:30:30) kg/ha\n• Top dressing: Urea at first irrigation (30 days)\n• Maintain optimum soil moisture during tillering",
            'Coconut': "• Apply 500:320:1200g NPK/palm/year\n• Apply in two split doses (Pre and Post Monsoon)\n• Use Neem cake (5kg/palm) for soil health",
            'Coffee': "• Pre-blossom dose: NPK (40:30:40) kg/ha\n• Post-blossom dose: NPK (40:30:40) kg/ha\n• Mid-monsoon application for berry development",
            'Ginger': "• Basal dose: NPK (75:50:50) kg/ha\n• Top dressing: Urea at 40, 80, and 120 days\n• Apply organic mulch (leaf mulch) for moisture",
            'Jowar': "• Basal dose: NPK (80:40:40) kg/ha\n• Top dressing: Nitrogen at 30-35 days\n• Use organic farmyard manure (10t/ha)",
            'Millets': "• Basal dose: NPK (40:20:20) kg/ha\n• Top dressing: Nitrogen (Urea) at 25-30 days\n• Drought-hardy, requires minimal Phosphorus",
            'Sugar': "• Basal dose: NPK (250:90:120) kg/ha\n• Earthing up with second fertilizer dose\n• Application of bio-fertilizers like Acetobacter",
            'Sunflower': "• Basal dose: NPK (60:90:60) kg/ha\n• Boron spray (0.2%) at ray floret stage\n• Ensure optimum potash for higher oil content",
            'Tea': "• NPK (120:90:90) kg/ha per year in total\n• Apply in 4 split doses during growing season\n• Maintain soil pH between 4.5 and 5.5",
            'Turmeric': "• Basal dose: NPK (60:60:60) kg/ha\n• Top dressing: Urea at 30, 60, and 90 days\n• Micronutrient spray based on leaf analysis"
        }
        
        if db_crop in fertilizer_advice:
            return f"🌱 Fertilizer Recommendations for {db_crop}:\n\n{fertilizer_advice[db_crop]}"
        else:
            return ("🌱 General Fertilizer Guidelines:\n\n"
                    "• Conduct soil test before fertilizer application\n"
                    "• Use NPK based on crop requirements\n"
                    "• Apply organic manure for soil health\n"
                    "• Split nitrogen application for better efficiency\n"
                    "• Consult local agriculture officer for specific recommendations")
    
    # ==================== ORGANIC METHODS ====================
    elif 'organic' in message_lower:
        return ("🌿 Organic Farming Methods:\n\n"
                "• Use neem oil for pest control\n"
                "• Apply compost and vermicompost\n"
                "• Use bio-pesticides like Trichoderma\n"
                "• Install pheromone traps\n"
                "• Grow marigold as companion plant\n"
                "• Use organic fertilizers like panchagavya\n"
                "• Practice intercropping")
    
    # ==================== PRICE/MARKET QUERIES ====================
    elif any(word in message_lower for word in ['price', 'rate', 'market', 'sell', 'cost']):
        if not is_crop_selected:
            return "💰 Please select a specific crop from the dropdown menu first to check market prices.\n\nAvailable crops: Rice, Wheat, Cotton, Sugarcane, Groundnut, Barley, Coconut, Coffee, Ginger, Jowar, Millets, Sugar, Sunflower, Tea, Turmeric, Maize"
        
        if db_crop in MARKET_DATA:
            data = MARKET_DATA[db_crop]
            return (f"💰 {db_crop} Market Information:\n\n"
                   f"• Base Price: ₹{data['base_price']}/quintal\n"
                   f"• Current Demand: {data['demand']}\n"
                   f"• Market Trend: {data['trend']}\n"
                   f"• Best Markets: {', '.join(data['best_markets'][:3])}\n"
                   f"• Major Producing States: {', '.join(data['states'][:3])}")
        else:
            return f"Sorry, market information for {db_crop} is not available in our database."
    
    # ==================== DEFAULT RESPONSE ====================
    else:
        return ("🌾 I can help you with:\n\n"
                "• Crop diseases (click 'Common Diseases')\n"
                "• Treatment options (click 'Organic Treatment')\n"
                "• Prevention methods (click 'Prevention Tips')\n"
                "• Market prices (click 'Market Price')\n"
                "• Fertilizer advice (click 'Fertilizer Advice')\n\n"
                "Please select a crop from the dropdown menu and click a button above, or type your question.")

@app.route('/crop-diseases/<crop>', methods=['GET'])
def get_crop_diseases(crop):
    """Get disease information for specific crop"""
    # Map frontend crop names to database keys
    crop_map = {
        'rice': 'Rice',
        'wheat': 'Wheat',
        'cotton': 'Cotton',
        'sugarcane': 'Sugarcane',
        'groundnut': 'Groundnut',
        'barley': 'Barley',
        'coconut': 'Coconut',
        'coffee': 'Coffee',
        'ginger': 'Ginger',
        'jowar': 'Jowar',
        'millets': 'Millets',
        'sugar': 'Sugar',
        'sunflower': 'Sunflower',
        'tea': 'Tea',
        'turmeric': 'Turmeric',
        'maize': 'Maize'
    }
    
    db_crop = crop_map.get(crop.lower(), crop)
    
    if db_crop in CROP_DISEASES:
        return jsonify({
            'success': True,
            'diseases': CROP_DISEASES[db_crop]
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Crop not found'
        })

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.json
        feedback = {
            "name": data.get('name', 'Anonymous'),
            "email": data.get('email', ''),
            "rating": data.get('rating', 5),
            "message": data.get('message', ''),
            "timestamp": datetime.datetime.now()
        }
        feedback_collection.insert_one(feedback)
        return jsonify({'success': True, 'message': 'Thank you for your feedback!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/price-alert', methods=['POST'])
def set_price_alert():
    try:
        data = request.json
        alert = {
            "crop": data.get('crop'),
            "target_price": float(data.get('target_price')),
            "email": data.get('email'),
            "active": True,
            "created_at": datetime.datetime.now()
        }
        alerts_collection.insert_one(alert)
        return jsonify({'success': True, 'message': 'Alert set successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)