# Import the dependencies.
from flask import Flask, jsonify

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
# Measurement class
Measurement = Base.classes.measurement
# Station class
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################

# Homepage
@app.route('/')
def home():
    """List all available api routes."""
    return (
        # Welcome
        f"Welcome to my Honolulu, Hawaii climate API!<br/>"
        f"<br/>"
        # Menu Header
        f"Available Routes:<br/>"
        f"<br/>"
        # Basic Queries
        f"For Percipitation Data from over the last 12 Months:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"<br/>"
        f"For Stations referenced Information:<br/>"
        f"/api/v1.0/stations<br/>"
        f"<br/>"
        f"For Temperature OBServations of the most-active Station:<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<br/>"
        f"The following links can be used to find the minimum temperature, the average temperature, and the maximum temperature<br/>"
        f"To Search the API from a SPECIFIC START date to the MOST RECENT date (replace 'YYYY-MM-DD' with the date you wish to query!):<br/>"
        f"/api/v1.0/YYYY-MM-DD<br/>"
        f"<br/>"
        f"To Search the API from a SPECIFIC START date to a SPECIFIC END date (replace 'YYYY-MM-DD' with the start date you wish to query first end the end date you wish to query last!):<br/>"
        f"/api/v1.0/YYYY-MM-DD/YYYY-MM-DD"
        # User defined Queries
        
    )

# Precipitation route
@app.route('/api/v1.0/precipitation')
def get_precipitation():
    # Query to get the most recent date from the Measurement table
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

    # Calculate the date one year ago from the most recent date
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    one_year_ago = one_year_ago.strftime('%Y-%m-%d')

    # Query the database to get date and precipitation for the last year
    results = session.query(Measurement.date, Measurement.prcp).\
                filter(Measurement.date >= one_year_ago).\
                filter(Measurement.date <= most_recent_date).all()

    # Create a dictionary to store date as key and precipitation as value
    precipitation_data = {date: prcp for date, prcp in results}

    return jsonify(precipitation_data)


# Stations route
@app.route('/api/v1.0/stations')
def get_stations():
    # Query all stations from the Station table
    stations = session.query(Station).all()

    # Create a list to store station data as dictionaries
    station_list = []
    for station in stations:
        station_data = {
            'Station': station.station,
            'Name': station.name,
            'Latitude': station.latitude,
            'Longitude': station.longitude,
            'Elevation': station.elevation
        }
        station_list.append(station_data)

    # Return JSONified station data
    return jsonify(station_list)

# TOBS route
@app.route('/api/v1.0/tobs')
def get_temperature_observations():
    # Find the most active station ID from previous queries
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
                            group_by(Measurement.station).\
                            order_by(func.count(Measurement.station).desc()).first()[0]

    # Calculate the most recent date
    most_recent_date = session.query(func.max(Measurement.date)).filter(Measurement.station == most_active_station).scalar()

    # Calculate the date one year ago from the most recent date
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    one_year_ago = one_year_ago.strftime('%Y-%m-%d')

    # Query temperature observations for the most active station for the previous year
    results = session.query(Measurement.date, Measurement.tobs).\
                filter(Measurement.station == most_active_station).\
                filter(Measurement.date >= one_year_ago).\
                filter(Measurement.date <= most_recent_date).all()

    # Create a list of temperature observations
    temp_observation_list = [{'date': date, 'tobs': tobs} for date, tobs in results]

    # Create a dictionary containing station ID and temperature observations
    response_data = {
        'station_id': most_active_station,
        'temperature_observations': temp_observation_list
    }

    # Return JSONified response data
    return jsonify(response_data)

# Dynamic start route
@app.route('/api/v1.0/<start>')
def temp_start(start):
    # Query for TMIN, TAVG, and TMAX for dates greater than or equal to the start date
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
              filter(Measurement.date >= start).all()

    # Create a dictionary to store temperature data
    temp_data = {
        'start_date': start,
        'TMIN': results[0][0],
        'TAVG': results[0][1],
        'TMAX': results[0][2]
    }

    # Return JSONified temperature data
    return jsonify(temp_data)

# Dynamic start/end route
@app.route('/api/v1.0/<start>/<end>')
def temp_start_end(start, end):
    # Query for TMIN, TAVG, and TMAX for dates within the start-end range
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
              filter(Measurement.date >= start).\
              filter(Measurement.date <= end).all()

    # Create a dictionary to store temperature data
    temp_data = {
        'start_date': start,
        'end_date': end,
        'TMIN': results[0][0],
        'TAVG': results[0][1],
        'TMAX': results[0][2]
    }

    # Return JSONified temperature data
    return jsonify(temp_data)

#################################################
# Run script
#################################################
if __name__ == '__main__':
    app.run(debug=True)