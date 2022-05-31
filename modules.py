import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn.conv import NNConv, GCNConv

class GNN(nn.Module):
    '''
    Gated Graph Neural Network based on Edge Network
    '''
    def __init__(self, num_step_message_passing, node_hidden_dim, edge_input_dim):
        super().__init__()
        self.num_step_message_passing = num_step_message_passing
        
        self.edge_nets = nn.ModuleList([
            nn.Linear(edge_input_dim, node_hidden_dim * node_hidden_dim, bias=False
            ) for _ in range(num_step_message_passing)
        ])
        self.convs = nn.ModuleList([
            NNConv(node_hidden_dim, node_hidden_dim, self.edge_nets[_], root_weight=False
            ) for _ in range(num_step_message_passing)
        ])
        self.grus = nn.ModuleList([
            nn.GRU(node_hidden_dim, node_hidden_dim
            ) for _ in range(num_step_message_passing)
        ])

    def forward(self, data, out):
        '''
        @params:
            data: batch data
            out: current node hidden states
        @return:
            out: node hidden states after GNN
        '''
        h = out.contiguous().unsqueeze(0)
        for i in range(self.num_step_message_passing):
            out = F.relu(self.convs[i](out, data.edge_index, data.edge_attr))
            out, h = self.grus[i](out.unsqueeze(0), h)
            out = out.squeeze(0)
        return out
    
class Classifier(nn.Module):
    '''
    classifier decoder implemented with mlp
    '''
    def __init__(self, n_layer, hidden_dim, output_dim, dpo):
        super().__init__()

        self.lins = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim)
            for _ in range(n_layer)
        ])
        self.dropout = nn.Dropout(p = dpo)
        self.out = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        for lin in self.lins:
            x = F.relu(lin(x))
        return self.out(self.dropout(x))

class Embedding(nn.Module):
    def __init__(self, input_dim, emb_dim):
        super().__init__()
        
        self.lin = nn.Linear(input_dim, emb_dim, bias=False)
        self.dropout = nn.Dropout()
        
    def forward(self, x):
        return self.dropout(self.lin(x))