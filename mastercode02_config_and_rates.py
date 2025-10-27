# mastercode02_config_and_rates.py
import numpy as np

# --- SIMULATION CONTROL ---
SIMULATION_DURATION = 50

# --- IMMIGRATION CONFIG ---
IMMIGRATION_CONFIG = {
    'base_annual_rate': 0.005,  # 0.5% of the population per year
    'age_range': (22, 35),
    'education_distribution': {
        'high_school_completed': 0.4,
        'college_completed': 0.6
    }
}

# --- FINANCIAL RESOURCE CAPACITIES ---
BANK_SAVINGS_ANNUAL_CAPACITY = 404_000_000
BANK_LOAN_ANNUAL_CAPACITY = 350_000_000
GOVERNMENT_SPENDING_ANNUAL_CAP = 200_000_000

# --- DEMOGRAPHIC RATES ---
RATES = {
    'Death Rates': {
        'Male': {'0-4': 0.0013, '5-9': 0.0001, '10-14': 0.0002, '15-19': 0.0006, '20-24': 0.0010, '25-29': 0.0014, '30-34': 0.0018, '35-39': 0.0023, '40-44': 0.0029, '45-49': 0.0037, '50-54': 0.0053, '55-59': 0.0080, '60-64': 0.0117, '65-69': 0.0164, '70-74': 0.0238, '75-79': 0.0378, '80-84': 0.0632, '85+': 0.15},
        'Female': {'0-4': 0.0011, '5-9': 0.0001, '10-14': 0.0001, '15-19': 0.0004, '20-24': 0.0006, '25-29': 0.0008, '30-34': 0.0010, '35-39': 0.0014, '40-44': 0.0021, '45-49': 0.0028, '50-54': 0.0041, '55-59': 0.0063, '60-64': 0.0097, '65-69': 0.0139, '70-74': 0.0204, '75-79': 0.0335, '80-84': 0.0577, '85+': 0.14}
    },
    'Fertility Rate': {
        'Married': {'15-19': 0.1737, '20-24': 0.4969, '25-29': 0.4969, '30-34': 0.4969, '35-39': 0.3294, '40-44': 0.2294, '45-49': 0.0294},
        'Unmarried': {'15-19': 0.180, '20-24': 0.290, '25-29': 0.270, '30-34': 0.130, '35-39': 0.0510, '40-44': 0.0001, '45-49': 0.0}
    },
    'Employment': {
        'Employed': {'15-19': 0.2, '20-24': 0.6, '25-29': 0.75, '30-34': 0.8, '35-39': 0.8, '40-44': 0.8, '45-49': 0.78, '50-54': 0.75, '55-59': 0.7, '60-64': 0.6, '65-69': 0.2, '70-74': 0.1, '75-79': 0.05, '80-84': 0.01, '85+': 0.0}
    }
}
SCENARIO_MULTIPLIERS = {
    'healthcare': {1: 1.5, 2: 1.2, 3: 1.0, 4: 0.8, 5: 0.6},
    'economy': {1: 0.7, 2: 0.9, 3: 1.0, 4: 1.1, 5: 1.2},
    'environmental': {1: 1.3, 2: 1.1, 3: 1.0, 4: 0.95, 5: 0.9},
    'transport': {
        1: {'car_purchase': 0.7, 'accident': 1.5}, 2: {'car_purchase': 0.9, 'accident': 1.2},
        3: {'car_purchase': 1.0, 'accident': 1.0}, 4: {'car_purchase': 1.1, 'accident': 0.9},
        5: {'car_purchase': 1.2, 'accident': 0.7},
    }
}
HISTORICAL_MACRO_DATA = {
    'Year': list(range(2000, 2024)),
    'Mortality Rate': [8.03, 8.09, 8.16, 8.08, 7.88, 7.99, 7.76, 7.6, 8.12, 7.89, 7.94, 8.07, 8.4, 8.22, 8.24, 8.44, 8.49, 8.64, 8.68, 8.7, 10.4, 10.5, 9.7, 9.2],
    'Birth Rate': [14.4, 14.1, 13.9, 14.1, 14, 14, 14.2, 14.3, 13.9, 13.5, 13, 12.7, 12.6, 12.4, 12.5, 12.4, 12.2, 11.8, 11.6, 11.4, 10.9, 11, 11.1, 11.6],
    'Employment Rate': [96.1, 95.3, 94.2, 94, 94.5, 94.9, 95.4, 95.4, 94.2, 90.7, 90.4, 91.1, 92.2, 92.6, 93.8, 94.9, 95.1, 95.6, 96.1, 96.3, 89.2, 94.6, 96.4, 96.4]
}
HISTORICAL_ECONOMIC_DATA = {
    'Year': list(range(2000, 2024)),
    'Top Tax Rate': [39.6, 39.1, 38.6, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 35.0, 39.6, 39.6, 39.6, 39.6, 39.6, 37.0, 37.0, 37.0, 37.0, 37.0, 37.0],
    'Salary Inflation': [3.7, 4.2, 3.0, 2.4, 2.4, 2.9, 3.9, 3.9, 3.4, 2.2, 1.9, 2.1, 1.9, 2.0, 2.1, 2.3, 2.6, 2.7, 2.9, 3.1, 4.6, 4.5, 4.9, 4.3],
    'Cost Inflation (CPI)': [3.4, 2.8, 1.6, 2.3, 2.7, 3.4, 3.2, 2.8, 3.8, -0.4, 1.6, 3.2, 2.1, 1.5, 1.6, 0.1, 1.3, 2.1, 2.4, 1.8, 1.2, 4.7, 8.0, 4.1],
    '30-Yr Mortgage': [8.05, 6.97, 6.54, 5.83, 5.84, 5.87, 6.41, 6.34, 6.03, 5.04, 4.69, 4.45, 3.66, 3.98, 4.17, 3.85, 3.65, 3.99, 4.54, 3.94, 3.11, 2.96, 5.34, 6.81]
}
ROAD_NETWORK_CAPACITY = {'interstate': 62000, 'highway': 38750, 'arterial': np.mean([34100, 31000, 27900])}

EMPLOYERS={
    'EMP01':{'name':'Healthcare System','capacity':12750},
    'EMP02':{'name':'Higher Education','capacity':6750},
    'EMP03':{'name':'City & County Gov.','capacity':3750},
    'EMP04':{'name':'Retail & Hospitality','capacity':7500},
    'EMP05':{'name':'Manufacturing','capacity':3000},
    'EMP06':{'name':'Small Businesses/Other','capacity':3750},
}
EMPLOYER_PROBS=[0.35,0.18,0.1,0.2,0.08,0.09]

EDUCATION_CAPACITIES={
    'Nursery/Preschool':2500,
    'Elementary (K-5)':5000,
    'Middle (6-8)':2200,
    'High School (9-12)':3200,
    'University':13500+1200,
    'Community College':5500,
    'masters_program':1500,
    'phd_program':500
}

SKILL_LEVELS=['Entry-Level / Low-Skill','Skilled Labor / Clerical','Mid-Level Professional','Senior Professional / Mgmt.']
INCOME_BANDS={'Healthcare System':[(25000,38000),(38000,55000),(55000,85000),(90000,250000)],'Higher Education':[(24000,35000),(35000,50000),(50000,75000),(80000,200000)],'City & County Gov.':[(25000,36000),(36000,52000),(52000,80000),(85000,160000)],'Retail & Hospitality':[(22000,32000),(32000,45000),(45000,70000),(70000,140000)],'Manufacturing':[(28000,40000),(40000,60000),(58000,90000),(90000,180000)],'Small Businesses/Other':[(24000,35000),(35000,58000),(50000,80000),(80000,200000)],}
PUBLIC_TRANSIT_CONFIG={'initial_buses':25,'initial_population':73440,'bus_capacity':33,'trips_per_bus_per_day':10}
CAR_AFFORDABILITY={'min_cost':6000,'min_household_income_threshold':30000}
COST_GRID={"Food":{"1_adult":[4242,6238,9345,12432],"2_adults_1_working":[7778,9667,12435,15169],"2_adults_2_working":[7778,9667,12435,15169]},"Child Care":{"1_adult":[0,7614,15229,18211],"2_adults_1_working":[0,0,0,0],"2_adults_2_working":[0,7614,15229,18211]},"Medical":{"1_adult":[3208,9333,9405,9482],"2_adults_1_working":[6905,10294,10566,10867],"2_adults_2_working":[6905,10294,10566,10867]},"Housing":{"1_adult":[10725,13484,13484,16738],"2_adults_1_working":[10785,13484,13484,16738],"2_adults_2_working":[10785,13484,13484,16738]},"Transportation":{"1_adult":[9405,10884,13711,15776],"2_adults_1_working":[10884,13711,15776,17501],"2_adults_2_working":[10884,13711,15776,17501]},"Civic":{"1_adult":[2589,4557,5031,6450],"2_adults_1_working":[4557,5031,6450,7156],"2_adults_2_working":[4557,5031,6450,7156]},"Internet & Mobile":{"1_adult":[1557,1557,1557,1557],"2_adults_1_working":[2139,2139,2139,2139],"2_adults_2_working":[2139,2139,2139,2139]},"Other":{"1_adult":[3770,7242,7587,9120],"2_adults_1_working":[7242,8033,9120,10117],"2_adults_2_working":[7242,8033,9120,10117]},}
GOV_SUPPORT_CONFIG={'single_parent_support':3000,'food_stamp_per_child':1500,'low_income_threshold_factor':1.25}
COMMUTATION_PURPOSE_RATES={'0-4':[0.0,0.0,0.1,0.2,0.1,0.6,0.0],'5-17':[0.0,0.6,0.1,0.15,0.05,0.1,0.0],'18-24':[0.4,0.3,0.1,0.1,0.05,0.05,0.0],'25-54':[0.6,0.05,0.15,0.05,0.05,0.1,0.0],'55-64':[0.4,0.0,0.2,0.2,0.1,0.1,0.0],'65+':[0.05,0.0,0.25,0.3,0.3,0.05,0.05],}
COMMUTATION_PURPOSES=["Work","School","Shopping","Leisure","Healthcare","Escort","Other"]