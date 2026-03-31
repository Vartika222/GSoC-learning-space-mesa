# Medieval Battlefield ABM (Mesa)

## What this model does
This model simulates a battle between two armies (Kingdom vs Horde) on a grid. Each army consists of different unit types — knights, archers, mages, and a dragon — each with distinct behaviors.

The goal was to explore how different agent roles and local decision rules (movement, attack range, abilities) lead to emergent battle outcomes like dominance, attrition, or stalemate.

I chose this model because I wanted to move beyond simple examples and try something that involves multiple interacting behaviors and spatial dynamics.

---

## Mesa features used
- MultiGrid (2D spatial environment)
- Multiple agent classes with different behaviors
- AgentSet (`self.agents.shuffle_do("step")`) for scheduling
- DataCollector for tracking battle metrics (units, HP, winner)

---

## What I learned
- How to structure more complex agent hierarchies (base class + specialized agents)
- How spatial interactions affect outcomes (range, movement, clustering)
- How small behavioral rules (like kiting or cooldowns) significantly impact system dynamics
- The difference between writing code that “works” and designing agent behavior intentionally

---

## What was hard / surprising
- Balancing agent behaviors- small parameter changes made one side dominate completely
- Managing interactions between multiple agent types without making the code messy
- Understanding how to remove agents safely during simulation
- Realizing that emergent behavior is very sensitive to initial placement and rules

---

## What I would do differently
- Add visualization (currently only terminal output)
- Improve balance between unit types (currently not well tuned)
- Introduce terrain or obstacles to make movement more realistic
- Possibly refactor combat logic to be more modular

---

## Potential Mesa improvements (from this model)
- More built-in examples for multi-agent interaction scenarios (not just simple models)
- Better debugging tools for spatial simulations
- Clearer documentation for new AgentSet-based scheduling (Mesa 3.x)

---

## Future scope / extensions

While building this model, I realized it focuses purely on combat and attrition. There are several directions it could be extended:

- **Objective-based gameplay**: Introduce key resources or “power sources” on the grid. Capturing or destroying these could end the simulation, shifting the system from pure combat to strategic control.

- **Morale and threshold effects**: Instead of fighting until elimination, armies could surrender based on conditions (e.g., loss of a certain percentage of high-value units like dragons). This would introduce non-linear outcomes and more realistic dynamics.

- **Hierarchical or administrative agents**: Adding higher-level coordination (e.g., commanders or alliances) could influence group behavior, similar to meta-agents in other Mesa models.

- **Heterogeneous strategies**: Different armies could follow different doctrines (aggressive vs defensive), allowing exploration of how strategy impacts outcomes.

These extensions would move the model from a purely tactical simulation toward a more strategic and system-level one.