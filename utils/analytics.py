import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

def analyze_spending_patterns(df: pd.DataFrame) -> Dict:
    """Analyze spending patterns and detect seasonality."""
    try:
        expense_df = df[df['type'] == 'expense'].copy()
        expense_df['created_at'] = pd.to_datetime(expense_df['created_at'])
        expense_df.set_index('created_at', inplace=True)
        
        # Daily spending pattern
        daily = expense_df.resample('D')['amount'].sum().fillna(0)
        weekly_pattern = daily.groupby(daily.index.dayofweek).mean()
        monthly_pattern = expense_df.resample('M')['amount'].sum()
        
        # Detect seasonality
        if len(monthly_pattern) >= 12:
            yearly_pattern = monthly_pattern.groupby(monthly_pattern.index.month).mean()
            high_spending_months = yearly_pattern.nlargest(3)
            low_spending_months = yearly_pattern.nsmallest(3)
        else:
            high_spending_months = pd.Series()
            low_spending_months = pd.Series()
        
        return {
            'weekly_pattern': weekly_pattern.to_dict(),
            'monthly_trend': monthly_pattern.to_dict(),
            'high_spending_months': high_spending_months.to_dict(),
            'low_spending_months': low_spending_months.to_dict()
        }
    except Exception as e:
        logger.error(f"Error analyzing spending patterns: {str(e)}")
        return {}

def forecast_spending(df: pd.DataFrame, forecast_periods: int = 3) -> Dict:
    """Forecast future spending using exponential smoothing."""
    try:
        expense_df = df[df['type'] == 'expense'].copy()
        expense_df['created_at'] = pd.to_datetime(expense_df['created_at'])
        monthly_spending = expense_df.set_index('created_at').resample('M')['amount'].sum()
        
        if len(monthly_spending) < 4:
            return {'error': 'Not enough data for forecasting'}
            
        # Fit exponential smoothing model
        model = ExponentialSmoothing(
            monthly_spending,
            seasonal_periods=12,
            trend='add',
            seasonal='add',
            damped=True
        ).fit()
        
        # Generate forecast
        forecast = model.forecast(forecast_periods)
        confidence_intervals = model.prediction_intervals(forecast_periods)
        
        return {
            'forecast': forecast.to_dict(),
            'lower_bound': confidence_intervals['lower'].to_dict(),
            'upper_bound': confidence_intervals['upper'].to_dict()
        }
    except Exception as e:
        logger.error(f"Error forecasting spending: {str(e)}")
        return {'error': str(e)}

def analyze_category_correlations(df: pd.DataFrame) -> Dict:
    """Analyze correlations between spending categories."""
    try:
        expense_df = df[df['type'] == 'expense'].copy()
        pivot = expense_df.pivot_table(
            index=pd.Grouper(key='created_at', freq='M'),
            columns='category',
            values='amount',
            aggfunc='sum'
        ).fillna(0)
        
        correlations = pivot.corr()
        
        # Find strongest positive and negative correlations
        upper_triangle = correlations.where(np.triu(np.ones(correlations.shape), k=1).astype(bool))
        strongest_positive = upper_triangle.unstack().nlargest(3)
        strongest_negative = upper_triangle.unstack().nsmallest(3)
        
        return {
            'correlations': correlations.to_dict(),
            'strongest_positive': strongest_positive.to_dict(),
            'strongest_negative': strongest_negative.to_dict()
        }
    except Exception as e:
        logger.error(f"Error analyzing category correlations: {str(e)}")
        return {}

def predict_category(description: str, historical_data: pd.DataFrame) -> str:
    """Predict transaction category based on historical data."""
    try:
        # Prepare training data
        X = historical_data['description'].str.lower().str.split()
        X = pd.get_dummies(X.apply(pd.Series).stack()).sum(level=0)
        
        # Fit model for each category
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LinearRegression()
        y = pd.get_dummies(historical_data['category'])
        model.fit(X_scaled, y)
        
        # Prepare new description
        new_desc = pd.Series([description.lower()])
        new_X = pd.get_dummies(new_desc.str.split().apply(pd.Series).stack()).sum(level=0)
        new_X = new_X.reindex(columns=X.columns, fill_value=0)
        
        # Make prediction
        new_X_scaled = scaler.transform(new_X)
        pred_proba = model.predict(new_X_scaled)
        predicted_category = y.columns[pred_proba.argmax()]
        
        return predicted_category
    except Exception as e:
        logger.error(f"Error predicting category: {str(e)}")
        return None

def get_spending_insights(df: pd.DataFrame) -> Dict:
    """Generate comprehensive spending insights."""
    try:
        expense_df = df[df['type'] == 'expense'].copy()
        expense_df['created_at'] = pd.to_datetime(expense_df['created_at'])
        
        # Calculate various metrics
        total_spending = expense_df['amount'].sum()
        avg_transaction = expense_df['amount'].mean()
        spending_trend = expense_df.set_index('created_at').resample('M')['amount'].sum().pct_change()
        
        # Identify unusual transactions
        std_dev = expense_df['amount'].std()
        mean_amount = expense_df['amount'].mean()
        unusual_transactions = expense_df[
            expense_df['amount'] > (mean_amount + 2 * std_dev)
        ][['description', 'amount', 'category']].to_dict('records')
        
        # Category breakdown
        category_breakdown = expense_df.groupby('category')['amount'].agg([
            'sum', 'mean', 'count'
        ]).to_dict('index')
        
        return {
            'total_spending': total_spending,
            'avg_transaction': avg_transaction,
            'spending_trend': spending_trend.to_dict(),
            'unusual_transactions': unusual_transactions,
            'category_breakdown': category_breakdown
        }
    except Exception as e:
        logger.error(f"Error generating spending insights: {str(e)}")
        return {}
