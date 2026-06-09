# Agriculture Price Prediction

A Flask-based web application that predicts crop prices using historical data and provides market insights, disease diagnosis, and treatment recommendations.

## Features
- **Price Prediction**: Predicts future market prices for various crops.
- **Market Insights**: Provides recommendations on whether to sell or hold based on trends.
- **Crop Disease Information**: Diagnosis and treatment for common crop diseases.
- **Chatbot Assistant**: AI-powered assistant for agriculture-related queries.
- **Price Alerts**: Set alerts for target prices.

## Tech Stack
- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Deployment**: Render / Railway

## Local Setup
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your MongoDB URI in environment variables:
   ```bash
   export MONGO_URI="your_mongodb_connection_string"
   ```
4. Run the app:
   ```bash
   python app.py
   ```

## Deployment
This app is ready to be deployed on **Render**.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Environment Variable**: Set `MONGO_URI` to your MongoDB Atlas connection string.
