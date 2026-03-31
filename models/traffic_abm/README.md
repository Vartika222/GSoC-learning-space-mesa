# Traffic ABM (Mesa)

## What this model does
This model simulates traffic flow on a grid using cars and traffic lights. Cars move forward unless blocked by another car or a red light, leading to congestion patterns.

## Mesa features used
- MultiGrid (spatial environment)
- Agent-based movement (CarAgent, TrafficLightAgent)
- DataCollector for tracking traffic metrics

## What I learned
- How simple local rules can create emergent behavior like traffic jams
- How to structure agent vs model logic in Mesa

## Challenges
- Handling movement conflicts (blocked cells, red lights)
- Tuning parameters like traffic light cycles to observe different outcomes