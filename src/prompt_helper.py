from openai import OpenAI

class PromptHelper:
    def __init__(self, num_qubits: int, depth: int):
        """ Initialize the PromptHelper class """
        with open("api_key.txt", "r", encoding="utf-8") as f:
            API_KEY = f.read().strip()

        self.client = OpenAI(
            api_key=API_KEY,
        )
        self.num_qubits = num_qubits
        self.depth = depth

        prompt = self.build_prompt()

        # print("\nConstructed Prompt:\n")
        # print(prompt)

        self.messages = [
            {
                "role": "system",
                "content": f'''

{prompt}

''',
            }
        ]

    def build_prompt(self) -> str:
        return (
            "You are an expert in quantum circuit design. "
            "Generate a quantum circuit JSON structure that approximates the original quantum circuit.\n\n"

            "Objectives:\n"
            "1. Match the target probability distribution over computational basis states.\n"
            "2. Reproduce the target quantum state vector as closely as possible, "
            "including amplitudes and relative phases.\n"
            "3. Maximize state fidelity to the original circuit state. "
            "The generated circuit should have high fidelity when evaluated with "
            "qiskit.quantum_info.state_fidelity().\n\n"

            "Constraints:\n"
            f"- Qubits: {self.num_qubits}\n"
            f"- Layers/Depth: {self.depth}\n"
            "- No classical bits.\n"
            "- Use only Qiskit QuantumCircuit gate method names.\n\n"

            "Output format:\n"
            "- Return ONLY valid JSON.\n"
            "- Use the schema shown in the following examples.\n"
            "\nBell state example:\n"
"""{
  "num_qubits": 2,
  "depth": 2,
  "operations": [
    {
      "layer": 0,
      "method": "h",
      "qubits": [0]
    },
    {
      "layer": 1,
      "method": "cx",
      "qubits": [0, 1]
    }
  ]
}
"""

        "\nParameterized gate example:\n"
"""{
  "num_qubits": 1,
  "depth": 1,
  "operations": [
    {
      "layer": 0,
      "method": "ry",
      "params": [1.5708],
      "qubits": [0]
    }
  ]
}
"""

        "\nRules:\n"
        "- Every operation must include: layer, method, qubits.\n"
        "- Include params only when the gate requires parameters.\n"
        "- layer must be an integer from 0 to depth - 1.\n"
        "- qubits must use zero-based indices.\n"
        "- Multi-qubit gate qubits must be ordered according to Qiskit convention, "
        "for example cx uses [control, target].\n"
        "- Prefer circuits that reproduce amplitudes and relative phases, not only probabilities.\n"
        "- Do not add measurements.\n"
        "- Do not use ucrx, ucry, ucrz, isometry, diagonal, initialize, prepare_state, set_statevector, or any direct state-preparation shortcuts.\n"
        "- Construct the quantum state only using explicit quantum gates.\n"
        "- Do not include comments, markdown, or explanations.\n\n"
    )

    def execute_prompt(self, prompt: str) -> str:
        self.messages.append(
            {
                "role": "user",
                "content": f"{prompt}"
            }
        )

        # print(json.dumps(self.messages, indent=2))

        try:    
            response = self.client.responses.create(
                model="gpt-5.5",
                input=self.messages
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

        # print("\nRaw Response:\n")
        # print(response.output_text)

        return response.output_text


        

        
