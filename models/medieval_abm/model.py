"""
Medieval Fantasy Battlefield ABM — Mesa 3.x compatible
Two armies: Kingdom vs Horde, each with Knights, Archers, Mages, and a Dragon.
"""

import random
import math
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector


def distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def step_toward(pos, target, grid):
    x, y = pos
    tx, ty = target
    dx = 0 if tx == x else (1 if tx > x else -1)
    dy = 0 if ty == y else (1 if ty > y else -1)
    for c in [(x + dx, y + dy), (x + dx, y), (x, y + dy)]:
        if 0 <= c[0] < grid.width and 0 <= c[1] < grid.height:
            return c
    return pos

def step_away(pos, threat, grid):
    x, y = pos
    tx, ty = threat
    dx = 0 if tx == x else (-1 if tx > x else 1)
    dy = 0 if ty == y else (-1 if ty > y else 1)
    for c in [(x + dx, y + dy), (x + dx, y), (x, y + dy), (x, y)]:
        if 0 <= c[0] < grid.width and 0 <= c[1] < grid.height:
            return c
    return pos


class CombatantAgent(Agent):
    team = None
    max_hp = 100
    damage = 10
    attack_range = 1.5
    armor = 0

    def __init__(self, model, team):
        super().__init__(model)
        self.team = team
        self.hp = self.max_hp
        self.alive = True
        self._damage_bonus = 0.0

    def enemies(self):
        return [a for a in self.model.agents
                if isinstance(a, CombatantAgent) and a.team != self.team and a.alive]

    def nearest_enemy(self):
        foes = self.enemies()
        return min(foes, key=lambda e: distance(self.pos, e.pos)) if foes else None

    def take_damage(self, raw):
        self.hp -= max(1, raw - self.armor)
        if self.hp <= 0:
            self.alive = False

    def effective_damage(self):
        return self.damage * (1 + self._damage_bonus)

    def die(self):
        self.model.grid.remove_agent(self)
        self.remove()

    def move_toward(self, target_pos):
        new_pos = step_toward(self.pos, target_pos, self.model.grid)
        if new_pos != self.pos:
            self.model.grid.move_agent(self, new_pos)

    def move_away(self, threat_pos):
        new_pos = step_away(self.pos, threat_pos, self.model.grid)
        if new_pos != self.pos:
            self.model.grid.move_agent(self, new_pos)


class KnightAgent(CombatantAgent):
    max_hp = 180
    damage = 25
    attack_range = 1.5
    armor = 8
    SHIELD_BLOCK_CHANCE = 0.30

    def __init__(self, model, team):
        super().__init__(model, team)
        self.hp = self.max_hp

    def take_damage(self, raw):
        if random.random() < self.SHIELD_BLOCK_CHANCE:
            raw = raw // 2
        super().take_damage(raw)

    def step(self):
        if not self.alive:
            return
        self._damage_bonus = 0.0
        target = self.nearest_enemy()
        if not target:
            return
        if distance(self.pos, target.pos) <= self.attack_range:
            target.take_damage(self.effective_damage())
        else:
            self.move_toward(target.pos)


class ArcherAgent(CombatantAgent):
    max_hp = 80
    damage = 18
    attack_range = 7.0
    armor = 2
    KITE_THRESHOLD = 2.5

    def __init__(self, model, team):
        super().__init__(model, team)
        self.hp = self.max_hp

    def step(self):
        if not self.alive:
            return
        self._damage_bonus = 0.0
        target = self.nearest_enemy()
        if not target:
            return
        dist = distance(self.pos, target.pos)
        if dist < self.KITE_THRESHOLD:
            self.move_away(target.pos)
        elif dist <= self.attack_range:
            target.take_damage(self.effective_damage())
        else:
            self.move_toward(target.pos)


class MageAgent(CombatantAgent):
    max_hp = 70
    damage = 30
    attack_range = 6.0
    armor = 1
    BLAST_RADIUS = 2.5
    COOLDOWN_TICKS = 4

    def __init__(self, model, team):
        super().__init__(model, team)
        self.hp = self.max_hp
        self._cooldown = 0

    def cast_fireball(self, target_pos):
        for a in list(self.model.agents):
            if (isinstance(a, CombatantAgent) and a.team != self.team
                    and a.alive and distance(a.pos, target_pos) <= self.BLAST_RADIUS):
                a.take_damage(self.effective_damage())
        self._cooldown = self.COOLDOWN_TICKS

    def step(self):
        if not self.alive:
            return
        self._damage_bonus = 0.0
        if self._cooldown > 0:
            self._cooldown -= 1
            target = self.nearest_enemy()
            if target:
                self.move_away(target.pos)
            return
        target = self.nearest_enemy()
        if not target:
            return
        if distance(self.pos, target.pos) <= self.attack_range:
            self.cast_fireball(target.pos)
        else:
            self.move_toward(target.pos)


class DragonAgent(CombatantAgent):
    max_hp = 400
    damage = 50
    attack_range = 4.0
    armor = 12
    BREATH_RADIUS = 3.5
    AURA_RADIUS = 6.0
    AURA_BONUS = 0.20
    BREATH_COOLDOWN = 3

    def __init__(self, model, team):
        super().__init__(model, team)
        self.hp = self.max_hp
        self._breath_cooldown = 0

    def apply_morale_aura(self):
        for a in self.model.agents:
            if (isinstance(a, CombatantAgent) and a.team == self.team
                    and a.alive and a.unique_id != self.unique_id
                    and distance(self.pos, a.pos) <= self.AURA_RADIUS):
                a._damage_bonus = self.AURA_BONUS

    def fire_breath(self, target_pos):
        for a in list(self.model.agents):
            if (isinstance(a, CombatantAgent) and a.team != self.team
                    and a.alive and distance(a.pos, target_pos) <= self.BREATH_RADIUS):
                a.take_damage(self.effective_damage())
        self._breath_cooldown = self.BREATH_COOLDOWN

    def step(self):
        if not self.alive:
            return
        self.apply_morale_aura()
        target = self.nearest_enemy()
        if not target:
            return
        self.move_toward(target.pos)
        dist = distance(self.pos, target.pos)
        if dist <= self.attack_range:
            if self._breath_cooldown == 0:
                self.fire_breath(target.pos)
            else:
                self._breath_cooldown -= 1
                target.take_damage(self.effective_damage() * 0.6)


class BattlefieldModel(Model):
    COMPOSITION = {"knights": 4, "archers": 4, "mages": 3, "dragons": 1}

    def __init__(self, width=40, height=30, seed=42):
        super().__init__(rng=seed)
        self.grid = MultiGrid(width, height, torus=False)
        self.winner = None
        self.tick = 0

        self._spawn_army("kingdom", x_range=(0, width // 2 - 2))
        self._spawn_army("horde",   x_range=(width // 2 + 2, width - 1))

        self.datacollector = DataCollector(
            model_reporters={
                "Kingdom Units": lambda m: self._count("kingdom"),
                "Horde Units":   lambda m: self._count("horde"),
                "Kingdom HP":    lambda m: self._total_hp("kingdom"),
                "Horde HP":      lambda m: self._total_hp("horde"),
                "Winner":        lambda m: m.winner or "ongoing",
            }
        )

    def _place(self, agent, x_range):
        for _ in range(200):
            x = random.randint(*x_range)
            y = random.randint(0, self.grid.height - 1)
            if self.grid.is_cell_empty((x, y)):
                self.grid.place_agent(agent, (x, y))
                return

    def _spawn_army(self, team, x_range):
        cls_map = {
            "knights": KnightAgent, "archers": ArcherAgent,
            "mages": MageAgent,     "dragons": DragonAgent,
        }
        for unit_type, count in self.COMPOSITION.items():
            for _ in range(count):
                agent = cls_map[unit_type](self, team)
                self._place(agent, x_range)

    def _count(self, team):
        return sum(1 for a in self.agents
                   if isinstance(a, CombatantAgent) and a.team == team and a.alive)

    def _total_hp(self, team):
        return sum(a.hp for a in self.agents
                   if isinstance(a, CombatantAgent) and a.team == team and a.alive)

    def _check_winner(self):
        k, h = self._count("kingdom"), self._count("horde")
        if k == 0 and h == 0:
            self.winner = "draw"
        elif k == 0:
            self.winner = "horde"
        elif h == 0:
            self.winner = "kingdom"

    def step(self):
        if self.winner:
            return
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")

        # Remove dead agents
        for a in [a for a in list(self.agents)
                  if isinstance(a, CombatantAgent) and not a.alive]:
            a.die()

        self._check_winner()
        self.tick += 1

    def run(self, max_steps=300):
        while not self.winner and self.tick < max_steps:
            self.step()
        if not self.winner:
            self.winner = ("timeout — kingdom leads"
                           if self._total_hp("kingdom") > self._total_hp("horde")
                           else "timeout — horde leads")
        return self.datacollector.get_model_vars_dataframe()


if __name__ == "__main__":
    model = BattlefieldModel(width=40, height=30, seed=7)
    results = model.run(max_steps=300)

    print("=== Medieval Fantasy Battlefield ABM ===\n")
    print(results.to_string())

    print("\n--- Battle Summary ---")
    print(f"Duration  : {model.tick} ticks")
    print(f"Winner    : {model.winner.upper()}")
    print(f"Kingdom remaining HP : {model._total_hp('kingdom')}")
    print(f"Horde remaining HP   : {model._total_hp('horde')}")

    print("\n--- Survivors ---")
    for team in ("kingdom", "horde"):
        for cls in (KnightAgent, ArcherAgent, MageAgent, DragonAgent):
            survivors = [a for a in model.agents
                         if isinstance(a, cls) and a.team == team and a.alive]
            if survivors:
                avg_hp = sum(a.hp for a in survivors) / len(survivors)
                print(f"  {team.capitalize()} {cls.__name__:<14} x{len(survivors)}  avg HP: {avg_hp:.0f}")