import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import global_max_pool
from sklearn.decomposition import PCA
import math

import modules


class MVG(nn.Module):
    def __init__(self, args):
        super().__init__()
        self.out = args.output_dim
        self.n_subgs = len(args.subgs)
        self.emb = modules.Embedding(args.node_input_dim, args.node_hidden_dim)
        self.gnn = modules.GNN(
            args.n_step_mp_comp,
            args.node_hidden_dim,
            args.edge_input_dim[-1]
        )

        self.decoder = modules.Classifier(
            args.n_layer_decoder,
            args.node_hidden_dim * self.n_subgs,
            args.output_dim,
            args.dropout
        )

    def forward(self, data_subgs):
        out = []
        for subg in range(self.n_subgs):
            data = data_subgs[subg]
            x = self.emb(data.x)
            x = self.gnn(data, x)
            x = global_max_pool(x, data.batch)
            out.append(x)
        x = torch.cat(out, dim=-1)
        out = self.decoder(x)
        return out
