# -*- coding: utf-8 -*-
"""quantum.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1HOhTFKTH131R6AGTesHVNE5QPejmvjfd
"""

import torch
import pennylane as qml
import numpy as np

def Rot_layer(gate, w):
    """
    Applies a given rotation gate (e.g., qml.RY or qml.RZ) to each qubit
    with the corresponding parameter in w.
    """
    for idx, element in enumerate(w):
        gate(element, wires=idx)

def entangling_layer(nqubits):
    """
    Applies a ring of CNOT gates to entangle all qubits.
    """
    for i in range(nqubits - 1):
        qml.CNOT(wires=[i, i + 1])
    qml.CNOT(wires=[nqubits - 1, 0])



def quantum_net(n_qubits, q_depth, feature_dim):
    """
    Variational quantum circuit used in the graph convolution layer.
    Uses amplitude encoding to embed a feature vector of length 'feature_dim'
    (which should equal 2^n_qubits) into the quantum state.
    Then applies q_depth layers of parameterized rotations and entangling gates.
    """

    dev = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(dev, interface='torch')
    def quantum_circuit(inputs, q_weights_flat):

        eps = 1e-7
        inputs = inputs + eps
        qml.AmplitudeEmbedding(inputs, wires=range(n_qubits), normalize=True)


        q_weights = q_weights_flat.reshape(q_depth, 2, n_qubits)


        for k in range(q_depth):
            Rot_layer(qml.RY, q_weights[k][0])
            entangling_layer(n_qubits)
            Rot_layer(qml.RZ, q_weights[k][1])


        exp_vals = [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]
        return exp_vals


    num_params = 2 * q_depth * n_qubits

    return qml.qnn.TorchLayer(quantum_circuit, {"q_weights_flat": (num_params,)}), quantum_circuit


def givens_rotation_matrix(theta, i, j, size):
    G = torch.eye(size)
    # Convert theta to a PyTorch tensor
    theta = torch.tensor(theta, dtype=torch.float32)
    c, s = torch.cos(theta/2), torch.sin(theta/2)
    G[i, i], G[i, j] = c, s
    G[j, i], G[j, j] = -s, c
    return G

def quantum_message_passing(features, A_norm):
    batch_size = features.shape[0]  # Get the batch size
    updated_features = features.clone()

    # Iterate over nodes in the batch
    for i in range(batch_size):
        for j in range(batch_size):  # Iterate over all nodes in the graph
            if A_norm[i, j] > 0:  # Check for connection between nodes i and j
                theta = np.pi/2

                # Apply rotation to the features of nodes i and j within the batch
                # Create a 2x2 Givens rotation matrix for the 2 nodes
                G = givens_rotation_matrix(theta, 0, 1, 2)

                # Extract features for nodes i and j
                # Select only the first two features for the rotation
                node_features = torch.stack([updated_features[i][:2], updated_features[j][:2]])

                # Apply rotation and update features
                rotated_features = torch.mv(G, node_features[0])
                # Update only the first two features for node i
                updated_features[i][:2] = rotated_features
    return updated_features