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

    qc = QuantumCircuit(num_qubits) # Classical bits usually added by user if measuring.

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
            - "SWAP_01" for 2 qubits: applies a SWAP gate between qubit 0 and 1.
            - "CYCLE_012" for 3 qubits: applies SWAP gates to achieve a cyclic permutation of qubit indices (q0->q1, q1->q2, q2->q0).
              This results in a specific permutation of the basis states.

    Returns:
        A QuantumCircuit object.
    """
    qc = QuantumCircuit(num_qubits) # Classical bits are usually added by the user if measuring.

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
    {
        "id": "comb_n3_k2",
        "name": "Combinations (N=3, k=2)",
        "description": "Superposition of states choosing 2 of 3 items (|011>, |101>, |110>).",
        "generator": generate_combination_superposition_circuit,
        "args": {"num_qubits_n": 3, "num_to_select_k": 2}
    },
    {
        "id": "comb_n4_k1",
        "name": "Combinations (N=4, k=1)",
        "description": "Superposition of states choosing 1 of 4 items.",
        "generator": generate_combination_superposition_circuit,
        "args": {"num_qubits_n": 4, "num_to_select_k": 1}
    },
    {
        "id": "comb_n4_k0", # Example for k=0
        "name": "Combinations (N=4, k=0)",
        "description": "State representing choosing 0 of 4 items (|0000>).",
        "generator": generate_combination_superposition_circuit,
        "args": {"num_qubits_n": 4, "num_to_select_k": 0}
    },
    {
        "id": "perm_custom_2q_0213",
        "name": "2Q Permutation ([0,2,1,3])",
        "description": "Maps |01> to |10> and |10> to |01>.",
        "generator": generate_custom_permutation_circuit,
        "args": {"num_qubits": 2, "permutation_list": [0, 2, 1, 3]}
    },
    {
        "id": "perm_custom_3q_swap14",
        "name": "3Q Permutation (Swap |001>,|100>)",
        "description": "Swaps basis states |001> (1) and |100> (4).",
        "generator": generate_custom_permutation_circuit,
        "args": {"num_qubits": 3, "permutation_list": [0, 4, 2, 3, 1, 5, 6, 7]}
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

def generate_combination_superposition_circuit(num_qubits_n: int, num_to_select_k: int) -> QuantumCircuit:
    """
    Generates a circuit that prepares an equal superposition of all computational basis states
    representing the selection of 'k' items from 'N' (where N is num_qubits_n).
    This means states with Hamming weight k.

    Args:
        num_qubits_n: Total number of items/qubits (N).
        num_to_select_k: Number of items/qubits to be in state |1> (k).

    Returns:
        A QuantumCircuit object.
    """
    if num_to_select_k < 0 or num_to_select_k > num_qubits_n:
        raise ValueError("Number to select k must be between 0 and N (num_qubits_n).")
    if num_qubits_n <= 0:
        raise ValueError("Number of qubits N must be positive.")

    from qiskit.quantum_info import Statevector
    from itertools import combinations

    # Determine the target basis states
    target_states_indices = []
    # Iterate through all possible (2^N) states for N qubits
    for i in range(2**num_qubits_n):
        # Convert index to binary string, padded with zeros to length N
        binary_representation = format(i, f'0{num_qubits_n}b')
        # Count number of '1's (Hamming weight)
        if binary_representation.count('1') == num_to_select_k:
            target_states_indices.append(i)

    if not target_states_indices:
        # This case should ideally not happen if k is valid, but as a safeguard
        # or for k=0 on N>0 (target is just |0...0>) or k=N (target is |1...1>)
        # For k=0, target is [0]. For k=N, target is [2^N - 1]
        if num_to_select_k == 0: # State |0...0>
            qc = QuantumCircuit(num_qubits_n)
            # Default state is |0...0>, so do nothing or add Idents for clarity
            qc.name = f"Combinations N={num_qubits_n} k=0 (|0...0>)"
            return qc
        elif num_to_select_k == num_qubits_n: # State |1...1>
            qc = QuantumCircuit(num_qubits_n)
            for q in range(num_qubits_n):
                qc.x(q)
            qc.name = f"Combinations N={num_qubits_n} k={num_to_select_k} (|1...1>)"
            return qc
        else: # Should not be reached if logic for target_states_indices is correct
             raise ValueError(f"Could not determine target states for N={num_qubits_n}, k={num_to_select_k}")


    # Create the desired statevector (equal superposition of target states)
    num_target_states = len(target_states_indices)
    desired_state_coeffs = np.zeros(2**num_qubits_n, dtype=complex)
    for index in target_states_indices:
        desired_state_coeffs[index] = 1 / np.sqrt(num_target_states)

    desired_state = Statevector(desired_state_coeffs)

    qc = QuantumCircuit(num_qubits_n)
    qc.initialize(desired_state.data, range(num_qubits_n))
    qc.name = f"Combinations N={num_qubits_n} k={num_to_select_k}"

    # Note: qc.initialize is a non-unitary operation in terms of gate decomposition.
    # It sets the simulator state. For actual gate-based construction, one would
    # need more complex algorithms, especially for larger N and k.
    # This is acceptable for an educational tool showing the target state.

    return qc

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

    # Test new combination function
    qc_comb_1 = generate_combination_superposition_circuit(3, 2) # 3 choose 2
    print("\nCombinations N=3, k=2 Circuit:")
    print(qc_comb_1.draw(output='text'))
    # Expected state: (|011> + |101> + |110>) / sqrt(3)

    qc_comb_2 = generate_combination_superposition_circuit(4, 1) # 4 choose 1
    print("\nCombinations N=4, k=1 Circuit:")
    print(qc_comb_2.draw(output='text'))
    # Expected state: (|0001> + |0010> + |0100> + |1000>) / sqrt(4)

    qc_comb_0 = generate_combination_superposition_circuit(3,0) # 3 choose 0 -> |000>
    print("\nCombinations N=3, k=0 Circuit:")
    print(qc_comb_0.draw(output='text'))

def generate_custom_permutation_circuit(num_qubits: int, permutation_list: list[int]) -> QuantumCircuit:
    """
    Generates a circuit that applies a specified permutation to the computational basis states.
    The permutation_list maps input basis state indices to output basis state indices.
    E.g., for 2 qubits, permutation_list [0, 2, 1, 3] means:
    |00> (idx 0) -> |00> (idx 0)
    |01> (idx 1) -> |10> (idx 2)
    |10> (idx 2) -> |01> (idx 1)
    |11> (idx 3) -> |11> (idx 3)

    Args:
        num_qubits: Number of qubits.
        permutation_list: A list of length 2**num_qubits, where permutation_list[i] is the
                          output index for input basis state index i. Must be a valid permutation.

    Returns:
        A QuantumCircuit that implements the permutation (possibly using initialize).
    """
    if num_qubits <= 0:
        raise ValueError("Number of qubits must be positive.")

    dim = 2**num_qubits
    if len(permutation_list) != dim:
        raise ValueError(f"Permutation list length must be 2**num_qubits ({dim}), but got {len(permutation_list)}.")
    if sorted(permutation_list) != list(range(dim)):
        raise ValueError("Permutation list must contain all indices from 0 to 2**num_qubits - 1 exactly once.")

    from qiskit.quantum_info import Statevector, Operator
    from qiskit.circuit.library import Permutation as QiskitPermutationGate

    # Create a permutation matrix
    # P_ij = 1 if j is mapped to i, else 0.
    # So, if state |j> maps to state |permutation_list[j]>, the matrix column j should have a 1 at row permutation_list[j].
    # Or, using Qiskit's Permutation gate convention: circuit.permutation([0,2,1,3])
    # This means qubit state index 0 maps to output index 0, input 1 to output 2, input 2 to output 1 etc.

    qc = QuantumCircuit(num_qubits)

    # Qiskit's Permutation gate is a good way to represent this if it's a permutation of basis states.
    # The list provided to Qiskit's Permutation is the new order of the basis states.
    # If our permutation_list[i] = j means input state i goes to output state j,
    # then Qiskit's Permutation wants a list where the value at index j is i from the original state.
    # This is the inverse of the permutation_list if permutation_list maps old_index -> new_index.
    # Let's clarify: Qiskit's Permutation([p_0, p_1, ..., p_{N-1}]) acts as |j> -> |p_j>.
    # So our permutation_list is directly what Qiskit's Permutation gate needs.

    try:
        # Attempt to use Qiskit's built-in Permutation gate, which can decompose for small N
        # or act as a unitary for simulation.
        permutation_gate = QiskitPermutationGate(num_qubits, permutation_list)
        qc.append(permutation_gate, range(num_qubits))
        qc.name = f"{num_qubits}Q Permutation"
    except Exception as e:
        # Fallback for very large permutations or if QiskitPermutationGate has issues
        # This is more of a conceptual fallback as QiskitPermutationGate is quite robust for this.
        print(f"Could not use QiskitPermutationGate directly ({e}), using qc.initialize as a fallback (simulator only).")

        # Create the initial statevector |0...0>
        initial_sv_coeffs = np.zeros(dim, dtype=complex)
        initial_sv_coeffs[0] = 1

        # Create the permuted statevector if we were to apply this to |0...0>
        # This isn't what we want. We want a unitary that *performs* the permutation.
        # The Operator class can take a permutation matrix.

        # Construct permutation matrix P: P|in_idx> = |out_idx>
        # P has P[out_idx, in_idx] = 1
        perm_matrix = np.zeros((dim, dim), dtype=complex)
        for in_idx, out_idx in enumerate(permutation_list):
            perm_matrix[out_idx, in_idx] = 1

        perm_op = Operator(perm_matrix)
        qc.unitary(perm_op, range(num_qubits), label=f"{num_qubits}Q Custom Perm")

    return qc


if __name__ == '__main__':
    # ... (previous tests remain the same) ...

    print("\nRegistry:")
    for entry in combinatorial_circ_reg:
        print(f"- {entry['name']}: calls {entry['generator'].__name__} with {entry['args']}")

    # Test new combination function
    qc_comb_1 = generate_combination_superposition_circuit(3, 2) # 3 choose 2
    print("\nCombinations N=3, k=2 Circuit:")
    print(qc_comb_1.draw(output='text'))

    qc_comb_2 = generate_combination_superposition_circuit(4, 1) # 4 choose 1
    print("\nCombinations N=4, k=1 Circuit:")
    print(qc_comb_2.draw(output='text'))

    qc_comb_0 = generate_combination_superposition_circuit(3,0) # 3 choose 0 -> |000>
    print("\nCombinations N=3, k=0 Circuit:")
    print(qc_comb_0.draw(output='text'))

    # Test custom permutation
    # |00> -> |00> (0->0)
    # |01> -> |10> (1->2)
    # |10> -> |01> (2->1)
    # |11> -> |11> (3->3)
    perm_list_2q = [0, 2, 1, 3]
    qc_perm_custom_2q = generate_custom_permutation_circuit(2, perm_list_2q)
    print(f"\nCustom 2Q Permutation {perm_list_2q}:")
    print(qc_perm_custom_2q.draw(output='text'))

    # For 3 qubits, e.g., |001> (1) <-> |100> (4)
    # 0->0, 1->4, 2->2, 3->3, 4->1, 5->5, 6->6, 7->7
    perm_list_3q = [0, 4, 2, 3, 1, 5, 6, 7]
    qc_perm_custom_3q = generate_custom_permutation_circuit(3, perm_list_3q)
    print(f"\nCustom 3Q Permutation {perm_list_3q}:")
    # Qiskit might decompose this into SWAPs or other gates if possible
    # For text output, it might just show "permutation" or "unitary"
    print(qc_perm_custom_3q.draw(output='text'))
