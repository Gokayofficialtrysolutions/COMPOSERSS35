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

    qc = QuantumCircuit(num_qubits)
    theta = 2 * np.arcsin(np.sqrt(success_probability_p))
    for i in range(num_qubits):
        qc.ry(theta, i)
    qc.name = f"Binomial N={num_qubits} p={success_probability_p:.2f}"
    return qc

def generate_permutation_circuit_example(num_qubits: int, pattern: str) -> QuantumCircuit:
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
            return qc
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
    if num_qubits <= 0: raise ValueError("Number of qubits must be positive.")
    dim = 2**num_qubits
    if len(permutation_list) != dim or sorted(permutation_list) != list(range(dim)):
        raise ValueError("Permutation list is invalid for the given number of qubits.")
    from qiskit.circuit.library import Permutation as QiskitPermutationGate
    from qiskit.quantum_info import Operator
    qc = QuantumCircuit(num_qubits)
    try:
        permutation_gate = QiskitPermutationGate(num_qubits, permutation_list)
        qc.append(permutation_gate, range(num_qubits))
        qc.name = f"{num_qubits}Q Permutation {str(permutation_list[:4])[:20]}..."
    except Exception as e_perm_gate:
        print(f"Warning: Could not use QiskitPermutationGate ({e_perm_gate}). Falling back to generic unitary (less optimal for decomposition).")
        perm_matrix = np.zeros((dim, dim), dtype=int)
        for i, o in enumerate(permutation_list): perm_matrix[o, i] = 1
        qc.unitary(Operator(perm_matrix), range(num_qubits), label=f"{num_qubits}Q CustomPerm")
        qc.name = f"{num_qubits}Q CustomPerm {str(permutation_list[:4])[:20]}..."
    return qc

def generate_w_state_n2_gates() -> QuantumCircuit:
    qc = QuantumCircuit(2, name="W_2_state_gates (N=2,k=1)")
    qc.h(0); qc.cx(0,1); qc.x(0)
    return qc

def generate_w_state_n3_library() -> QuantumCircuit:
    from qiskit.circuit.library import WState
    qc = QuantumCircuit(3, name="W_3_state_lib (N=3,k=1)")
    w3_gate_instance = WState(num_qubits=3)
    qc.append(w3_gate_instance, [0,1,2])
    return qc

def generate_deutsch_jozsa_circuit(num_problem_qubits: int, oracle_type: str = 'balanced_pattern1') -> QuantumCircuit:
    if num_problem_qubits < 1: raise ValueError("Number of problem qubits (n) must be at least 1.")
    n = num_problem_qubits
    qc = QuantumCircuit(n + 1, n); qc.name = f"Deutsch-Jozsa N={n} {oracle_type}"
    aux_qubit = n
    qc.x(aux_qubit); qc.h(aux_qubit)
    qc.h(range(n)); qc.barrier()
    if oracle_type == 'constant_zero': pass
    elif oracle_type == 'constant_one': qc.x(aux_qubit)
    elif oracle_type == 'balanced_pattern1':
        for i in range(n): qc.cx(i, aux_qubit)
    elif oracle_type == 'balanced_pattern2':
        if n == 1: qc.x(0); qc.cx(0, aux_qubit); qc.x(0)
        elif n == 2: qc.cx(0, aux_qubit)
        else:
             for i in range(n // 2): qc.cx(i, aux_qubit)
             if n % 2 == 1 : qc.cx(n-1, aux_qubit)
    else: raise ValueError(f"Unknown oracle_type: {oracle_type}")
    qc.barrier(); qc.h(range(n)); qc.measure(range(n), range(n))
    return qc

def generate_grover_search_2_qubit_circuit(marked_element: str) -> QuantumCircuit:
    if not isinstance(marked_element, str) or len(marked_element) != 2 or not all(c in '01' for c in marked_element):
        raise ValueError("Marked element must be a 2-bit string (e.g., '00', '01', '10', '11').")
    qc = QuantumCircuit(2, 2); qc.name = f"Grover 2Q Mark({marked_element})"
    qc.h(0); qc.h(1); qc.barrier()
    if marked_element == "11": qc.cz(0, 1)
    elif marked_element == "01": qc.x(1); qc.cz(0, 1); qc.x(1) # Qiskit q1=0, q0=1
    elif marked_element == "10": qc.x(0); qc.cz(0, 1); qc.x(0) # Qiskit q1=1, q0=0
    elif marked_element == "00": qc.x(0); qc.x(1); qc.cz(0, 1); qc.x(0); qc.x(1)
    qc.barrier()
    qc.h(0); qc.h(1); qc.x(0); qc.x(1); qc.cz(0, 1); qc.x(0); qc.x(1); qc.h(0); qc.h(1)
    qc.barrier(); qc.measure([0,1], [0,1])
    return qc

def _qft_dagger(qc, n_qubits, target_qubits):
    for qubit in range(n_qubits//2):
        qc.swap(target_qubits[qubit], target_qubits[n_qubits-qubit-1])
    for j in range(n_qubits):
        for m in range(j):
            qc.cp(-np.pi/float(2**(j-m)), target_qubits[m], target_qubits[j])
        qc.h(target_qubits[j])

def generate_quantum_counting_example_n3_k1_circuit(counting_qubits: int = 2) -> QuantumCircuit:
    n_problem = 3; t = counting_qubits
    qc = QuantumCircuit(n_problem + t, t); qc.name = f"ConceptualQC_N{n_problem}_t{t}"
    problem_q = list(range(n_problem)); count_q = list(range(n_problem, n_problem + t))
    for qubit_idx in count_q: qc.h(qubit_idx)
    for qubit_idx in problem_q: qc.h(qubit_idx)
    qc.barrier(label="Init")

    oracle_circuit = QuantumCircuit(n_problem, name="Oracle_100_Phase") # Marks |100> (q2=1,q1=0,q0=0)
    oracle_circuit.x(problem_q[0]); oracle_circuit.x(problem_q[1])
    oracle_circuit.h(problem_q[2])
    oracle_circuit.mct([problem_q[0], problem_q[1]], problem_q[2])
    oracle_circuit.h(problem_q[2])
    oracle_circuit.x(problem_q[0]); oracle_circuit.x(problem_q[1])

    diffuser_circuit = QuantumCircuit(n_problem, name="Diffuser_N3")
    for q_idx in problem_q: diffuser_circuit.h(q_idx)
    for q_idx in problem_q: diffuser_circuit.x(q_idx)
    diffuser_circuit.h(problem_q[n_problem-1])
    diffuser_circuit.mct(problem_q[:-1], problem_q[n_problem-1])
    diffuser_circuit.h(problem_q[n_problem-1])
    for q_idx in problem_q: diffuser_circuit.x(q_idx)
    for q_idx in problem_q: diffuser_circuit.h(q_idx)

    grover_gate_def = QuantumCircuit(n_problem, name="GroverOp_100")
    grover_gate_def.append(oracle_circuit, problem_q)
    grover_gate_def.append(diffuser_circuit, problem_q)
    G_gate = grover_gate_def.to_gate()

    for i in range(t):
        control_qubit = count_q[i]
        num_applications = 2**i
        for _ in range(num_applications):
            qc.append(G_gate.control(1), [control_qubit] + problem_q)
    qc.barrier(label="Ctrl-Grover")
    _qft_dagger(qc, t, count_q)
    qc.barrier(label="IQFT")
    qc.measure(count_q, range(t))
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
        "id": "perm_2q_swap01", "name": "2-Qubit SWAP(0,1)", "description": "Swaps states of qubit 0 and qubit 1.",
        "generator": generate_permutation_circuit_example, "args": {"num_qubits": 2, "pattern": "SWAP_01"}
    },
    {
        "id": "perm_3q_cycle012", "name": "3-Qubit Cycle (0->1->2)", "description": "Cyclic permutation of qubit states q0->q1, q1->q2, q2->q0.",
        "generator": generate_permutation_circuit_example, "args": {"num_qubits": 3, "pattern": "CYCLE_012"}
    },
    {
        "id": "comb_n3_k2", "name": "Combinations (N=3, k=2)", "description": "Superposition of states choosing 2 of 3 items.",
        "generator": generate_combination_superposition_circuit, "args": {"num_qubits_n": 3, "num_to_select_k": 2}
    },
    {
        "id": "w_state_n2_gates", "name": "N=2, k=1 (W-like, Gates)",
        "description": "Gate-based circuit for (|01>+|10>)/√2.",
        "generator": generate_w_state_n2_gates, "args": {}
    },
    {
        "id": "w_state_n3_library", "name": "N=3, k=1 (W-State, Library)",
        "description": "Uses qiskit.circuit.library.WState for (|001>+|010>+|100>)/√3.",
        "generator": generate_w_state_n3_library, "args": {}
    },
    {
        "id": "dj_n1_const0", "name": "Deutsch-Jozsa (n=1, Constant Zero)",
        "description": "Deutsch-Jozsa with 1 problem qubit. Oracle: f(x)=0. Expect '0'.",
        "generator": generate_deutsch_jozsa_circuit, "args": {"num_problem_qubits": 1, "oracle_type": "constant_zero"}
    },
    {
        "id": "dj_n1_balanced_pattern1", "name": "Deutsch-Jozsa (n=1, Balanced f(x)=x)",
        "description": "Deutsch-Jozsa with 1 problem qubit. Oracle: f(x)=x. Expect '1'.",
        "generator": generate_deutsch_jozsa_circuit, "args": {"num_problem_qubits": 1, "oracle_type": "balanced_pattern1"}
    },
    {
        "id": "grover_2q_mark11", "name": "Grover's Search (2Q, Mark '11')",
        "description": "Finds the state |11> among 4 states using one Grover iteration.",
        "generator": generate_grover_search_2_qubit_circuit, "args": {"marked_element": "11"}
    },
    {
        "id": "qc_conceptual_n3_t2", "name": "Quantum Counting (Conceptual N=3, t=2)",
        "description": "Conceptual Quantum Counting for N=3 problem qubits, t=2 counting qubits. Oracle marks |100>.",
        "generator": generate_quantum_counting_example_n3_k1_circuit, "args": {"counting_qubits": 2}
    }
]

if __name__ == '__main__':
    print("--- Testing Binomial Circuits ---")
    qc_binom_1 = generate_binomial_distribution_circuit(3, 0.5)
    print(qc_binom_1.draw(output='text'))

    print("\n--- Testing Grover's Search ---")
    qc_grover = generate_grover_search_2_qubit_circuit("11")
    print(qc_grover.draw(output='text'))

    print("\n--- Testing Conceptual Quantum Counting ---")
    qc_qcounting = generate_quantum_counting_example_n3_k1_circuit(2)
    print(qc_qcounting.draw(output='text'))

    print("\n--- Registry Content ---")
    for entry in combinatorial_circ_reg:
        print(f"- ID: {entry['id']}, Name: {entry['name']}")
        try:
            test_qc = entry["generator"](**entry["args"])
            print(f"  Generated: {test_qc.name}, Qubits: {test_qc.num_qubits}")
        except Exception as e_reg:
            print(f"  Error generating {entry['id']}: {e_reg}")
