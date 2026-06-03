# Is Your Quantum Circuit Synthesis Benchmark LLM-Ready?

**Contributors:** Bernhard Schenkenfelder, Patrick Wegerer, Raphael Zefferer, Stefan Klikovits, Manuel Wimmer  
**Published by:** Software Competence Center Hagenberg (SCCH)

---

## Overview

This repository contains the code and data for the paper *"Is Your Quantum Circuit Synthesis Benchmark LLM-Ready?"*, submitted to **QCE26: 2026 IEEE International Conference on Quantum Computing & Engineering** (Metro Toronto Convention Centre, Toronto, Canada, September 13–18, 2026).

The project benchmarks large language models (LLMs) on the task of quantum circuit synthesis — given a target circuit's statevector and measurement probabilities, can an LLM generate an approximating circuit using only explicit quantum gates? Two models were evaluated:

- **GPT-5.5** — called via the official OpenAI API
- **Qwen 3.6** — self-hosted

## Requirements

- Python 3.10+
- Qiskit
- NumPy
- OpenAI Python SDK (for GPT-5.5)

Install dependencies with:

```bash
pip install qiskit numpy openai
```

## Project Structure

```
├── README.md              # This file
├── prompts/               # LLM prompts used in the experiments
│   ├── PROMPT_SYSTEM.md   # Main system prompt (objectives, constraints, JSON schema)
│   └── PROMPT_ITERATION.md # Refinement prompt (sent when fidelity < 0.9)
├── src/                   # Python scripts
│   ├── main.py            # Main experiment runner
│   ├── prompt_helper.py   # Prompt construction and LLM API calls
│   └── plot.py            # Result visualisation
├── data/                  # QASM circuit files used as benchmarks
├── protocols/             # Experimental protocol spreadsheets
└── results/               # LLM output for each benchmark run
    ├── GPT5.5/            # GPT-5.5 results
    │   ├── clifford/      # Clifford circuit results
    │   ├── universal/     # Universal circuit results
    │   ├── qft/           # QFT circuit results
    │   ├── aa5/           # AA5 circuit results
    │   ├── qec_en/        # QEC encoding circuit results
    │   └── qN-qubits/     # Random circuit results grouped by qubit count
    └── Qwen3.6/           # Qwen 3.6 results (same structure)
```

## Usage

1. Place your OpenAI API key in `api_key.txt` in the project root (this file is `.gitignore`d).
2. Edit `src/main.py` to select the target QASM circuit or a random quantum circuit and desired output path.
3. Run the experiment:

```bash
python src/main.py
```

The script generates a random quantum circuit or loads a QASM circuit, computes its statevector and measurement probabilities, sends the data to the LLM via the system prompt in `prompts/PROMPT_SYSTEM.md`, and evaluates the fidelity of the generated circuit. If fidelity is below 0.9, it iterates up to 5 times using the refinement prompt in `prompts/PROMPT_ITERATION.md`.