#!/usr/bin/env python
# encoding: utf-8

import torch
from torch.utils.data import DataLoader

import os
import pickle
import argparse
import logging as log

import models
import train as train
from dataset import Dataset
import random
import numpy as np

parser = argparse.ArgumentParser(description='Algorithm Detection')
parser.add_argument('--debug',          action='store_true',        help='log debug messages or not')
parser.add_argument('--run_exist',      action='store_true',        help='run dir exists ok or not')
parser.add_argument('--run_dir',        type=str,   default='run/', help='dir to save log and models')
parser.add_argument('--data_dir',       type=str,   default='data112/')
parser.add_argument('--log_every',      type=int,   default=0,      help='number of steps to log loss, do not log if 0')
parser.add_argument('--eval_every',     type=int,   default=0,      help='number of steps to evaluate, only evaluate after each epoch if 0')
parser.add_argument('--save_every',     type=int,   default=2,      help='number of steps to save model')
parser.add_argument('--device',         type=int,   default=-1,      help='gpu device id, cpu if -1')
parser.add_argument('--model',          type=str,   default='MVG')
parser.add_argument('--select_subg',    type=int,   default=0,      help='designate the subgs to do ggnn with comp, 0: ast, 1: rw, 2: dfg, 3: cfg, 4: comp')
parser.add_argument('--n_layer_decoder',type=int,   default=2,      help='number of mlp hidden layers in decoder')
parser.add_argument('--n_compress_layers', type=int, default=2,     help='number of layers for subgraphs dimension reduction')
parser.add_argument('--node_hidden_dim',type=int,   default=80,     help='hidden size for nodes')

parser.add_argument('--sub_node_dim',   type=int, default=64,   help='the node dimension of subgraph')
parser.add_argument('--comp_node_dim',  type=int, default=168,   help='the node dimension of complete graph')

parser.add_argument('--n_step_mp_subg', type=int,   default=2,      help='number of message passing steps for subgraphs (dfg, cfg, ast)')
parser.add_argument('--n_step_mp_comp', type=int,   default=4,      help='number of message passing steps for the complete graph')
parser.add_argument('--n_step_mp_iter', type=int,   default=2,      help='number of message passing iterations btw subgraphs and the complete graph')
parser.add_argument('--n_epochs',       type=int,   default=200,   help='number of epochs to train')
parser.add_argument('--batch_size',     type=int,   default=2,      help='number of instances in a batch')
parser.add_argument('--lr',             type=float, default=1e-4,   help='learning rate')
parser.add_argument('--dropout',        type=float, default=0.5,   help='dropout')

parser.add_argument('--checkpoint_path',     type=str,   default='run/params_10.pt',      help='checkpoint path')
parser.add_argument('--action',     type=str,   default='scatter_vec',  choices=['none', 'label_acc', 'scatter_vec', 'scatter_vec_full', 'continue_run'],    help='checkpoint path')



args = parser.parse_args()

if args.debug:
    args.run_exist = True
    args.run_dir = 'debug'
os.makedirs(args.run_dir, exist_ok=args.run_exist)

log.basicConfig(
    format='%(asctime)s: %(message)s',
    datefmt='%m/%d %I:%M:%S %p', level=log.DEBUG if args.debug else log.INFO)
log.getLogger().addHandler(log.FileHandler(os.path.join(args.run_dir, 'log.txt'), mode='w'))
log.info('args: %s' % str(args))
args.device = 'cpu' if args.device < 0 else 'cuda:%i' % args.device
args.device = torch.device(args.device)

def preprocess():
    datasets = {}
    for split in ['train', 'test']:
        file_name = os.path.join(args.data_dir, 'dataset_%s.pkl' % split)
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                datasets[split] = pickle.load(f)
            log.info('Dataset split %s loaded' % split)
        else:
            datasets[split] = Dataset(root_dir=args.data_dir, split=split)
            with open(file_name, 'wb') as f:
                pickle.dump(datasets[split], f)
            log.info('Dataset split %s created and dumpped' % split)

    setattr(args, 'subgs', datasets['train'].SUBGS)
    setattr(args, 'node_input_dim', datasets['train'].node_input_dim)
    setattr(args, 'edge_input_dim', datasets['train'].edge_input_dim)
    setattr(args, 'output_dim', datasets['train'].output_dim)
    
    loaders = {}
    for split in ['train', 'test']:
        loaders[split] = DataLoader(
            datasets[split],
            batch_size=args.batch_size,
            collate_fn=datasets[split].collate,
            shuffle=True if split == 'train' else False
        )
    return loaders

if __name__ == '__main__':
    loaders = preprocess()
    Model = getattr(models, args.model)
    if  args.action == 'continue_run':
        model = torch.load(args.checkpoint_path, map_location = torch.device(args.device))
        log.info(str(vars(args)))
        log.info(model)
        
        train.train(model, loaders, args)
    else:
        model = Model(args).to(args.device)
        log.info(str(vars(args)))
        log.info(model)
        
        train.train(model, loaders, args)
