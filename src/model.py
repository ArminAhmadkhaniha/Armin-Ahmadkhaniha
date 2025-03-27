# -*- coding: utf-8 -*-
"""model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/10wtYVSb285zs1Pzc3zuc1VcvpudNH7DQ
"""

from quantum import quantum_net, quantum_message_passing
import torch



class QuantumGCN(torch.nn.Module):
    def __init__(self, n_qubits, n_classes=2):
        """
        Initializes the QuantumGCN model.
        Args:
            n_qubits (int): Number of qubits in the quantum circuit.
            n_classes (int): Number of output classes.
        """
        super().__init__()
        self.q_feature = quantum_net(n_qubits, 1, 256)[0]
        self.fc = torch.nn.Linear(n_qubits, n_classes)

    def forward(self, x, A_norm):
        x = self.q_feature(x)
        x = quantum_message_passing(x, A_norm)
        return self.fc(x)