# Iteration Prompt — Fidelity Refinement

**Source:** `src/main.py` → `main()`, retry loop (lines 100–117)

This prompt is sent to the LLM as a **user message** when the previous circuit's fidelity is below 0.9. It is sent up to 5 times (cycles). All placeholders are filled at runtime.

---

The previous circuit did not achieve high fidelity (`{fidelity_new}`). Generate a new circuit that better matches the target probability distribution, target state vector, and state fidelity.

Previous LLM-generated circuit:
`{circuit_json_new}`

Probability distribution from previous LLM-generated circuit:
`{measurement_probabilities_new}`

State vector from previous LLM-generated circuit:
`{array_to_string(state_llm_new.data)}`

Target probability distribution:
`{measurement_probabilities}`

Target state vector:
`{array_to_string(state.data)}`
