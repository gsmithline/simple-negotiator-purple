# Simple Aspiration Negotiator (Purple Agent)

A simple purple agent for testing the Meta-Game Negotiation Assessor on AgentBeats.

## Strategy

This agent uses an **aspiration-based** negotiation strategy:

- **Proposing**: Aims to keep approximately 85% of total value, prioritizing highest-value items
- **Accepting**: Accepts offers that meet or exceed BATNA, or are within 5% of a reasonable counteroffer

## Usage

### Local Development

```bash
# Install dependencies
uv sync

# Run the agent
python main.py
```

### Docker

```bash
# Build
docker build -t simple-negotiator-purple .

# Run
docker run -p 8080:8080 simple-negotiator-purple
```

## Message Format

### Propose Action
```json
{
  "action": "PROPOSE",
  "quantities": [7, 4, 1],
  "valuations_self": [45, 72, 33],
  "batna_self": 85
}
```

Response:
```json
{
  "allocation_self": [4, 2, 1],
  "allocation_other": [3, 2, 0],
  "reason": "Aspiration-based proposal targeting 85% of total value"
}
```

### Accept/Reject Action
```json
{
  "action": "ACCEPT_OR_REJECT",
  "offer_value": 150,
  "batna_value": 100,
  "counter_value": 160
}
```

Response:
```json
{
  "accept": true,
  "action": "ACCEPT",
  "reason": "Offer value 150 vs BATNA 100 and counter 160"
}
```

## AgentBeats Registration

1. Deploy to a cloud provider (e.g., Google Cloud Run)
2. Register on AgentBeats with your deployment URL
3. Submit to the Meta-Game Negotiation Assessor leaderboard

## License

Apache 2.0
