# mastercode02_setup.py
import salabim as sim, random
from mastercode02_config_and_rates import EMPLOYERS, EMPLOYER_PROBS, EDUCATION_CAPACITIES
from mastercode02_agents import Person
import mastercode02_globals as g
from mastercode02_generator import generate_initial_population, DATA

class Initializer(sim.Component):
    def __init__(self, env):
        super().__init__(env=env)

    def process(self):
        print("\n--- RUNNING MASTERCODE02 INITIALIZER ---\n")

        g.POPULATION.clear(); g.HOUSEHOLDS.clear()
        generated_agents_data = generate_initial_population()
        for agent_data in generated_agents_data:
            initial_data = {'id': g.next_person_id(),'age': agent_data.age,'sex': agent_data.sex,'education': agent_data.education,'employment': agent_data.employment,'household_id': None,'marital_status': agent_data.marital_status}
            Person(self.env, initial_data, g.POPULATION)

        for hh_type, count in DATA['households'].items():
            for _ in range(count):
                hh_id = g.next_household_id()
                g.HOUSEHOLDS[hh_id] = {'id': hh_id, 'type': hh_type, 'members': []}

        unplaced_agents = list(g.POPULATION)
        random.shuffle(unplaced_agents)
        for person in unplaced_agents:
            target_hh_id = random.choice(list(g.HOUSEHOLDS.keys()))
            person.household_id = target_hh_id
            g.HOUSEHOLDS[target_hh_id]['members'].append(person)

        for name, capacity in EDUCATION_CAPACITIES.items(): g.EDUCATION_RESOURCE[name] = sim.Resource(name, capacity=capacity, env=self.env)
        for emp_id, emp_data in EMPLOYERS.items(): g.EMPLOYER_RESOURCE[emp_id] = sim.Resource(emp_data['name'], capacity=emp_data['capacity'], env=self.env)

        print("Initializer: Pre-assigning initial employers and income...")
        employer_ids = list(EMPLOYERS.keys())
        for person in g.POPULATION:
            if person.employment_status == 'Employed':
                chosen_employer_id = random.choices(employer_ids, weights=EMPLOYER_PROBS, k=1)[0]
                person.employer = chosen_employer_id
                person._assign_skill_and_income()

        print("Initializer: Initial state setup is complete.")

        for person in g.POPULATION:
            person.activate()

        print(f"\nSUCCESS: Initialized and activated {len(g.POPULATION)} people in {len(g.HOUSEHOLDS)} households.")
        yield self.hold(0)