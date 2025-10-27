# mastercode02_agents.py
import salabim as sim, pandas as pd, warnings, random
from copy import deepcopy
from statsmodels.tsa.arima.model import ARIMA
import numpy as np
from mastercode02_config_and_rates import (HISTORICAL_MACRO_DATA, HISTORICAL_ECONOMIC_DATA,
                                             INCOME_BANDS, SKILL_LEVELS, CAR_AFFORDABILITY,
                                             PUBLIC_TRANSIT_CONFIG, ROAD_NETWORK_CAPACITY,
                                             EMPLOYERS, GOV_SUPPORT_CONFIG,
                                             COMMUTATION_PURPOSE_RATES, COMMUTATION_PURPOSES,
                                             SIMULATION_DURATION, IMMIGRATION_CONFIG,
                                             BANK_LOAN_ANNUAL_CAPACITY, BANK_SAVINGS_ANNUAL_CAPACITY,
                                             GOVERNMENT_SPENDING_ANNUAL_CAP)
import mastercode02_globals as g
from mastercode02_utils import compute_household_cost

warnings.filterwarnings("ignore")

def log_vehicle_event(year, event_type, car_id, details):
    g.VEHICLE_EVENTS.append({'year': year, 'event': event_type, 'car_id': car_id, 'details': details})

class Person(sim.Component):
    def __init__(self, env, initial_data, population_list):
        super().__init__(env=env)
        self.id = initial_data['id']; self.age = initial_data['age']; self.sex = initial_data['sex']
        self.education = initial_data['education']; self.employment_status = initial_data['employment']
        self.employer = None; self.household_id = initial_data['household_id']
        self.marital_status = initial_data.get('marital_status', 'Single'); self.year_in_level = 0
        self.skill_level = None; self.annual_income = 0; self.gov_support_cum = 0; self.cars = []
        self.use_bus = False; self.accident_involvement = False; self.commute_purpose = "Other"
        self.layoff_status = False
        self.is_in_jc_school = False
        self.years_married = None

        self.start_age_nursery = random.choice([2, 3]); self.start_age_elementary = self.start_age_nursery + 2
        self.start_age_middle = self.start_age_elementary + 5; self.start_age_high_school = self.start_age_middle + 3
        self.start_age_college = self.start_age_high_school + 4; self.start_age_masters = self.start_age_college + 4
        self.start_age_phd = self.start_age_masters + 2

        if self.education in ['Nursery/Preschool', 'Elementary (K-5)', 'Middle (6-8)', 'High School (9-12)', 'University']:
            start_ages = {
                'Nursery/Preschool': self.start_age_nursery,
                'Elementary (K-5)': self.start_age_elementary,
                'Middle (6-8)': self.start_age_middle,
                'High School (9-12)': self.start_age_high_school,
                'University': self.start_age_college
            }
            self.year_in_level = max(1, int(self.age - start_ages.get(self.education, self.age) + 1))

        population_list.append(self)
        self.passivate()

    def process(self):
        if self.employer and self.employer in g.EMPLOYER_RESOURCE:
            yield self.request(g.EMPLOYER_RESOURCE[self.employer])

        while True:
            death_prob = self.env.RATES['Death Rates'][self.sex].get(self.get_age_group(), 0) * g.arima_death_rate_modifier * g.event_death_rate_modifier
            if random.random() < death_prob:
                self.die()
                break

            yield self.hold(1)
            self.age += 1

            if self.years_married is not None:
                self.years_married += 1

            self.update_education_cyclical()
            yield from self.update_employment_status()

            if self.sex == 'Female' and 15 <= self.age < 50:
                base_birth_prob = self.env.RATES['Fertility Rate']['Married' if 'Married' in self.marital_status else 'Unmarried'].get(self.get_age_group(), 0)
                final_birth_prob = base_birth_prob * g.arima_birth_rate_modifier * g.event_birth_rate_modifier
                if self.years_married is not None and self.years_married <= 10:
                    final_birth_prob *= 1.5
                if random.random() < final_birth_prob:
                    self.give_birth(g.HOUSEHOLDS, g.POPULATION)
            
            self._update_income_annually()
            self._manage_car_lifecycle()
            self._decide_on_car_purchase()
            self._update_commute_details()

    def update_education_cyclical(self):
        if self.education in ['High School (9-12)', 'University'] and random.random() < g.event_dropout_prob:
            self.education = 'high_school_dropout' if self.education == 'High School (9-12)' else 'college_dropout'
            self.year_in_level = 0
            return

        current_level = self.education
        if self.education in ['Nursery/Preschool', 'Elementary (K-5)', 'Middle (6-8)', 'High School (9-12)', 'University', 'masters_program', 'phd_program']:
            self.year_in_level += 1

        if self.age == self.start_age_nursery and current_level == 'too_young': self.education = 'Nursery/Preschool'; self.year_in_level = 1
        elif self.year_in_level > 2 and current_level == 'Nursery/Preschool': self.education = 'Elementary (K-5)'; self.year_in_level = 1
        elif self.year_in_level > 5 and current_level == 'Elementary (K-5)': self.education = 'Middle (6-8)'; self.year_in_level = 1
        elif self.year_in_level > 3 and current_level == 'Middle (6-8)': self.education = 'High School (9-12)'; self.year_in_level = 1
        elif self.year_in_level > 4 and current_level == 'High School (9-12)': self.education = 'high_school_completed' if random.random() < 0.95 else 'high_school_dropout'; self.year_in_level = 0
        elif self.education == 'high_school_completed' and self.age >= self.start_age_college:
            if random.random() < 0.60: self.education = 'University'; self.year_in_level = 1
        elif self.year_in_level > 4 and current_level == 'University': self.education = 'college_completed' if random.random() < 0.75 else 'college_dropout'; self.year_in_level = 0
        elif self.education == 'college_completed' and self.age >= self.start_age_masters:
            if random.random() < 0.10: self.education = 'masters_program'; self.year_in_level = 1
        elif self.year_in_level > 2 and current_level == 'masters_program': self.education = 'masters_completed' if random.random() < 0.90 else 'masters_dropout'; self.year_in_level = 0
        elif self.education == 'masters_completed' and self.age >= self.start_age_phd:
             if random.random() < 0.05: self.education = 'phd_program'; self.year_in_level = 1
        elif self.year_in_level > 4 and current_level == 'phd_program': self.education = 'phd_completed'; self.year_in_level = 0

    def die(self):
        current_year = int(self.env.now())
        if self.is_in_jc_school:
            res = g.EDUCATION_RESOURCE.get(self.education)
            if res and res in self.claimed_resources():
                self.release(res)
        if self.cars:
            household = g.HOUSEHOLDS.get(self.household_id)
            if household and household.get('members'):
                other_members = [p for p in household['members'] if p is not self and p.age >= 18]
                if other_members:
                    heir = sorted(other_members, key=lambda p: p.age, reverse=True)[0]
                    for car in self.cars:
                        heir.cars.append(car)
                        log_vehicle_event(current_year, 'Inheritance', car['id'], f"Owner {self.id} died, car inherited by Person {heir.id}")
                else:
                    for car in self.cars: log_vehicle_event(current_year, 'Retirement', car['id'], f"Owner {self.id} died, no heir in household.")
        if self.employer and self.employer in g.EMPLOYER_RESOURCE and g.EMPLOYER_RESOURCE[self.employer] in self.claimed_resources():
            self.release(g.EMPLOYER_RESOURCE[self.employer])
        household = g.HOUSEHOLDS.get(self.household_id)
        if household and self in household.get('members', []):
            household['deaths'] = household.get('deaths', 0) + 1
            household['members'].remove(self)
        if self in g.POPULATION:
            g.POPULATION.remove(self)
        self.cancel()

    def _manage_car_lifecycle(self):
        if not self.cars: return
        current_year = int(self.env.now())
        for car in self.cars[:]:
            car['age'] = car.get('age', 0) + 1
            if car['age'] > 10:
                self.cars.remove(car)
                log_vehicle_event(current_year, 'Retirement', car['id'], f"Car retired due to age. Owner: {self.id}")

    def _decide_on_car_purchase(self):
        if self.age < 18 or self.cars: return
        household = g.HOUSEHOLDS.get(self.household_id)
        if not household: return
        if household.get('total_income', 0) > CAR_AFFORDABILITY['min_household_income_threshold']:
            prob = 0.10
            if self.employment_status == 'Employed': prob = 0.30
            if random.random() < prob:
                new_car_id = g.next_car_id()
                self.cars.append({'id': new_car_id, 'age': 0})
                log_vehicle_event(int(self.env.now()), 'Purchase', new_car_id, f"Purchased by Person {self.id} in HH {self.household_id}")

    def _assign_skill_and_income(self):
        if self.employment_status != 'Employed' or not self.employer:
            self.skill_level = None; self.annual_income = 0
            return
        if self.education in ['masters_completed', 'phd_completed']: self.skill_level = SKILL_LEVELS[3]
        elif self.education == 'college_completed': self.skill_level = SKILL_LEVELS[2]
        elif self.education in ['high_school_completed', 'college_dropout']: self.skill_level = SKILL_LEVELS[1]
        else: self.skill_level = SKILL_LEVELS[0]
        employer_data = EMPLOYERS.get(self.employer)
        if not employer_data:
            self.annual_income = 0
            return
        employer_name = employer_data['name']
        skill_index = SKILL_LEVELS.index(self.skill_level); income_range = INCOME_BANDS[employer_name][skill_index]
        base_income = random.uniform(income_range[0], income_range[1])
        self.annual_income = base_income * g.event_income_modifier

    def _update_income_annually(self):
        if self.annual_income > 0:
            self.annual_income *= (1 + self.env.salary_inflation)

    def _update_commute_details(self):
        age_group = '0-4' if self.age <= 4 else '5-17' if self.age <= 17 else '18-24' if self.age <= 24 else '25-54' if self.age <= 54 else '55-64' if self.age <= 64 else '65+'
        weights = COMMUTATION_PURPOSE_RATES[age_group]
        self.commute_purpose = random.choices(COMMUTATION_PURPOSES, weights=weights, k=1)[0]
        g.TRIP_SUMMARY.append({'year': int(self.env.now()), 'purpose': self.commute_purpose})
        if self.cars:
            self.use_bus = False

    def update_employment_status(self):
        if self.employment_status == 'Employed' and random.random() < 0.05:
            self.layoff_status = True; self.employment_status = 'Unemployed'
            if self.employer and self.employer in g.EMPLOYER_RESOURCE and g.EMPLOYER_RESOURCE[self.employer] in self.claimed_resources():
                yield self.release(g.EMPLOYER_RESOURCE[self.employer])
            self.employer = None; self._assign_skill_and_income()
        if self.employment_status in ['Not in Labor Force', 'Unemployed'] and 18 <= self.age < 65:
            job_chance = self.env.RATES['Employment']['Employed'].get(self.get_age_group(), 0) * g.event_employment_rate_modifier
            if random.random() < job_chance:
                available = {n: r for n, r in g.EMPLOYER_RESOURCE.items() if r.available_quantity() > 0}
                if available:
                    chosen = random.choice(list(available.keys())); yield self.request(g.EMPLOYER_RESOURCE[chosen])
                    self.employment_status = 'Employed'; self.employer = chosen; self._assign_skill_and_income()

    def get_age_group(self):
        if self.age <= 4: return '0-4'
        if self.age <= 9: return '5-9'
        if self.age <= 14: return '10-14'
        if self.age <= 19: return '15-19'
        if self.age <= 24: return '20-24'
        if self.age <= 29: return '25-29'
        if self.age <= 34: return '30-34'
        if self.age <= 39: return '35-39'
        if self.age <= 44: return '40-44'
        if self.age <= 49: return '45-49'
        if self.age <= 54: return '50-54'
        if self.age <= 59: return '55-59'
        if self.age <= 64: return '60-64'
        if self.age <= 69: return '65-69'
        if self.age <= 74: return '70-74'
        if self.age <= 79: return '75-79'
        if self.age <= 84: return '80-84'
        return '85+'

    def give_birth(self, households, population_list):
        new_id = g.next_person_id()
        initial_data = {'id': new_id, 'age': 0, 'sex': random.choice(['Male', 'Female']), 'education': 'too_young', 'employment': 'Too Young', 'household_id': self.household_id, 'marital_status': 'Never married'}
        new_person = Person(self.env, initial_data, population_list)
        if self.household_id in households:
            households[self.household_id]['members'].append(new_person)
            households[self.household_id]['births'] = households[self.household_id].get('births', 0) + 1
        new_person.activate()


class EducationManager(sim.Component):
    def process(self):
        while True:
            yield self.hold(1)
            all_students = [p for p in g.POPULATION if p.is_in_jc_school]
            for student in all_students:
                res = g.EDUCATION_RESOURCE.get(student.education)
                if res and res in student.claimed_resources():
                    student.release(res)
                student.is_in_jc_school = False
            for level_name, resource in g.EDUCATION_RESOURCE.items():
                eligible_students = [p for p in g.POPULATION if p.education == level_name]
                random.shuffle(eligible_students)
                available_seats = int(resource.capacity())
                enrolled_count = 0
                for student in eligible_students:
                    if enrolled_count < available_seats:
                        student.request(resource)
                        student.is_in_jc_school = True
                        enrolled_count += 1
                    else:
                        student.is_in_jc_school = False
                total_eligible = len(eligible_students)
                refused_count = total_eligible - enrolled_count
                g.annual_education_stats[level_name] = {
                    'in_use': enrolled_count,
                    'refused': refused_count
                }

class ScenarioManager(sim.Component):
    def __init__(self, env, events):
        super().__init__(env=env)
        self.events = events
    def process(self):
        while True:
            g.event_birth_rate_modifier = 1.0; g.event_death_rate_modifier = 1.0
            g.event_employment_rate_modifier = 1.0; g.event_inflation_modifier = 1.0
            g.event_income_modifier = 1.0; g.event_gov_support_modifier = 1.0
            g.event_gov_cap_modifier = 1.0; g.event_dropout_prob = 0.0
            current_year = int(self.env.now())
            for event in self.events:
                if event['enabled'] and event['start_year'] <= current_year < event['end_year']:
                    level = event['level']
                    if event['type'] == 'public_health':
                        g.event_birth_rate_modifier *= (1 + 0.1 * level); g.event_death_rate_modifier *= (1 - 0.1 * level)
                        g.event_employment_rate_modifier *= (1 + 0.05 * level)
                    elif event['type'] == 'political_stability':
                        g.event_inflation_modifier *= (1 - 0.05 * level); g.event_employment_rate_modifier *= (1 + 0.05 * level)
                        g.event_gov_cap_modifier = 1.5; g.event_income_modifier *= (1 + 0.05 * level)
                        g.event_gov_support_modifier *= (1 + 0.1 * level)
                    elif event['type'] == 'panic':
                        g.event_death_rate_modifier *= (1 + 0.5 * level); g.event_employment_rate_modifier *= (1 - 0.1 * level)
                        g.event_income_modifier *= (1 - 0.1 * level); g.event_dropout_prob = 0.05 * level
                        g.event_inflation_modifier *= (1 + 0.1 * level); g.event_gov_cap_modifier = float('inf')
                        g.event_gov_support_modifier *= (1 + 0.2 * level)
            yield self.hold(1)


class WorldManager(sim.Component):
    def __init__(self, env):
        super().__init__(env=env); self.forecasts = {}
        g.arima_death_rate_modifier = 1.0; g.arima_birth_rate_modifier = 1.0
        g.arima_marriage_rate_modifier = 1.0
        self._train_models()
    def _train_models(self):
        df = pd.DataFrame(HISTORICAL_MACRO_DATA); df.set_index('Year', inplace=True)
        for column in ['Mortality Rate', 'Birth Rate', 'Employment Rate']:
            try:
                model = ARIMA(df[column], order=(1, 1, 1)).fit()
                pred = model.get_forecast(steps=SIMULATION_DURATION + 1)
                self.forecasts[column] = {'mean': pred.predicted_mean,'stderr': pred.se_mean,'base_value': df[column].iloc[-1]}
            except Exception as e: print(f"ARIMA training failed for {column}: {e}")
    def process(self):
        while True:
            yield self.hold(1)
            year = int(self.env.now())
            if year >= len(self.forecasts['Mortality Rate']['mean']): break
            try:
                for rate_name, g_modifier_name in [('Mortality Rate', 'arima_death_rate_modifier'),('Birth Rate', 'arima_birth_rate_modifier'),('Employment Rate', 'arima_marriage_rate_modifier')]:
                    forecast_data = self.forecasts[rate_name]
                    mean = forecast_data['mean'].iloc[year]; stderr = forecast_data['stderr'].iloc[year]
                    stochastic_forecast = np.random.normal(loc=mean, scale=stderr)
                    scaling_factor = stochastic_forecast / forecast_data['base_value'] if forecast_data['base_value'] != 0 else 1
                    setattr(g, g_modifier_name, scaling_factor)
            except Exception as e: print(f"Error in WorldManager process: {e}")

class EconomicManager(sim.Component):
    def __init__(self, env):
        super().__init__(env=env); self.forecasts = {}; self._train_models(); self.update_env_rates(0)
    def _train_models(self):
        df = pd.DataFrame(HISTORICAL_ECONOMIC_DATA); df.set_index('Year', inplace=True)
        for column in ['Top Tax Rate', 'Salary Inflation', 'Cost Inflation (CPI)', '30-Yr Mortgage']:
            try:
                model = ARIMA(df[column], order=(1, 1, 1)).fit()
                pred = model.get_forecast(steps=SIMULATION_DURATION + 1)
                self.forecasts[column] = {'mean': pred.predicted_mean, 'stderr': pred.se_mean}
            except Exception as e: print(f"ARIMA training failed for {column}: {e}")
    def update_env_rates(self, year):
        for rate_name, env_var in [('Top Tax Rate', 'tax_rate'), ('Salary Inflation', 'salary_inflation'), ('Cost Inflation (CPI)', 'cpi_inflation'), ('30-Yr Mortgage', 'mortgage_rate')]:
            forecast_data = self.forecasts[rate_name]; mean = forecast_data['mean'].iloc[year]; stderr = forecast_data['stderr'].iloc[year]
            stochastic_forecast = np.random.normal(loc=mean, scale=stderr); base_rate = stochastic_forecast / 100
            if env_var == 'cpi_inflation': base_rate *= g.event_inflation_modifier
            setattr(self.env, env_var, base_rate)
    def process(self):
        while True:
            yield self.hold(1); year = int(self.env.now())
            if year >= len(self.forecasts['Top Tax Rate']['mean']): break
            try: self.update_env_rates(year)
            except Exception as e: print(f"Error in EconomicManager process: {e}")

class HouseholdFinanceManager(sim.Component):
    def process(self):
        while True:
            yield self.hold(1)
            for hh_id, hh_data in g.HOUSEHOLDS.items():
                members = hh_data.get('members', [])
                if not members: continue
                total_income = sum(p.annual_income for p in members); cpi_multiplier = 1 + self.env.cpi_inflation
                required_cost = compute_household_cost(members, cpi_multiplier); taxes = total_income * self.env.tax_rate
                net_income_minus_cost = (total_income - taxes) - required_cost
                savings = hh_data.get('savings_balance', 0); loans = hh_data.get('loan_balance', 0); loan_repaid = hh_data.get('loan_repaid_cum', 0)
                if net_income_minus_cost > 0:
                    repayment = min(net_income_minus_cost, loans)
                    if repayment > 0: loans -= repayment; loan_repaid += repayment; net_income_minus_cost -= repayment
                    surplus = net_income_minus_cost
                    if g.annual_savings_accepted + surplus <= BANK_SAVINGS_ANNUAL_CAPACITY: g.annual_savings_accepted += surplus; savings += surplus
                    else: g.refused_log['savings'] += 1
                else:
                    deficit = abs(net_income_minus_cost)
                    if g.annual_loans_disbursed + deficit <= BANK_LOAN_ANNUAL_CAPACITY: g.annual_loans_disbursed += deficit; loans += deficit
                    else: g.refused_log['loans'] += 1
                hh_data.update({'total_income': total_income, 'required_cost': required_cost, 'savings_balance': savings, 'loan_balance': loans, 'loan_repaid_cum': loan_repaid, 'taxes_cum': hh_data.get('taxes_cum', 0) + taxes})

class PublicTransitManager(sim.Component):
    def process(self):
        ratio = PUBLIC_TRANSIT_CONFIG['initial_buses'] / PUBLIC_TRANSIT_CONFIG['initial_population']
        while True:
            current_pop = len(g.POPULATION); self.env.bus_fleet_size = int(np.ceil(current_pop * ratio))
            daily_capacity = self.env.bus_fleet_size * PUBLIC_TRANSIT_CONFIG['bus_capacity'] * PUBLIC_TRANSIT_CONFIG['trips_per_bus_per_day']
            self.env.total_bus_capacity = daily_capacity; yield self.hold(1)

class CommuteManager(sim.Component):
    def process(self):
        while True:
            yield self.hold(1)
            bus_demand = sum(1 for p in g.POPULATION if not p.cars and p.commute_purpose in ['Work', 'School'])
            bus_capacity = getattr(self.env, 'total_bus_capacity', 0)
            service_ratio = min(1.0, bus_capacity / bus_demand if bus_demand > 0 else 1.0)
            served_passengers = int(bus_demand * service_ratio)
            self.env.bus_passengers_served = served_passengers; self.env.bus_passengers_refused = bus_demand - served_passengers
            for p in g.POPULATION:
                if not p.cars and p.commute_purpose in ['Work', 'School']: p.use_bus = True if random.random() < service_ratio else False
                else: p.use_bus = False

class GovernmentManager(sim.Component):
    def process(self):
        while True:
            yield self.hold(1)
            current_gov_cap = GOVERNMENT_SPENDING_ANNUAL_CAP * g.event_gov_cap_modifier
            for hh_id, hh_data in g.HOUSEHOLDS.items():
                members = hh_data.get('members', []); adults = [p for p in members if p.age >= 18]; children = [p for p in members if p.age < 18]
                if len(adults) == 1 and len(children) > 0:
                    support_amount = GOV_SUPPORT_CONFIG['single_parent_support'] * g.event_gov_support_modifier
                    if g.annual_gov_support_disbursed + support_amount <= current_gov_cap: g.annual_gov_support_disbursed += support_amount; adults[0].gov_support_cum += support_amount
                    else: g.refused_log['gov_support'] += 1
                if len(children) > 0 and hh_data.get('total_income', 0) > 0 and hh_data.get('total_income', 0) < hh_data.get('required_cost', 0) * GOV_SUPPORT_CONFIG['low_income_threshold_factor']:
                    support_per_adult = (len(children) * GOV_SUPPORT_CONFIG['food_stamp_per_child'] * g.event_gov_support_modifier) / len(adults) if adults else 0
                    for adult in adults:
                        if g.annual_gov_support_disbursed + support_per_adult <= current_gov_cap: g.annual_gov_support_disbursed += support_per_adult; adult.gov_support_cum += support_per_adult
                        else: g.refused_log['gov_support'] += 1

class MarriageManager(sim.Component):
    def __init__(self, env, households, population, marriages):
        super().__init__(env=env); self.households = households; self.population = population; self.marriages = marriages
    def process(self):
        while True:
            yield self.hold(1)
            eligible_males = [p for p in self.population if not p.ispassive() and p.sex == 'Male' and p.age >= 22 and p.marital_status == 'Never married']
            random.shuffle(eligible_males)
            for male in eligible_males:
                marriage_prob = 0.40 * g.arima_marriage_rate_modifier
                if random.random() < marriage_prob:
                    eligible_females = [p for p in self.population if not p.ispassive() and p.sex == 'Female' and p.marital_status == 'Never married' and abs(p.age - male.age) <= 5]
                    if eligible_females:
                        female = random.choice(eligible_females); new_hh_id = g.next_household_id()
                        self.form_new_household(male, female, new_hh_id)
                        male.marital_status = 'Married'; female.marital_status = 'Married'
    def form_new_household(self, person1, person2, new_hh_id):
        male, female = (person1, person2) if person1.sex == 'Male' else (person2, person1)
        male.years_married = 0; female.years_married = 0
        man_former_hh, woman_former_hh = male.household_id, female.household_id
        if man_former_hh in g.HOUSEHOLDS and male in g.HOUSEHOLDS[man_former_hh]['members']: g.HOUSEHOLDS[man_former_hh]['members'].remove(male)
        if woman_former_hh in g.HOUSEHOLDS and female in g.HOUSEHOLDS[woman_former_hh]['members']: g.HOUSEHOLDS[woman_former_hh]['members'].remove(female)
        g.HOUSEHOLDS[new_hh_id] = {'id': new_hh_id, 'type': 'Married-couple family household', 'members': [male, female], 'births': 0, 'deaths': 0, 'marriages': 1}
        male.household_id = new_hh_id; female.household_id = new_hh_id
        marriage_id = f"M_{int(self.env.now())}_{g.next_marriage_id()}"
        g.MARRIAGES.append({'marriage_id': marriage_id, 'man_id': male.id, 'man_former_hh': man_former_hh, 'man_age': male.age, 'woman_id': female.id, 'woman_former_hh': woman_former_hh, 'woman_age': female.age, 'new_hh_id': new_hh_id, 'year_of_marriage': int(self.env.now())})

class TrafficManager(sim.Component):
    def process(self):
        while True:
            yield self.hold(1); car_commuters = sum(len(p.cars) for p in g.POPULATION if not p.ispassive())
            total_wait_time = 0; status = {}
            for road_type, capacity in ROAD_NETWORK_CAPACITY.items():
                load_factor = car_commuters / capacity if capacity > 0 else 0; road_wait_time = 0
                if load_factor < 0.7: status[road_type] = 'Normal'
                elif load_factor < 1.0: status[road_type] = 'Congested'; road_wait_time = (load_factor - 0.7) * 30
                else: status[road_type] = 'Gridlock'; road_wait_time = 9 + (load_factor - 1.0) * 60
                total_wait_time += road_wait_time
            g.ANNUAL_SUMMARY_DATA['traffic_status'] = status; g.ANNUAL_SUMMARY_DATA['avg_wait_time'] = total_wait_time / 3 if len(ROAD_NETWORK_CAPACITY) > 0 else 0
            accident_prob = 0.005
            if status.get('interstate') == 'Gridlock' or status.get('highway') == 'Gridlock': accident_prob = 0.015
            num_accidents = 0
            for p in g.POPULATION:
                if p.cars and random.random() < accident_prob: p.accident_involvement = True; num_accidents += 1
                else: p.accident_involvement = False
            g.ANNUAL_SUMMARY_DATA['num_accidents'] = num_accidents

class ImmigrationManager(sim.Component):
    def process(self):
        while True:
            yield self.hold(1)
            base_immigrants = int(len(g.POPULATION) * IMMIGRATION_CONFIG['base_annual_rate'])
            economic_multiplier = max(0, g.latest_economic_index / 50.0)
            num_to_add = int(base_immigrants * economic_multiplier)
            if num_to_add > 0: print(f"ImmigrationManager: Adding {num_to_add} new agents this year.")
            for _ in range(num_to_add):
                age = random.randint(*IMMIGRATION_CONFIG['age_range'])
                education_levels = list(IMMIGRATION_CONFIG['education_distribution'].keys()); weights = list(IMMIGRATION_CONFIG['education_distribution'].values())
                education = random.choices(education_levels, weights=weights, k=1)[0]
                initial_data = {'id': g.next_person_id(),'age': age,'sex': random.choice(['Male', 'Female']),'education': education,'employment': 'Unemployed','household_id': None,'marital_status': 'Never married'}
                new_person = Person(self.env, initial_data, g.POPULATION)
                new_hh_id = g.next_household_id()
                g.HOUSEHOLDS[new_hh_id] = {'id': new_hh_id, 'type': 'Nonfamily household', 'members': [new_person]}
                new_person.household_id = new_hh_id; new_person.activate()