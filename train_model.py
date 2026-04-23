import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

def get_season(month_num):
    if month_num in [7, 8, 9, 10]:
        return 'Kharif'
    elif month_num in [11, 12, 1, 2, 3]:
        return 'Rabi'
    else:
        return 'Zaid'

def load_and_preprocess_data(filepath='crop_price_dataset.csv'):
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    
    # Ensure date parsing
    df['month'] = pd.to_datetime(df['month'])
    
    # Sort by commodity and date to calculate previous price correctly
    df = df.sort_values(by=['commodity_name', 'month']).reset_index(drop=True)
    
    # Calculate Previous Price (1 month shift per commodity)
    df['Previous_Price'] = df.groupby('commodity_name')['avg_modal_price'].shift(1)
    
    # Drop rows with NaN (the first month for each commodity)
    df = df.dropna(subset=['Previous_Price'])
    
    # Extract Season
    df['Season'] = df['month'].dt.month.apply(get_season)
    
    # Rename columns for consistency with the app
    df = df.rename(columns={
        'commodity_name': 'Crop_Type',
        'avg_modal_price': 'Current_Price'
    })
    
    # Select only the needed columns
    df = df[['Crop_Type', 'Season', 'Previous_Price', 'Current_Price']]
    
    print(f"Data preprocessed. Shape: {df.shape}")
    return df

def train():
    df = load_and_preprocess_data()
    
    # Preprocessing
    df_encoded = pd.get_dummies(df, columns=['Crop_Type', 'Season'])
    
    X = df_encoded.drop('Current_Price', axis=1)
    y = df_encoded['Current_Price']
    
    # Save the feature columns for prediction alignment later
    feature_columns = X.columns.tolist()
    joblib.dump(feature_columns, 'feature_columns.pkl')
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    rmse = np.sqrt(mse)
    print(f"Model trained successfully. RMSE: {rmse:.2f}")
    
    print("Saving model...")
    joblib.dump(model, 'model.pkl')
    print("Model saved to model.pkl and feature columns to feature_columns.pkl")

if __name__ == '__main__':
    train()
