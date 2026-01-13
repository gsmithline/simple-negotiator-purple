"""
Simple aspiration-based negotiator for AgentBeats bargaining evaluation.
"""
from typing import List, Tuple, Dict, Any


class AspirationNegotiator:
    """
    Lightweight aspiration-based negotiator:
    - As proposer: keeps enough items to reach ~85% of total self value
    - As responder: accepts if offer meets BATNA or is within 5% of a plausible counter
    """

    def __init__(self, keep_fraction: float = 0.85, accept_slack: float = 0.05):
        self.keep_fraction = float(max(0.0, min(1.0, keep_fraction)))
        self.accept_slack = float(max(0.0, accept_slack))

    def propose(
        self,
        quantities: Tuple[int, ...],
        valuations_self: List[int],
    ) -> Tuple[List[int], List[int]]:
        """Generate a proposal allocation."""
        total_value = sum(v * q for v, q in zip(valuations_self, quantities))
        target_value = self.keep_fraction * total_value

        # Greedy keep by value density (highest value items first)
        idxs = sorted(range(len(quantities)), key=lambda i: (-valuations_self[i], i))
        keep = [0] * len(quantities)
        acc = 0.0

        for i in idxs:
            if quantities[i] <= 0 or valuations_self[i] <= 0:
                continue
            if acc >= target_value:
                break
            # Keep as many as needed up to available
            need = int(max(0, (target_value - acc) // max(1, valuations_self[i])))
            need = min(need, quantities[i])
            if need == 0 and acc < target_value:
                need = min(1, quantities[i])
            keep[i] = need
            acc += need * valuations_self[i]

        allocation_self = keep
        allocation_other = [quantities[i] - allocation_self[i] for i in range(len(quantities))]
        return allocation_self, allocation_other

    def accepts(self, offer_value: int, batna_value: int, counter_value: int) -> bool:
        """Decide whether to accept an offer."""
        threshold = max(batna_value, int(counter_value * (1.0 - self.accept_slack)))
        return offer_value >= threshold


def handle_negotiation_message(message: str, negotiator: AspirationNegotiator) -> Dict[str, Any]:
    """
    Parse an incoming negotiation message and return an appropriate response.
    """
    import json
    import re

    # Extract JSON from message
    json_match = re.search(r'```json\s*(.*?)```', message, re.DOTALL)
    if json_match:
        observation = json.loads(json_match.group(1))
    else:
        # Try to parse the whole message as JSON
        try:
            observation = json.loads(message)
        except json.JSONDecodeError:
            # Look for JSON object in the message
            json_obj_match = re.search(r'\{[^{}]*\}', message, re.DOTALL)
            if json_obj_match:
                observation = json.loads(json_obj_match.group())
            else:
                return {"error": "Could not parse observation", "action": "WALK"}

    action = observation.get("action", "").upper()
    quantities = observation.get("quantities", [7, 4, 1])
    valuations_self = observation.get("valuations_self", [50, 50, 50])
    batna_self = observation.get("batna_self", 0)

    if action == "PROPOSE":
        allocation_self, allocation_other = negotiator.propose(
            tuple(quantities), valuations_self
        )
        return {
            "allocation_self": allocation_self,
            "allocation_other": allocation_other,
            "reason": f"Aspiration-based proposal targeting {negotiator.keep_fraction*100:.0f}% of total value"
        }

    elif action in ("ACCEPT_OR_REJECT", "ACCEPT"):
        offer_value = observation.get("offer_value", 0)
        batna_value = observation.get("batna_value", batna_self)
        counter_value = observation.get("counter_value", offer_value)

        accept = negotiator.accepts(offer_value, batna_value, counter_value)
        return {
            "accept": accept,
            "action": "ACCEPT" if accept else "COUNTEROFFER",
            "reason": f"Offer value {offer_value} vs BATNA {batna_value} and counter {counter_value}"
        }

    else:
        # Default: make a proposal
        allocation_self, allocation_other = negotiator.propose(
            tuple(quantities), valuations_self
        )
        return {
            "allocation_self": allocation_self,
            "allocation_other": allocation_other,
            "action": "COUNTEROFFER",
            "reason": "Default aspiration-based counteroffer"
        }
