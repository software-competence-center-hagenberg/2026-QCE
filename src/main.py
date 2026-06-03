import re
import os
import concurrent.futures
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit
from qiskit.quantum_info import Statevector, state_fidelity

import json

from prompt_helper import PromptHelper


def format_statevector(state) -> str:
    """Format a full statevector without numpy truncation."""
    sv = np.array(state.data)
    return np.array2string(
        sv,
        threshold=np.inf,
        max_line_width=200,
        precision=6,
        separator=", ",
    )


def load_try_configs(file_path: str) -> list[tuple[int, int]]:
    """Load (qubits, depth) pairs from tries.csv.

    Supported formats per line:
    - "<qubits>,<depth>"
    - "<qubits>-qubits-<depth>-depth.txt"
    """
    configs: list[tuple[int, int]] = []

    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if "," in line:
                left, right = [part.strip() for part in line.split(",", 1)]
                configs.append((int(left), int(right)))
                continue

            match = re.search(r"(\d+)-qubits-(\d+)-depth", line)
            if match:
                configs.append((int(match.group(1)), int(match.group(2))))
                continue

            raise ValueError(f"Unsupported tries.csv line format: {line}")

    return configs


def run_single_try(num_qubits: int, depth: int, path: str):
    NUM_QUBITS = num_qubits
    DEPTH = depth

    # Reset file for this run
    with open(path, "w", encoding="utf-8") as _f:
        _f.write("")

    # Generate a random quantum circuit and analyze it
    qc = generate_random_circuit(
        num_qubits=NUM_QUBITS,
        depth=DEPTH,
    )
    print_header("Generated Random Quantum Circuit:", path)

    print_text(qc, path)

    print_circuit_stats(qc, path)
    print_text(f"Number of qubits: {qc.num_qubits}", path)
    print_text(f"Circuit depth: {qc.depth()}", path)

    # Generate the statevector from the circuit
    state = compute_statevector(qc)
    print_header("State Vector:", path)
    print_text(format_statevector(state), path)

    # Compute measurement probabilities
    probabilities = compute_measurement_probabilities(state)
    measurement_probabilities = ""
    print_header("Measurement Probabilities:", path)
    for basis_state, probability in enumerate(probabilities):
        print_text(f"|{basis_state:0{NUM_QUBITS}b}>: {probability:.5f}", path)
        measurement_probabilities += (
            f"  |{basis_state:0{NUM_QUBITS}b}>: {probability:.5f}\\n"
        )

    # Call LLM API to generate a quantum circuit based on the measurement probabilities
    prompt_helper = PromptHelper(num_qubits=NUM_QUBITS, depth=DEPTH)
    circuit_json = prompt_helper.execute_prompt(
        f"Target probability distribution:\n{measurement_probabilities}\n\nTarget state vector:\n{format_statevector(state)}"
    )

    if circuit_json is None:
        raise RuntimeError(
            "LLM returned no response — check API connectivity and context window"
        )

    qc_llm = json_to_quantum_circuit(circuit_json)

    print_text(qc_llm, path)

    print_circuit_stats(qc_llm, path)

    state_llm = compute_statevector(qc_llm)
    print_header("State Vector:", path)
    print_text(format_statevector(state_llm), path)

    probabilities_llm = compute_measurement_probabilities(state_llm)
    measurement_probabilities_llm = ""
    print_header("Measurement Probabilities from LLM-Generated Circuit:", path)
    for basis_state_llm, probability_llm in enumerate(probabilities_llm):
        print_text(f"|{basis_state_llm:0{NUM_QUBITS}b}>: {probability_llm:.5f}", path)
        measurement_probabilities_llm += (
            f"  |{basis_state_llm:0{NUM_QUBITS}b}>: {probability_llm:.5f}\\n"
        )

    # Compute the fidelity between the states
    fidelity = compute_fidelity(state, state_llm)
    print_header("Fidelity of the state with the LLM-generated circuit:", path)
    print_text(f"{fidelity:.4f}", path)

    fidelity_new = fidelity
    state_llm_new = state_llm
    measurement_probabilities_new = measurement_probabilities_llm
    circuit_json_new = circuit_json
    i = 0
    while fidelity_new < 0.9 and i < 5:
        print_header(
            f"Fidelity is below 0.9, regenerating circuit (cycle {i + 1}) ...", path
        )

        prompt = f"""
The previous circuit did not achieve high fidelity ({fidelity_new:.4f}). Generate a new circuit that better matches the target probability distribution, target state vector, and state fidelity.

Previous LLM-generated circuit:
{circuit_json_new}

Probability distribution from previous LLM-generated circuit:
{measurement_probabilities_new}

State vector from previous LLM-generated circuit:
{format_statevector(state_llm_new)}

Target probability distribution:
{measurement_probabilities}

Target state vector:
{format_statevector(state)}
"""

        circuit_json_new = prompt_helper.execute_prompt(prompt)

        if circuit_json_new is None:
            raise RuntimeError(
                "LLM returned no response during retry — check API and context window"
            )

        qc_llm_new = json_to_quantum_circuit(circuit_json_new)

        print_header("Quantum Circuit Generated by LLM:", path)

        print_text(qc_llm_new, path)

        print_circuit_stats(qc_llm_new, path)

        state_llm_new = compute_statevector(qc_llm_new)
        print_header("State Vector from LLM-Generated Circuit:", path)
        print_text(format_statevector(state_llm_new), path)

        probabilities_new = compute_measurement_probabilities(state_llm_new)
        measurement_probabilities_new = ""
        print_header("Measurement Probabilities from LLM-Generated Circuit:", path)
        for basis_state_new, probability_new in enumerate(probabilities_new):
            print_text(
                f"|{basis_state_new:0{NUM_QUBITS}b}>: {probability_new:.5f}", path
            )
            measurement_probabilities_new += (
                f"  |{basis_state_new:0{NUM_QUBITS}b}>: {probability_new:.5f}\\n"
            )

        fidelity_new = compute_fidelity(state, state_llm_new)
        print_header("Fidelity of the state with the new LLM-generated circuit:", path)
        print_text(f"{fidelity_new:.4f}", path)
        i += 1


def main():
    configs = load_try_configs("tries.csv")

    # Process each (Q, D) config sequentially — all 5 tries for a config run in parallel,
    # but we wait for them all to finish before moving to the next config.
    for num_qubits, depth in configs:
        print(f"\n{'='*60}")
        print(f"Starting Q{num_qubits}-qubits-{depth}-depth (5 tries)...")
        print(f"{'='*60}")

        # Build jobs for just this config's 5 tries
        jobs: list[tuple[int, int, str]] = []
        for try_number in range(1, 6):
            path = f"Q{num_qubits}-qubits-{depth}-depth-{try_number}.txt"
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                print(f"  Skipping {path} (already complete)")
                continue
            jobs.append((num_qubits, depth, path))

        if not jobs:
            print(f"  All 5 tries for Q{num_qubits}-D{depth} already complete, skipping.")
            continue

        # Run all 5 tries for this config in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as executor:
            futures = {
                executor.submit(run_single_try, num_qubits, depth, path): path
                for num_qubits, depth, path in jobs
            }
            for future in concurrent.futures.as_completed(futures):
                path = futures[future]
                try:
                    future.result()
                    print(f"Finished {path}")
                except Exception as exc:
                    print(f"Error in {path}: {exc}")

        print(f"Completed Q{num_qubits}-qubits-{depth}-depth, moving to next config...")

def generate_random_circuit(num_qubits, depth):
    """Generates a random quantum circuit."""
    return random_circuit(
        num_qubits=num_qubits, depth=depth, max_operands=2, measure=False
    )


def compute_statevector(circuit: QuantumCircuit) -> Statevector:
    """Computes the statevector from a quantum circuit."""
    return Statevector.from_instruction(circuit)


def compute_measurement_probabilities(statevector: Statevector) -> list:
    """Computes the measurement probabilities from a statevector."""
    return statevector.probabilities()


def compute_fidelity(statevector1: Statevector, statevector2: Statevector) -> float:
    """Computes the fidelity between two statevectors."""
    return state_fidelity(statevector1, statevector2)


def json_to_quantum_circuit(json_string):

    data = json.loads(json_string)

    qc = QuantumCircuit(data["num_qubits"])

    operations = sorted(data["operations"], key=lambda op: op.get("layer", 0))

    current_layer = None

    for op in operations:
        layer = op.get("layer", 0)

        # optional visual layer separation
        # if current_layer is not None and layer != current_layer:
        #     qc.barrier()

        current_layer = layer

        method_name = op["method"].lower()

        if not hasattr(qc, method_name):
            raise ValueError(f"Unsupported gate: {method_name}")

        method = getattr(qc, method_name)
        params = op.get("params", [])
        qubits = op.get("qubits", [])

        # Build the full argument list: numeric params first, then qubits.
        # Qiskit gate methods always take parameters before qubit specifiers.
        # e.g. qc.h(q0), qc.ry(theta, q0), qc.cx(control, target)
        try:
            if method_name in {"mcry", "mcrx", "mcrz", "mcp"}:
                angle = params[0]
                controls = qubits[:-1]
                target = qubits[-1]
                method(angle, controls, target)
            elif method_name in {"mcx"}:
                controls = qubits[:-1]
                target = qubits[-1]
                method(controls, target)
            else:
                method(*params, *qubits)
        except Exception as e:
            print(f"Warning: {method_name}({params}, {qubits}) failed: {e}.")
            print(json.dumps(data, indent=2))
            raise e

    return qc


def print_header(title: str, path: str):
    with open(path, "a", encoding="utf-8") as f:
        print("\n\n", file=f)
        print("---", file=f)
        print(f"{title}", file=f)
        print("---", file=f)
        print("\n", file=f)


def print_text(text, path: str):
    with open(path, "a", encoding="utf-8") as f:
        print(text, file=f)


def print_circuit_stats(qc, path: str):
    num_gates = qc.count_ops()
    total_gates = sum(num_gates.values())
    print_header("Circuit Statistics:", path)
    print_text(f"Total gates: {total_gates}", path)
    print_text(f"Gates: {list(num_gates.items())}", path)

    one_qubit_gates = 0
    two_qubit_gates = 0
    more_quibit_gates = 0

    for instruction in qc.data:
        operation = instruction.operation
        qargs = instruction.qubits

        num_qubits = len(qargs)

        if num_qubits == 1:
            one_qubit_gates += 1

        elif num_qubits == 2:
            two_qubit_gates += 1
        else:
            more_quibit_gates += 1

    print_text(f"1-qubit gates: {one_qubit_gates}", path)
    print_text(f"2-qubit gates: {two_qubit_gates}", path)
    print_text(f"n-qubit gates: {more_quibit_gates}", path)


if __name__ == "__main__":
    main()
