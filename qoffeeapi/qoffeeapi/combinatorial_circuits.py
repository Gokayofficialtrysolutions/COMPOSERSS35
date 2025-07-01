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

    qc.name = f"Binomial N={num_qubits} p={success_probability_p:.2f}"
    return qc

def generate_permutation_circuit_example(num_qubits: int, pattern: str) -> QuantumCircuit:
    """
    Generates an example permutation circuit using simple gate patterns.
    Args:
        num_qubits: Number of qubits.
        pattern: Name of the pattern (e.g., "SWAP_01", "CYCLE_012", "BIT_REVERSAL_3Q").
    Returns:
        A QuantumCircuit object.
    """
    qc = QuantumCircuit(num_qubits)
    if num_qubits == 2:
        if pattern == "SWAP_01": qc.swap(0, 1); qc.name = "2Q SWAP(0,1)"
        else: raise ValueError(f"Unknown 2-qubit pattern: {pattern}")
    elif num_qubits == 3:
        if pattern == "CYCLE_012": qc.swap(1, 2); qc.swap(0, 1); qc.name = "3Q Cycle (q0->q1->q2)"
        elif pattern == "BIT_REVERSAL_3Q": qc.swap(0, 2); qc.name = "3Q Bit Reversal"
        else: raise ValueError(f"Unknown 3-qubit pattern: {pattern}")
    elif num_qubits == 4:
        if pattern == "PERFECT_SHUFFLE_4Q": qc.swap(1,2); qc.name = "4Q Perfect Shuffle (q1<->q2)"
        elif pattern == "BIT_REVERSAL_4Q": qc.swap(0,3); qc.swap(1,2); qc.name = "4Q Bit Reversal"
        else: raise ValueError(f"Unknown 4-qubit pattern: {pattern}")
    else: raise ValueError(f"Permutation examples by pattern only for 2, 3 or 4 qubits, got {num_qubits}.")
    return qc

def generate_combination_superposition_circuit(num_qubits_n: int, num_to_select_k: int) -> QuantumCircuit:
    """
    Generates a circuit to prepare an equal superposition of all computational basis states
    with Hamming weight k (k ones among N qubits). Uses qc.initialize().
    Args:
        num_qubits_n: Total number of qubits (N).
        num_to_select_k: Number of qubits to be in state |1> (k).
    Returns:
        A QuantumCircuit object.
    """
    if num_to_select_k < 0 or num_to_select_k > num_qubits_n: raise ValueError("k must be between 0 and N.")
    if num_qubits_n <= 0: raise ValueError("N must be positive.")
    from qiskit.quantum_info import Statevector

    target_states_indices = []
    for i in range(2**num_qubits_n):
        if format(i, f'0{num_qubits_n}b').count('1') == num_to_select_k:
            target_states_indices.append(i)

    if not target_states_indices:
        if num_to_select_k == 0:
            qc = QuantumCircuit(num_qubits_n, name=f"Combinations N={num_qubits_n} k=0 (|0...0>)")
            return qc # All zeros is default state
        elif num_to_select_k == num_qubits_n:
            qc = QuantumCircuit(num_qubits_n, name=f"Combinations N={num_qubits_n} k={num_to_select_k} (|1...1>)")
            qc.x(range(num_qubits_n)); return qc
        else: raise ValueError(f"Could not determine target states for N={num_qubits_n}, k={num_to_select_k}")

    num_target_states = len(target_states_indices)
    desired_state_coeffs = np.zeros(2**num_qubits_n, dtype=complex)
    for index in target_states_indices: desired_state_coeffs[index] = 1 / np.sqrt(num_target_states)

    qc = QuantumCircuit(num_qubits_n)
    qc.initialize(Statevector(desired_state_coeffs).data, range(num_qubits_n))
    qc.name = f"Combinations N={num_qubits_n} k={num_to_select_k}"
    return qc

def generate_custom_permutation_circuit(num_qubits: int, permutation_list: list[int]) -> QuantumCircuit:
    """
    Generates a circuit for a specified permutation of computational basis states.
    Args:
        num_qubits: Number of qubits.
        permutation_list: List mapping input basis state indices to output indices.
    Returns:
        A QuantumCircuit object.
    """
    if num_qubits <= 0: raise ValueError("Number of qubits must be positive.")
    dim = 2**num_qubits
    if len(permutation_list) != dim or sorted(permutation_list) != list(range(dim)):
        raise ValueError("Permutation list is invalid for the given number of qubits.")
    from qiskit.circuit.library import Permutation as QiskitPermutationGate
    from qiskit.quantum_info import Operator # For fallback if Permutation gate fails

    qc = QuantumCircuit(num_qubits)
    try:
        permutation_gate = QiskitPermutationGate(num_qubits, permutation_list)
        qc.append(permutation_gate, range(num_qubits))
        qc.name = f"{num_qubits}Q Permutation {str(permutation_list[:4])[:20]}..." # Shortened name
    except Exception as e_perm_gate: # Fallback to generic unitary if Permutation class has issues
        print(f"Warning: Could not use QiskitPermutationGate ({e_perm_gate}). Falling back to generic unitary (less optimal for decomposition).")
        perm_matrix = np.zeros((dim, dim), dtype=int)
        for i, o in enumerate(permutation_list): perm_matrix[o, i] = 1
        qc.unitary(Operator(perm_matrix), range(num_qubits), label=f"{num_qubits}Q CustomPerm")
        qc.name = f"{num_qubits}Q CustomPerm {str(permutation_list[:4])[:20]}..."
    return qc

def generate_w_state_n2_gates() -> QuantumCircuit:
    """
    Generates the 2-qubit W-state analog: (|01> + |10>) / sqrt(2) using elementary gates.
    Qiskit qubit order q1, q0 (q1 is most significant).
    """
    qc = QuantumCircuit(2, name="W_2_state_gates (N=2,k=1)")
    qc.h(0)
    qc.cx(0,1)
    qc.x(0)
    return qc

def generate_w_state_n3_library() -> QuantumCircuit:
    """
    Generates the 3-qubit W-state: (|100> + |010> + |001>) / sqrt(3)
    using Qiskit's WState library function.
    """
    from qiskit.circuit.library import WState
    qc = QuantumCircuit(3, name="W_3_state_lib (N=3,k=1)")
    w3_gate_instance = WState(num_qubits=3)
    qc.append(w3_gate_instance, [0,1,2])
    return qc

def generate_deutsch_jozsa_circuit(num_problem_qubits: int, oracle_type: str = 'balanced_pattern1') -> QuantumCircuit:
    """
    Generates a circuit for the Deutsch-Jozsa algorithm.

    Args:
        num_problem_qubits: The number of qubits for the input register (n).
                            The total number of qubits in the circuit will be n + 1 (for the auxiliary qubit).
        oracle_type: Type of oracle to implement.
                     'constant_zero': f(x) = 0 for all x.
                     'constant_one': f(x) = 1 for all x.
                     'balanced_pattern1': A simple balanced oracle (e.g., CNOTs from input to auxiliary).
                                          For n=1, f(x)=x. For n=2, f(x)=x1 XOR x2.
                     'balanced_pattern2': Another simple balanced oracle.
                                          For n=1, f(x)=NOT x. For n=2, f(x)=x1 XOR (NOT x2).

    Returns:
        A QuantumCircuit object for the Deutsch-Jozsa algorithm.
    """
    if num_problem_qubits < 1:
        raise ValueError("Number of problem qubits (n) must be at least 1.")

    n = num_problem_qubits
    # Total qubits = n (problem) + 1 (auxiliary)
    # Classical bits = n (for measuring problem qubits)
    qc = QuantumCircuit(n + 1, n)
    qc.name = f"Deutsch-Jozsa N={n} {oracle_type}"

    # Auxiliary qubit is q_n (the last one)
    aux_qubit = n

    # 1. Initialize auxiliary qubit to |->
    qc.x(aux_qubit)
    qc.h(aux_qubit)

    # 2. Apply Hadamard to all problem qubits
    qc.h(range(n))
    qc.barrier()

    # 3. Implement the Oracle (U_f)
    if oracle_type == 'constant_zero':
        # f(x) = 0. Oracle is Identity (or simply do nothing to aux_qubit based on input).
        # For clarity, an explicit Identity might be added, but it's often omitted.
        pass # Identity effectively
    elif oracle_type == 'constant_one':
        # f(x) = 1. Oracle flips the auxiliary qubit regardless of input.
        qc.x(aux_qubit)
    elif oracle_type == 'balanced_pattern1':
        # Example: f(x) = x_0 XOR x_1 XOR ... XOR x_{n-1}
        # Implemented by CNOTs from each problem qubit to the auxiliary qubit.
        for i in range(n):
            qc.cx(i, aux_qubit)
    elif oracle_type == 'balanced_pattern2':
        # Example: f(0...0) = 0, f(1...1) = 1, others mixed to be balanced.
        # A simple one for n=1: f(x) = NOT x. Oracle: X(q0) CNOT(q0, aux) X(q0)
        # A simple one for n=2: f(x0,x1) = x0. Oracle: CNOT(q0, aux)
        if n == 1: # f(x) = NOT x
            qc.x(0)
            qc.cx(0, aux_qubit)
            qc.x(0)
        elif n == 2: # f(x0, x1) = x0 (balanced)
            qc.cx(0, aux_qubit)
        else: # Fallback for n > 2 to a generic balanced pattern
             for i in range(n // 2): # Flip based on first half of qubits
                qc.cx(i, aux_qubit)
             if n % 2 == 1 : # if n is odd, ensure it's balanced by one more CNOT
                qc.cx(n-1, aux_qubit)


    else:
        raise ValueError(f"Unknown oracle_type: {oracle_type}")

    qc.barrier()
    # 4. Apply Hadamard to all problem qubits again
    qc.h(range(n))

    # 5. Measure problem qubits
    qc.measure(range(n), range(n))

    return qc

combinatorial_circ_reg = [
    {
        "id": "binomial_n3_p0.5", "name": "Binomial (N=3, p=0.5)", "description": "3 qubits, each with 50% chance of being |1>.",
        "generator": generate_binomial_distribution_circuit, "args": {"num_qubits": 3, "success_probability_p": 0.5}
    },
    {
        "id": "binomial_n4_p0.25", "name": "Binomial (N=4, p=0.25)", "description": "4 qubits, each with 25% chance of being |1>.",
        "generator": generate_binomial_distribution_circuit, "args": {"num_qubits": 4, "success_probability_p": 0.25}
    },
    {
        "id": "binomial_n2_p0.75", "name": "Binomial (N=2, p=0.75)", "description": "2 qubits, each with 75% chance of being |1>.",
        "generator": generate_binomial_distribution_circuit, "args": {"num_qubits": 2, "success_probability_p": 0.75}
    },
    {
        "id": "perm_2q_swap01", "name": "2-Qubit SWAP(0,1)", "description": "Swaps states of qubit 0 and qubit 1.",
        "generator": generate_permutation_circuit_example, "args": {"num_qubits": 2, "pattern": "SWAP_01"}
    },
    {
        "id": "perm_3q_cycle012", "name": "3-Qubit Cycle (0->1->2)", "description": "Cyclic permutation of qubit states q0->q1, q1->q2, q2->q0.",
        "generator": generate_permutation_circuit_example, "args": {"num_qubits": 3, "pattern": "CYCLE_012"}
    },
    {
        "id": "perm_example_3q_bit_reversal", "name": "3Q Permutation (Bit Reversal via SWAPs)", "description": "Reverses qubit order (q0 <-> q2).",
        "generator": generate_permutation_circuit_example, "args": {"num_qubits": 3, "pattern": "BIT_REVERSAL_3Q"}
    },
    {
        "id": "perm_example_4q_perfect_shuffle", "name": "4Q Permutation (Perfect Shuffle q1<->q2)", "description": "Interleaves qubits: q0,q1,q2,q3 -> q0,q2,q1,q3.",
        "generator": generate_permutation_circuit_example, "args": {"num_qubits": 4, "pattern": "PERFECT_SHUFFLE_4Q"}
    },
    {
        "id": "perm_example_4q_bit_reversal", "name": "4Q Permutation (Bit Reversal via SWAPs)", "description": "Reverses qubit order (q0<->q3, q1<->q2).",
        "generator": generate_permutation_circuit_example, "args": {"num_qubits": 4, "pattern": "BIT_REVERSAL_4Q"}
    },
    {
        "id": "comb_n3_k2", "name": "Combinations (N=3, k=2)", "description": "Superposition of states choosing 2 of 3 items.",
        "generator": generate_combination_superposition_circuit, "args": {"num_qubits_n": 3, "num_to_select_k": 2}
    },
    {
        "id": "comb_n4_k1", "name": "Combinations (N=4, k=1)", "description": "Superposition of states choosing 1 of 4 items.",
        "generator": generate_combination_superposition_circuit, "args": {"num_qubits_n": 4, "num_to_select_k": 1}
    },
     {
        "id": "comb_n4_k2", "name": "Combinations (N=4, k=2)", "description": "Superposition of states choosing 2 of 4 items.",
        "generator": generate_combination_superposition_circuit, "args": {"num_qubits_n": 4, "num_to_select_k": 2}
    },
    {
        "id": "comb_n4_k0", "name": "Combinations (N=4, k=0)", "description": "State representing choosing 0 of 4 items (|0000>).",
        "generator": generate_combination_superposition_circuit, "args": {"num_qubits_n": 4, "num_to_select_k": 0}
    },
    {
        "id": "perm_custom_2q_0213", "name": "2Q Permutation ([0,2,1,3])", "description": "Maps |01> to |10> and |10> to |01>.",
        "generator": generate_custom_permutation_circuit, "args": {"num_qubits": 2, "permutation_list": [0, 2, 1, 3]}
    },
    {
        "id": "perm_custom_3q_swap14", "name": "3Q Permutation (Swap |001>,|100>)", "description": "Swaps basis states |001> (1) and |100> (4).",
        "generator": generate_custom_permutation_circuit, "args": {"num_qubits": 3, "permutation_list": [0, 4, 2, 3, 1, 5, 6, 7]}
    },
    {
        "id": "perm_3q_reverse_all", "name": "3Q Permutation (Reverse All Basis States)", "description": "Reverses order of all basis states (e.g., |000>->|111>).",
        "generator": generate_custom_permutation_circuit, "args": {"num_qubits": 3, "permutation_list": [7,6,5,4,3,2,1,0]}
    },
    {
        "id": "w_state_n2_gates", "name": "N=2, k=1 (W-like, Gates)",
        "description": "Gate-based circuit for (|01>+|10>)/√2. (Bell state |Ψ+⟩)",
        "generator": generate_w_state_n2_gates, "args": {}
    },
    {
        "id": "w_state_n3_library", "name": "N=3, k=1 (W-State, Library)",
        "description": "Uses qiskit.circuit.library.WState for (|001>+|010>+|100>)/√3. Decomposable.",
        "generator": generate_w_state_n3_library, "args": {}
    },
    {
        "id": "dj_n1_const0", "name": "Deutsch-Jozsa (n=1, Constant Zero)",
        "description": "Deutsch-Jozsa with 1 problem qubit. Oracle: f(x)=0. Expect '0'.",
        "generator": generate_deutsch_jozsa_circuit, "args": {"num_problem_qubits": 1, "oracle_type": "constant_zero"}
    },
    {
        "id": "dj_n1_const1", "name": "Deutsch-Jozsa (n=1, Constant One)",
        "description": "Deutsch-Jozsa with 1 problem qubit. Oracle: f(x)=1. Expect '0'.",
        "generator": generate_deutsch_jozsa_circuit, "args": {"num_problem_qubits": 1, "oracle_type": "constant_one"}
    },
    {
        "id": "dj_n1_balanced_pattern1", "name": "Deutsch-Jozsa (n=1, Balanced f(x)=x)",
        "description": "Deutsch-Jozsa with 1 problem qubit. Oracle: f(x)=x. Expect '1'.",
        "generator": generate_deutsch_jozsa_circuit, "args": {"num_problem_qubits": 1, "oracle_type": "balanced_pattern1"}
    },
    {
        "id": "dj_n2_balanced_pattern1", "name": "Deutsch-Jozsa (n=2, Balanced f(x0,x1)=x0^x1)",
        "description": "Deutsch-Jozsa with 2 problem qubits. Oracle: f(x0,x1)=x0 XOR x1. Expect '11'.",
        "generator": generate_deutsch_jozsa_circuit, "args": {"num_problem_qubits": 2, "oracle_type": "balanced_pattern1"}
    }
]

if __name__ == '__main__':
    # Test the functions
    print("--- Testing Binomial Circuits ---")
    qc_binom_1 = generate_binomial_distribution_circuit(3, 0.5)
    print(qc_binom_1.draw(output='text'))
    qc_binom_2 = generate_binomial_distribution_circuit(2, 0.75)
    print(qc_binom_2.draw(output='text'))

    print("\n--- Testing Permutation Examples ---")
    qc_perm_1 = generate_permutation_circuit_example(2, "SWAP_01")
    print(qc_perm_1.draw(output='text'))
    qc_perm_2 = generate_permutation_circuit_example(3, "CYCLE_012")
    print(qc_perm_2.draw(output='text'))
    qc_perm_3 = generate_permutation_circuit_example(3, "BIT_REVERSAL_3Q")
    print(qc_perm_3.draw(output='text'))
    qc_perm_4 = generate_permutation_circuit_example(4, "PERFECT_SHUFFLE_4Q")
    print(qc_perm_4.draw(output='text'))
    qc_perm_5 = generate_permutation_circuit_example(4, "BIT_REVERSAL_4Q")
    print(qc_perm_5.draw(output='text'))

    print("\n--- Testing Combination Circuits (Initialize) ---")
    qc_comb_1 = generate_combination_superposition_circuit(3, 2)
    print(qc_comb_1.draw(output='text'))
    qc_comb_2 = generate_combination_superposition_circuit(4, 1)
    print(qc_comb_2.draw(output='text'))

    print("\n--- Testing Custom Permutation Circuits ---")
    perm_list_2q = [0, 2, 1, 3]
    qc_perm_custom_2q = generate_custom_permutation_circuit(2, perm_list_2q)
    print(f"Custom 2Q Permutation {perm_list_2q}:\n{qc_perm_custom_2q.draw(output='text')}")
    perm_list_3q = [0, 4, 2, 3, 1, 5, 6, 7]
    qc_perm_custom_3q = generate_custom_permutation_circuit(3, perm_list_3q)
    print(f"Custom 3Q Permutation {perm_list_3q}:\n{qc_perm_custom_3q.draw(output='text')}")

    print("\n--- Testing W-State Circuits ---")
    qc_w2_gates = generate_w_state_n2_gates()
    print("N=2 W-state analog (Gate-based):\n", qc_w2_gates.draw(output='text'))
    qc_w3_lib = generate_w_state_n3_library()
    print("N=3 W-state Circuit (from Qiskit Library):\n", qc_w3_lib.draw(output='text'))
    try:
        print("Decomposed N=3 W-state Circuit (from Qiskit Library):\n", qc_w3_lib.decompose().draw(output='text'))
    except Exception as e:
        print(f"Could not draw/decompose W3 state: {e}")

    print("\n--- Registry Content ---")
    for entry in combinatorial_circ_reg:
        print(f"- ID: {entry['id']}, Name: {entry['name']}, Gen: {entry['generator'].__name__}")
        # try:
        #     test_qc = entry["generator"](**entry["args"])
        #     print(f"  Generated: {test_qc.name}")
        # except Exception as e_reg:
        #     print(f"  Error generating {entry['id']}: {e_reg}")
