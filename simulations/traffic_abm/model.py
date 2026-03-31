"""
Simple Traffic ABM — Cars move right on a grid, stopping for red lights and other cars.
- TrafficLightAgent: Toggles between green and red every few steps.
- CarAgent: Moves right if the next cell is clear and the light is green; otherwise waits.
- TrafficModel: Initializes a grid with traffic lights and cars, collects data on waiting cars, moving cars, and average distance traveled.
"""

import random
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector


class TrafficLightAgent(Agent):
    def __init__(self, model, cycle=6):
        super().__init__(model)
        self.cycle = cycle
        self.green = True
        self._timer = cycle

    def step(self):
        self._timer -= 1
        if self._timer <= 0:
            self.green = not self.green
            self._timer = self.cycle


class CarAgent(Agent):
    def __init__(self, model, speed=1):
        super().__init__(model)
        self.speed = speed
        self.waiting = False
        self.distance = 0

    def _next_cell(self):
        x, y = self.pos
        next_x = (x + 1) % self.model.grid.width
        return (next_x, y)

    def _cell_blocked(self, cell):
        return any(isinstance(a, CarAgent)
                   for a in self.model.grid.get_cell_list_contents([cell]))

    def _red_light_ahead(self, cell):
        return any(isinstance(a, TrafficLightAgent) and not a.green
                   for a in self.model.grid.get_cell_list_contents([cell]))

    def step(self):
        self.waiting = False
        for _ in range(self.speed):
            target = self._next_cell()
            if self._cell_blocked(target) or self._red_light_ahead(target):
                self.waiting = True
                break
            self.model.grid.move_agent(self, target)
            self.distance += 1


class TrafficModel(Model):
    def __init__(self, width=20, height=5, n_cars=10, n_lights=4, light_cycle=6, seed=42):
        super().__init__(rng=seed)
        self.grid = MultiGrid(width, height, torus=True)

        light_cols = [int((i + 1) * width / (n_lights + 1)) for i in range(n_lights)]
        for col in light_cols:
            for row in range(height):
                light = TrafficLightAgent(self, cycle=light_cycle)
                self.grid.place_agent(light, (col, row))

        placed = 0
        attempts = 0
        while placed < n_cars and attempts < 1000:
            row = placed % height
            col = random.randint(0, width - 1)
            if not any(isinstance(a, (CarAgent, TrafficLightAgent))
                       for a in self.grid.get_cell_list_contents([(col, row)])):
                speed = random.choice([1, 1, 2])
                car = CarAgent(self, speed=speed)
                self.grid.place_agent(car, (col, row))
                placed += 1
            attempts += 1

        self.datacollector = DataCollector(
            model_reporters={
                "Waiting Cars": lambda m: sum(
                    1 for a in m.agents if isinstance(a, CarAgent) and a.waiting
                ),
                "Moving Cars": lambda m: sum(
                    1 for a in m.agents if isinstance(a, CarAgent) and not a.waiting
                ),
                "Avg Distance": lambda m: (
                    lambda cars: sum(c.distance for c in cars) / len(cars) if cars else 0
                )([a for a in m.agents if isinstance(a, CarAgent)]),
            }
        )

    def step(self):
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")

    def run(self, n_steps=50):
        for _ in range(n_steps):
            self.step()
        return self.datacollector.get_model_vars_dataframe()


if __name__ == "__main__":
    model = TrafficModel(width=20, height=5, n_cars=10, n_lights=4, light_cycle=6)
    results = model.run(n_steps=50)
    print("=== Traffic ABM — 50 ticks ===\n")
    print(results.to_string())
    print(f"\nPeak waiting cars : {results['Waiting Cars'].max()}")
    print(f"Avg distance/car  : {results['Avg Distance'].iloc[-1]:.1f} cells")
    print(f"Congestion rate   : {results['Waiting Cars'].mean():.1f} cars waiting on average")
