import numpy as np
from qiskit import QuantumCircuit

def generate_binomial_distribution_circuit(num_qubits: int, success_probability_p: float) -> QuantumCircuit:
    """
    Generates a quantum circuit where measuring qubits in the computational basis
    yields statistics approximating a binomial distribution.
    Each qubit represents an independent trial.
    The probability of measuring |1> (success) for each qubit is success_probability_p.

    Args:
        num_qubits: The number of qubits, representing the number of trials (n).
        success_probability_p: The probability of success (measuring |1>) for each trial (p).

    Returns:
        A QuantumCircuit object.
    """
    if not (0 <= success_probability_p <= 1):
        raise ValueError("Success probability p must be between 0 and 1.")
    if num_qubits <= 0:
        raise ValueError("Number of qubits must be positive.")

    qc = QuantumCircuit(num_qubits, num_qubits) # Add classical bits for measurement

    # Angle for Ry gate to achieve desired probability for |1>
    # P(|1>) = sin^2(theta/2) = success_probability_p
    # theta = 2 * arcsin(sqrt(success_probability_p))
    theta = 2 * np.arcsin(np.sqrt(success_probability_p))

    for i in range(num_qubits):
        qc.ry(theta, i)

    # qc.measure_all() # Optional: Can add measurement if circuit is to be run directly
                       # Or leave it to the execution context to add measurements.
                       # For library functions, usually better not to add measure_all.
    qc.name = f"Binomial N={num_qubits} p={success_probability_p:.2f}"
    return qc

def generate_permutation_circuit_example(num_qubits: int, pattern: str) -> QuantumCircuit:
    """
    Generates an example permutation circuit.
    For now, simple patterns for 2 or 3 qubits.

    Args:
        num_qubits: Number of qubits (2 or 3 for current examples).
        pattern:
            - "SWAP_01" for 2 qubits: swaps |01> and |10> (achieved by SWAP gate).
            - "CYCLE_3Q_001_010_100" for 3 qubits: attempts |001> -> |010> -> |100> -> |001>
              (This is non-trivial with simple gates and might need decomposition or be illustrative)
              For simplicity, a basic SWAP network example.

    Returns:
        A QuantumCircuit object.
    """
    qc = QuantumCircuit(num_qubits, num_qubits)

    if num_qubits == 2:
        if pattern == "SWAP_01": # This is just a SWAP gate
            qc.swap(0, 1)
            qc.name = "2Q SWAP(0,1)"
        else:
            raise ValueError(f"Unknown 2-qubit pattern: {pattern}")
    elif num_qubits == 3:
        if pattern == "CYCLE_012": # Swaps q0->q1, q1->q2, q2->q0
            qc.swap(1, 2) # q0,q2,q1
            qc.swap(0, 1) # q2,q0,q1
            qc.name = "3Q Cycle (0->1->2)"
        else:
            raise ValueError(f"Unknown 3-qubit pattern: {pattern}")
    else:
        raise ValueError(f"Permutation examples only implemented for 2 or 3 qubits currently, got {num_qubits}.")

    return qc

# Registry for these circuits
# Each entry:
#   id: unique identifier
#   name: User-friendly name
#   description: Short description
#   generator: function to call
#   params: list of dicts, each defining a parameter for the UI if we had dynamic inputs
#           or specific values for pre-defined examples.
#           For pre-defined, params could be the direct args for the generator.

# For Phase 1, params will be the direct args for pre-defined examples.
combinatorial_circ_reg = [
    {
        "id": "binomial_n3_p0.5",
        "name": "Binomial (N=3, p=0.5)",
        "description": "3 qubits, each with 50% chance of being |1>.",
        "generator": generate_binomial_distribution_circuit,
        "args": {"num_qubits": 3, "success_probability_p": 0.5}
    },
    {
        "id": "binomial_n4_p0.25",
        "name": "Binomial (N=4, p=0.25)",
        "description": "4 qubits, each with 25% chance of being |1>.",
        "generator": generate_binomial_distribution_circuit,
        "args": {"num_qubits": 4, "success_probability_p": 0.25}
    },
    {
        "id": "perm_2q_swap01",
        "name": "2-Qubit SWAP(0,1)",
        "description": "Swaps states of qubit 0 and qubit 1.",
        "generator": generate_permutation_circuit_example,
        "args": {"num_qubits": 2, "pattern": "SWAP_01"}
    },
    {
        "id": "perm_3q_cycle012",
        "name": "3-Qubit Cycle (0->1->2)",
        "description": "Cyclic permutation of qubit states q0->q1, q1->q2, q2->q0.",
        "generator": generate_permutation_circuit_example,
        "args": {"num_qubits": 3, "pattern": "CYCLE_012"}
    },
]

if __name__ == '__main__':
    # Test the functions
    qc_binom_1 = generate_binomial_distribution_circuit(3, 0.5)
    print("Binomial N=3, p=0.5 Circuit:")
    print(qc_binom_1.draw(output='text'))

    qc_binom_2 = generate_binomial_distribution_circuit(4, 0.25)
    print("\nBinomial N=4, p=0.25 Circuit:")
    print(qc_binom_2.draw(output='text'))

    qc_perm_1 = generate_permutation_circuit_example(2, "SWAP_01")
    print("\n2-Qubit SWAP(0,1) Circuit:")
    print(qc_perm_1.draw(output='text'))

    qc_perm_2 = generate_permutation_circuit_example(3, "CYCLE_012")
    print("\n3-Qubit Cycle (0->1->2) Circuit:")
    print(qc_perm_2.draw(output='text'))

    print("\nRegistry:")
    for entry in combinatorial_circ_reg:
        print(f"- {entry['name']}: calls {entry['generator'].__name__} with {entry['args']}")
        # Test generation from registry
        # test_qc = entry["generator"](**entry["args"])
        # print(test_qc.draw(output='text'))
