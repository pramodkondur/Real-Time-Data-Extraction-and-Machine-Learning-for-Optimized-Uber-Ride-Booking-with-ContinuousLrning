# Real-Time Uber Ride Price, Waiting Time, and Ride Time Prediction

## Project Overview
This project aims to optimize Uber ride booking by analyzing real-time data and predicting the best times to book based on ride price, waiting time, and ride time for selected routes. Data is collected from Uber every hour between 7 AM and 11 PM for 7 specific locations in Chennai, with predictions delivered via a user-friendly Streamlit interface.

The system continuously scrapes real-time Uber data and stores it in a MySQL database. Machine Learning (ML) models are used to make predictions on the best times for booking, taking into account factors like latitude, longitude, and distance. New data is processed daily at 9 AM, with models retrained automatically using MLFlow to track and improve model performance.

## Project Features
- **Real-time Data Collection:** Data is scraped from Uber for 7 locations, with all possible routes among them captured in 1-hour intervals from 7 AM to 11 PM.
- **Database Management:** Data is stored in MySQL and continuously collected using job scheduling, while MLFlow is used to track and manage model training.
- **Latitude and Longitude Calculation:** Geolocation is computed using the Nominatim API, with route distances calculated using the Open Route Service API.
- **Machine Learning Model:** A Random Forest model was trained on known locations and optimized using hyperparameter tuning. The system was validated using unseen locations and routes, providing accurate results.
- **Streamlit Interface:** Users can select locations, input addresses, and check predictions for future times. Predictions are restricted to within a 20km radius of the midpoint of selected locations, preventing discrepancy due to longer distances.
- **Prediction for Future Hours:** The system predicts ride prices and times for the next three hours, showing percentage changes and helping users save money.

## Key Components

### 1. User Interface Development
- A user-friendly **Streamlit** interface where users can input ride details (route from, route to, pickup time) and receive fare predictions.
- Interactive map integration allows users to visualize location selection and check boundaries (20 km radius) of valid locations.

### 2. Real-Time Data Extraction
- Data scraped from Uber for locations including waiting time, drop time, vehicle type, fare estimates, and surge pricing.
- **MySQL** database used to store this data for future analysis.

### 3. Machine Learning Model for Prediction
- Initially trained using **Random Forest** and **XGBoost** for known routes, hyperparameter tuned using **MLFlow**.
- Latitude and longitude calculated using **Nominatim** and distance computed via **Open Route Service API**.
- Random Forest provided the best accuracy, tested on unseen data using 2 of the 7 locations for validation.

### 4. Prediction and Time Optimization
- Predictions for ride price, wait time, and ride time calculated using the model.
- Users can view recommendations for future rides with predicted prices and percentage changes for upcoming hours.

### 5. Model Performance and Retraining
- Daily retraining using newly collected data. Best model is selected and tracked using **MLFlow**.
- Evaluation using metrics like **Mean Absolute Error (MAE)** and accuracy.

## Tools and Technologies
- **Programming Language:** Python
- **Libraries:** Pandas, Scikit-learn, Pydeck, Streamlit, Geopy, MLFlow
- **Web Scraping:** BeautifulSoup, Selenium
- **Mapping:** Open Route Service API, Pydeck
- **APIs:** Nominatim, Open Route Service API
- **Database:** MySQL
- **Machine Learning Frameworks:** Scikit-learn (Random Forest, XGBoost)

## Setup Instructions

1. **Install Required Packages:**
    ```bash
    pip install streamlit pandas scikit-learn geopy mlflow pydeck
    ```

2. **Clone Repository:**
    ```bash
    git clone https://github.com/pramodkondur/UberWise-EndtoEnd.git
    cd uber-price-prediction
    ```

3. **Configure MySQL Database:**
    - Set up MySQL to store the scraped Uber data.
    - Update database credentials accordingly.

4. **Run Streamlit Application:**
    ```bash
    streamlit run app.py
    ```

## Future Enhancements
- **Additional Routes:** Expand beyond Chennai to include other cities.
- **Live Integration with Uber API:** Direct integration for real-time Uber API access for better data accuracy.
---

This project provides users with an efficient, data-driven way to predict the best time to book an Uber ride, ensuring cost savings and convenience by analyzing real-time data and leveraging machine learning models.
