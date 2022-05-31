'''train up'''
import os
from matplotlib.colors import same_color
import torch
import torch.nn.functional as F
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import f1_score
from sklearn.metrics import hamming_loss
from sklearn.metrics import accuracy_score
import logging as log
import numpy
import tqdm
import pickle

from utils import batch_data_to_device


def train(model, loaders, args):
    log.info("training...")
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    for epoch in range(args.n_epochs):
        loss_all = 0
        accurate_cnt_micro = 0.0
        accurate_cnt_hamming_loss = 0.0
        accurate_cnt_exact_match = 0.0
        for step, data in tqdm.tqdm(enumerate(loaders['train'])):
            with torch.no_grad():
                data_subgs, y = batch_data_to_device(data, args.device)
            batch_size = y.shape[0]
            
            model.train()
            optimizer.zero_grad()

            receive_y = model(data_subgs)

            # y_model = None
            loss = 0
            y_model = torch.sigmoid(receive_y)
            loss = F.binary_cross_entropy(y_model, y.float())


            loss.backward()
            optimizer.step()
            step += 1
            

        loss = loss_all / len(loaders['train'].dataset)
        acc = multiLabelEval(model, loaders['test'], args)
        log.info('Epoch: {:03d}, Loss: {:.7f}, acc_micro: {:.7f}, acc_hamming_loss: {:.7f}, acc_exact_match: {:.7f}'.format(epoch, loss, acc[0], acc[1], acc[2]))
        
        if args.save_every > 0 and epoch % args.save_every == 0:
            torch.save(model, os.path.join(args.run_dir, 'params_%i.pt' % epoch))


def multiLabelEval(model, loader, args):
    model.eval()
    predict_list = []
    actual_list = []
    sigmoid = torch.nn.Sigmoid()
    with torch.no_grad():
        for data in loader:
            data_subgs, y = batch_data_to_device(data, args.device)
            y_model = model(data_subgs)
            y_model = sigmoid(y_model)
            y_model = (y_model > 0.5).cpu().numpy()
            range_len = len(y_model)
            for i in range(0, range_len):
                predict_list.append(y_model[i])
                actual_list.append(y.cpu().numpy()[i])
        accurate_cnt_micro = f1_score(numpy.array(predict_list), numpy.array(actual_list), average='micro') 
        accurate_cnt_hamming_loss = hamming_loss(numpy.array(predict_list), numpy.array(actual_list))
        accurate_cnt_exact_match  = accuracy_score(numpy.array(predict_list), numpy.array(actual_list))
    return [accurate_cnt_micro, accurate_cnt_hamming_loss, accurate_cnt_exact_match]


