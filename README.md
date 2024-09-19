# Real-Time Data Extraction and Machine Learning for Optimized Uber Ride Booking with Continuous Learning

## Project Overview
This project is aimed at optimizing Uber ride bookings through real-time data analysis and machine learning techniques, incorporating a continuous learning framework. By leveraging data extraction methods and predictive modelling, the project seeks to enhance user experience by forecasting optimal booking times based on various factors, including ride prices and wait times. It further explores the significance, methodology, key features, technological components, and future enhancements.

## Why this project?
The rise of ride-sharing services like Uber has transformed urban transportation. However, users often struggle with fluctuating ride prices and varying wait times. This project addresses these challenges by leveraging real-time data and machine learning models to predict the best times for booking Uber rides. The goal is to provide a data-driven approach that ensures cost savings and improved convenience for users.

## Significance of the Project

As urban populations continue to grow, the demand for efficient transportation solutions increases. By optimizing ride booking times, this project can lead to:

**Cost Savings:** Predicting lower fare times can help users save money.

**Reduced Wait Times:** Identifying optimal booking periods can minimize waiting for rides.

**Enhanced User Experience:** Providing users with reliable predictions can improve satisfaction.


## Project Features

**Continuous Real-time Data Collection:** Data is scraped from Uber for seven locations, capturing all possible routes at one-hour intervals from 7 AM to 11 PM.

**Database Management:** A MySQL database is employed for data storage, facilitating continuous collection through job scheduling.

**Geolocation API Integration:** Latitude and longitude are calculated using the Nominatim API, and distances are computed via the Open Route Service API to improve model scope outside the scraped locations data.

**Machine Learning Models:** Various ML models, including Random Forest and XGBoost, are trained, tested and tuned on historical data to predict optimal booking times.

**Interactive Web Interface:** A Streamlit application allows users to select locations and view predictions for future booking times while visualizing maps using Pydeck

**Continuous Learning Framework:** The system is designed to continuously learn from new data, automatically retraining models to adapt to changing patterns in ride demand and pricing using MlFlow.

## Model Architecture and Tools Used:

![CHEESE!](./images/architechture.png)

**Programming Language:** Python

**IDE:** PyCharm and Jupyter notebook

**Web Scraping:** Selenium

**Mapping:** Pydeck, Geopy

**APIs:** Nominatim, Open Route Service

**Database:** MySQL

**Machine Learning Frameworks:** Scikit-learn 

**Version Control:** Git, GitHub

**Model Logging and Continuous Learning:** MlFlow

## Methodology

### 1. Data Collection 

**Data Scraping:**

Data was scrapped from the Uber website using Selenium and is continuously scrapped at 1 hour intervals between 7 AM and 11 PM IST for 7 locations in the city of Chennai, Tamil Nadu and all it’s possible routes among them.

**Types of Data:**

Data collected included 
- Ride type (Uber Go, Uber Sedan, Uber XL, Uber Auto, Uber Moto, Uber Premier), 
- Maximum ride persons (1,2,3,4,6) 
- Route location from
- Route location to
- Ride request date
- Ride request time 
- Waiting time (minutes)
- Reaching_time (minutes)
- Ride time (minutes) 
- Ride price in Rupees

The following images illustrate a row, total rows x columns and date period of the collected data as of September 19, 2024:

![CHEESE!](./images/samplerow.png)
![CHEESE!](./images/datesimages.png)
![CHEESE!](./images/totalrows.png)

### 2. Data Preprocessing and Exploration

**Data Formatting:**

Since data was got at hourly intervals, not all data are got at exactly at the hour as selenium takes a while to scrape all the data from these 42 routes (For example starts scrapping at 9:00 AM but may finish at 9:05 AM or 9:10 AM). Thus we round it off to the hour and if there are multiple occurrences of the same data (I.e. same ride type, locations) then the data is averaged among them to give unique values of data for that time slot.  Date formatting and time formatting was done as well

**Feature Engineering:**

New features, including day of the week, and hour of the day, were added to enhance model predictions while removing unwanted columns.

A depiction of the that is shown below.

![CHEESE!](./images/filteredtbl.png)

**Exploratory Data Analysis (EDA):**

EDA was performed to analyze key metrics such as the distribution of ride times, prices, and waiting times by day of week and hour of day. They are represented below.

![CHEESE!](./images/dist1.png)
![CHEESE!](./images/dist2.png)
![CHEESE!](./images/dist3.png)
![CHEESE!](./images/dist4.png)
![CHEESE!](./images/dist5.png)
![CHEESE!](./images/dist6.png)

**Distribution** of ride price, ride waiting time, ride time also show us that they are not skewed much and can thus be utilized by the machine learning models. They are shown below.

![CHEESE!](./images/di1.png)
![CHEESE!](./images/di2.png)
![CHEESE!](./images/di3.png)

**Correlation analysis** among the numerical are shown as below. 
Although hours, day of week likely affect the price, they are not totally co-related as they are fluctuations among them thus we don't need to drop any columns but proceed with next steps

![CHEESE!](./images/heatmap.png)

### 3. Model Selection, Training, and Testing

**Model Selection:**

For our project we went ahead and chose Linear Regression as our base model and ensemble learning techniques like Random Forest Regressor and XGBoost Regressor as they are able to deal with both normal distribution data and even skewed data and since our model is slightly skewed we went ahead and chose these models. Overall, these ensemble technique work the best for linear regression problems.

**Model Evaluation:**

Model was then trained after conducting a train-test split with encoding the categorical features and scaling numerical features. Model metrics of Mean Absolute Error (MAE), Mean Squared Error(MSE), and R2 Score were utilized as metics
The results obtained were as follows:

![CHEESE!](./images/lr1.png)
![CHEESE!](./images/rf1.png)
![CHEESE!](./images/xg1.png)

From the observations, we can clearly see that Random Forest performs the best, while Linear Regression performs the worst due to it’s nature of not being able to capture non-linearity in data.
Model was hyper-tuned using RandomizedSearchCV for different values of no. of estimators, max depth of the model, min samples split, and min samples leaf.
Results indicated that the default model performed the best. Thus we can utilize that. 

### 4. Further Improvement:

**Why?**

So why do we need further improvement? The Current model does give us good performance metrics but it is limited to only the 7 locations and the 42 unique routes among them.  In order to expand the scope of our model, we need to go beyond just the 42 routes. In order for our model in real world scenario where we can use these data for multiple locations in the city we can consider utilizing geo-locational features

**Geo-locational features using APIs:**

Thus latitudes and longitudes of these locations and the distances between the 41 routes were calculated using APIs. Nominatim API was used to obtain latitudes, longitudes while Open Route Service API was used to get the distances among these routes. Results are as follows:

![CHEESE!](./images/latlong.png)
![CHEESE!](./images/dist.png)

### 5. Model Training and Testing on New Data

**Different Train-Test Split:**

Train-Test split was not done randomly but by completely hiding two locations and all it’s occurrence among the two and also any occurrence between it and other locations in the proposed train set, thereby these locations and it’s routes become completely new, unseen data to the model.

**Training, Testing, and Evaluation:** Models trained, tested and evaluated with results at this step as follows: 

![CHEESE!](./images/lr2.png)
![CHEESE!](./images/rf2.png)
![CHEESE!](./images/xg2.png)

Random Forest performs the best and although the performance is slightly lower than our model using location names instead of geo-locational features, the model still performs very well and thus we can utilize this model as it increases the scope of our project beyond the limited number of locations to choose from.

### 6. An Interactive Web Application

**Web App:** 

In order for users to be able to utilize what we have created we leveraged Streamlit for them to be able to use the application in real-time.

**Location Restriction:** 

Since the data collected was only from 7 locations in the city of Chennai, the best method was to restrict the selection of locations for from and to to be within 20 km of the mean of the other 7 locations. That way we can get accurate predictions of our values.

**Dynamic geo-locational features:**

Since we are using new locations, we need to fetch their corresponding latitudes, longitudes, and distances as well. This was dynamically done using the Nominatim API and Open Route Service API.

**Routes Mapping:**

Further, routes of selected locations was also mapped to give a visual appearance to the users of the road route using Open Route Service API.

**Error Handling:**

Errors were also handled if location exceeds the 20km radius and if there are invalid addresses 

**Prediction of Value:**

Upon selection of features, the app generates ride price, ride waiting time, and ride time for the selected date and hour. It also provides the values for the next three hours with percentage change and colour coding to help users with selecting the best ride enabling cost savings, convenience, and satisfaction.

### 7. Continuous Learning Framewor

**New data = New Model:**

To ensure that the model remains effective over time, a continuous learning framework is implemented. This involves:

**Scheduled Retraining:**

Models are automatically retrained on new data that is collected daily at 9 AM, allowing them to adapt to the latest trends and patterns.

**Model Performance Tracking and Best Model Selection:**

Using MLFlow, the performance of various models is tracked, while automatically selection the best-performing model. 

![CHEESE!](./images/MlFlow.png)

### 8. Demo

![CHEESE!](./images/demo1.png)
![CHEESE!](./images/demo2.png)
![CHEESE!](./images/demo3.png)
![CHEESE!](./images/demo4.png)

### 9. Future Enhancements

The project presents multiple avenues for future expansion:

**Additional Routes:** 

Extend the model's functionality to other cities and locations.

**Real-Time API Integration:** 

Establish direct connections with the Uber API for enhanced data accuracy and responsiveness.

**Enhanced Continuous Learning:** 

Incorporate user feedback and behavioural data to refine prediction algorithms further.

## Conclusion

This project successfully integrates real-time data extraction and machine learning techniques to optimize Uber ride bookings. The inclusion of a continuous learning framework ensures that the system adapts to evolving patterns in ride demand and pricing. By providing users with predictive insights into ride prices and wait times, it enhances the overall transportation experience. The project highlights the potential of data-driven approaches in urban mobility, paving the way for future innovations.

## References

- https://openrouteservice.org/
- https://nominatim.org/
- https://www.uber.com/in/en/
- https://scikit-learn.org/stable/
- https://mlflow.org/docs/latest/index.html
- https://www.selenium.dev/documentation/
- https://dev.mysql.com/
- https://deckgl.readthedocs.io/en/latest/layer.html
- https://docs.streamlit.io/

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

3. **Configure MySQL Database and scedhuler:**
    - Set up MySQL to store the scraped Uber data.
    - Update database credentials accordingly.
    - Run scheduler.py for the job to run on schedule

4. **Run Streamlit Application:**
    ```bash
    streamlit run app.py
    ```
## Link to the notebook files

You can view the code and in depth in the notebooks

[Data Preparation and Model Train/Test/Eval](./notebooks/main_notebook.ipynb)

[Fetch Lat/Long](./notebooks/get_lat_long.ipynb)

[Further Imrovement and Model Train/Test/Eval](./notebooks/DistanceModel.ipynb)

[Fetch Best Model](./notebooks/to_get_best_model.ipynb)


