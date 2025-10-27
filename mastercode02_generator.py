# mastercode02_generator.py
import random
import re

DATA = {
    'demographics': {
        'Male': {'Under 5 years': 1198, '5 to 9 years': 3111, '10 to 14 years': 1278, '15 to 19 years': 2678, '20 to 24 years': 4219, '25 to 29 years': 2760, '30 to 34 years': 2403, '35 to 39 years': 1639, '40 to 44 years': 2209, '45 to 49 years': 2105, '50 to 54 years': 2397, '55 to 59 years': 1192, '60 to 64 years': 2253, '65 to 69 years': 1707, '70 to 74 years': 1788, '75 to 79 years': 1041, '80 to 84 years': 805, '85 years and over': 932},
        'Female': {'Under 5 years': 1627, '5 to 9 years': 2215, '10 to 14 years': 1264, '15 to 19 years': 2854, '20 to 24 years': 5275, '25 to 29 years': 2965, '30 to 34 years': 2653, '35 to 39 years': 1936, '40 to 44 years': 2267, '45 to 49 years': 1924, '50 to 54 years': 1481, '55 to 59 years': 1444, '60 to 64 years': 2326, '65 to 69 years': 2183, '70 to 74 years': 1880, '75 to 79 years': 1209, '80 to 84 years': 1063, '85 years and over': 1159}
    },
    'households': {'Married-couple family household': 11825, 'Male householder, no spouse present, family household': 946, 'Female householder, no spouse present, family household': 2985, 'Nonfamily household': 15406},
    'employment': {'16-19': {'emp_ratio': 0.445, 'unemp_rate': 0.104}, '20-24': {'emp_ratio': 0.645, 'unemp_rate': 0.051}, '25-29': {'emp_ratio': 0.785, 'unemp_rate': 0.064}, '30-34': {'emp_ratio': 0.749, 'unemp_rate': 0.046}, '35-44': {'emp_ratio': 0.850, 'unemp_rate': 0.0}, '45-54': {'emp_ratio': 0.741, 'unemp_rate': 0.074}, '55-59': {'emp_ratio': 0.682, 'unemp_rate': 0.0}, '60-64': {'emp_ratio': 0.626, 'unemp_rate': 0.017}, '65-74': {'emp_ratio': 0.187, 'unemp_rate': 0.0}, '75+': {'emp_ratio': 0.059, 'unemp_rate': 0.0}},
    'marital_status': {'Male': {'15-19': {'Never married': 1.0},'20-34': {'Now married (except separated)': 0.24, 'Widowed': 0.0, 'Divorced': 0.031, 'Separated': 0.001, 'Never married': 0.728}, '35-44': {'Now married (except separated)': 0.641, 'Widowed': 0.012, 'Divorced': 0.072, 'Separated': 0.019, 'Never married': 0.256}, '45-54': {'Now married (except separated)': 0.669, 'Widowed': 0.005, 'Divorced': 0.157, 'Separated': 0.007, 'Never married': 0.161}, '55-64': {'Now married (except separated)': 0.581, 'Widowed': 0.029, 'Divorced': 0.253, 'Separated': 0.012, 'Never married': 0.126}, '65+': {'Now married (except separated)': 0.573, 'Widowed': 0.151, 'Divorced': 0.167, 'Separated': 0.026, 'Never married': 0.083}}, 'Female': {'15-19': {'Now married (except separated)': 0.006, 'Separated': 0.006, 'Never married': 0.988},'20-34': {'Now married (except separated)': 0.265, 'Widowed': 0.004, 'Divorced': 0.031, 'Separated': 0.005, 'Never married': 0.695}, '35-44': {'Now married (except separated)': 0.622, 'Widowed': 0.017, 'Divorced': 0.128, 'Separated': 0.028, 'Never married': 0.206}, '45-54': {'Now married (except separated)': 0.564, 'Widowed': 0.048, 'Divorced': 0.162, 'Separated': 0.013, 'Never married': 0.213}, '55-64': {'Now married (except separated)': 0.523, 'Widowed': 0.075, 'Divorced': 0.255, 'Separated': 0.046, 'Never married': 0.101}, '65+': {'Now married (except separated)': 0.356, 'Widowed': 0.355, 'Divorced': 0.216, 'Separated': 0.019, 'Never married': 0.054}}}
}

class TempPerson:
    def __init__(self, age, sex, education, marital_status, employment):
        self.age, self.sex, self.education, self.marital_status, self.employment = age, sex, education, marital_status, employment

def assign_education(age):
    if age < 3: return 'too_young'
    if age < 5: return 'Nursery/Preschool'
    if age < 10: return 'Elementary (K-5)'
    if age < 14: return 'Middle (6-8)'
    if age < 18: return 'High School (9-12)'
    if age < 22: return 'University'
    return random.choices(
        ['high_school_completed', 'college_dropout', 'college_completed', 'masters_completed'],
        weights=[35, 25, 30, 10], k=1
    )[0]

def assign_marital_status(age, sex):
    if age < 15: return "Never married"
    age_key = '15-19' if 15 <= age <= 19 else '20-34' if 20 <= age <= 34 else '35-44' if 35 <= age <= 44 else '45-54' if 45 <= age <= 54 else '55-64' if 55 <= age <= 64 else '65+'
    dist = DATA['marital_status'][sex][age_key]
    return random.choices(list(dist.keys()), weights=list(dist.values()), k=1)[0]

def assign_employment(age):
    if age < 16: return "Too Young"
    age_key = '16-19' if 16 <= age <= 19 else '20-24' if 20 <= age <= 24 else '25-29' if 25 <= age <= 29 else '30-34' if 30 <= age <= 34 else '35-44' if 35 <= age <= 44 else '45-54' if 45 <= age <= 54 else '55-59' if 55 <= age <= 59 else '60-64' if 60 <= age <= 64 else '65-74' if 65 <= age <= 74 else '75+'
    rates = DATA['employment'][age_key]
    if age >= 65: return "Employed" if random.random() < rates['emp_ratio'] else "Retired"
    lfp_rate = rates['emp_ratio'] / (1 - rates['unemp_rate']) if (1 - rates['unemp_rate']) > 0 else rates['emp_ratio']
    rand_val = random.random()
    if rand_val < rates['unemp_rate']: return "Unemployed"
    if rand_val < lfp_rate: return "Employed"
    return "Not in Labor Force"

def generate_initial_population():
    print("--- Starting Programmatic Population Generation ---")
    generated_agents = []
    for sex, age_groups in DATA['demographics'].items():
        for age_group_str, count in age_groups.items():
            age_nums = [int(s) for s in re.findall(r'\d+', age_group_str)]
            min_age, max_age = (0, 4) if 'Under' in age_group_str else (85, 95) if 'over' in age_group_str else (age_nums[0], age_nums[1])
            for _ in range(count):
                age = random.randint(min_age, max_age)
                education = assign_education(age)
                employment = assign_employment(age)
                generated_agents.append(TempPerson(age=age, sex=sex, education=education, marital_status=assign_marital_status(age, sex), employment=employment))
    print(f"SUCCESS: Generated exactly {len(generated_agents)} temporary agent data objects.")
    return generated_agents