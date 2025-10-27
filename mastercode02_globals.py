# mastercode02_globals.py

# --- Main Simulation Containers ---
POPULATION = []
HOUSEHOLDS = {}
MARRIAGES = []

# --- Resource Dictionaries ---
EDUCATION_RESOURCE = {}
EMPLOYER_RESOURCE = {}

# --- ID Counters ---
_person_id_counter = 73440; _household_id_counter = 31162; _marriage_id_counter = 0; _car_id_counter = 0
def next_person_id(): global _person_id_counter; _person_id_counter += 1; return _person_id_counter
def next_household_id(): global _household_id_counter; _household_id_counter += 1; return _household_id_counter
def next_marriage_id(): global _marriage_id_counter; _marriage_id_counter += 1; return _marriage_id_counter
def next_car_id(): global _car_id_counter; _car_id_counter += 1; return f"CAR_{_car_id_counter}"

# --- Annual Data for Logging ---
ANNUAL_SUMMARY_DATA = {}
VEHICLE_EVENTS = []
TRIP_SUMMARY = []
RATES_LOG = []
annual_education_stats = {}

# --- Annual trackers for capped financial resources ---
annual_savings_accepted = 0
annual_loans_disbursed = 0
annual_gov_support_disbursed = 0
refused_log = {'savings': 0, 'loans': 0, 'gov_support': 0}

# --- Global Modifiers for Trigger Events ---
event_birth_rate_modifier = 1.0
event_death_rate_modifier = 1.0
event_employment_rate_modifier = 1.0
event_inflation_modifier = 1.0
event_income_modifier = 1.0
event_gov_support_modifier = 1.0
event_gov_cap_modifier = 1.0
event_dropout_prob = 0.0

# --- Global Modifiers for ARIMA Forecasts ---
arima_birth_rate_modifier = 1.0
arima_death_rate_modifier = 1.0
arima_marriage_rate_modifier = 1.0

# --- Latest calculated score for dynamic managers ---
latest_economic_index = 100.0