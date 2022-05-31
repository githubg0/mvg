import os
import torch
import torch.nn.functional as F
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import f1_score
from sklearn.metrics import hamming_loss
from sklearn.metrics import accuracy_score
import logging as log
import numpy
import tqdm

from utils import batch_data_to_device

def train(model, loaders, args):
    log.info("training...")
    # optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, betas = (0.5,  0.999))
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    for epoch in range(args.n_epochs):
        loss_all = 0
        accurate_cnt_micro = 0.0
        accurate_cnt_hamming_loss = 0.0
        accurate_cnt_exact_match = 0.0
        # print(len(loaders['train']))
        # print(len(loaders['valid']))
        for step, data in tqdm.tqdm(enumerate(loaders['train'])):
            with torch.no_grad():
                data_subgs, y = batch_data_to_device(data, args.device)
            # print(len(data_subgs[0]), 'dddd')
            # print(data_subgs, 'gggg')
            # print(y)
            # for it in data_subgs:
            #     print(it)
            # print('ggggggggg')
            
            batch_size = y.shape[0]
            
            model.train()
            optimizer.zero_grad()

            receive_y = model(data_subgs)

            y_model = None
            loss = 0
            if receive_y[0] == 0:
                y_model = torch.sigmoid(receive_y[1])
                loss = F.binary_cross_entropy(y_model, y.float())
            else:
                y_model = torch.sigmoid(receive_y[1])
                loss = F.binary_cross_entropy(y_model, y.float()) + receive_y[2]

            # y_model = torch.sigmoid(model(data_subgs))
            # loss = F.binary_cross_entropy(y_model, y.float())
            loss.backward()
            optimizer.step()
            step += 1
            
            with torch.no_grad():
                loss_all += loss.item() * batch_size
                y_model = (y_model > 0.5).cpu().numpy()
                y_true = y.cpu().numpy()
                accurate_cnt_micro += f1_score(y_model, y_true, average='micro')
                accurate_cnt_hamming_loss += hamming_loss(y_model, y_true)
                accurate_cnt_exact_match += accuracy_score(y_model, y_true)
            
                if args.log_every > 0 and step % args.log_every == 0:
                    loss = loss_all / step / loaders['train'].batch_size
                    acc = [1.0 * accurate_cnt_micro / step / loaders['train'].batch_size,
                           1.0 * accurate_cnt_hamming_loss / step / loaders['train'].batch_size,
                           1.0 * accurate_cnt_exact_match / step / loaders['train'].batch_size]
                    log.info('\ttrain Step: {:03d}k, Loss: {:.7f}, acc_micro: {:.7f}, acc_hamming_loss: {:.7f}, acc_exact_match: {:.7f}'.format(step // 1000, loss, acc[0],acc[1],acc[2]))
                if args.eval_every > 0 and step % args.eval_every == 0:
                    acc = multiLabelEval(model, loaders['valid'], args)
                    log.info('\teval Step: {:03d}k, acc_micro: {:.7f}, acc_hamming_loss: {:.7f}, acc_exact_match: {:.7f}'.format(step // 1000, acc[0], acc[1], acc[2]))
                
        loss = loss_all / len(loaders['train'].dataset)
        acc = multiLabelEval(model, loaders['valid'], args)
        log.info('Epoch: {:03d}, Loss: {:.7f}, acc_micro: {:.7f}, acc_hamming_loss: {:.7f}, acc_exact_match: {:.7f}'.format(epoch, loss, acc[0], acc[1], acc[2]))
        
        if args.save_every > 0 and epoch % args.save_every == 0:
            torch.save(model, os.path.join(args.run_dir, 'params_%i.pt' % epoch))


# single label evaluation
def evaluate(model, loader, args):
    model.eval()
    accurate_cnt = 0
    with torch.no_grad():
        for data in loader:
            data_subgs, y = batch_data_to_device(data, args.device)
            y_model = model(data_subgs)
            y_model = y_model.argmax(dim=-1)
            accurate_cnt += y_model.eq(y).sum().item()
    return accurate_cnt / len(loader.dataset)

# multi-label evaluation
def multiLabelEval(model, loader, args):
    model.eval()
    #  = 0.0
    # accurate_cnt_hamming_loss = 0.0
    # accurate_cnt_exact_match = 0.0
    # print(len(loader))
    predict_list = []
    actual_list = []
    with torch.no_grad():
        for data in loader:
            data_subgs, y = batch_data_to_device(data, args.device)
            # y_model = model(data_subgs)
            y_model = model(data_subgs)[1]
            y_model = (y_model > 0.5).cpu().numpy()
            range_len = len(y_model)
            for i in range(0, range_len):
                predict_list.append(y_model[i])
                actual_list.append(y.cpu().numpy()[i])
            # predict_list.append(y_model[0])
            # actual_list.append(y.cpu().numpy()[0])
            # print(len(y_model), len(y.cpu().numpy()))
            # predict_list += y_model[0]
            # actual_list += y.cpu().numpy()[0]
            
            # print('*******', predict_list, '*******')
            # print('#######', actual_list, '########')
            # accurate_cnt_micro += f1_score(y_model, y.cpu().numpy(), average='micro')
            # accurate_cnt_hamming_loss += hamming_loss(y_model, y.cpu().numpy())
            # accurate_cnt_exact_match += accuracy_score(y_model, y.cpu().numpy())
        # print('******', len(actual_list), '******')
        # print('predict:', len(predict_list), 'actual:',len(actual_list))
        accurate_cnt_micro = f1_score(numpy.array(predict_list), numpy.array(actual_list), average='micro') 
        accurate_cnt_hamming_loss = hamming_loss(numpy.array(predict_list), numpy.array(actual_list))
        accurate_cnt_exact_match  = accuracy_score(numpy.array(predict_list), numpy.array(actual_list))
    return [accurate_cnt_micro, accurate_cnt_hamming_loss, accurate_cnt_exact_match]
    # return [accurate_cnt_micro / len(loader.dataset), accurate_cnt_hamming_loss / len(loader.dataset), accurate_cnt_exact_match / len(loader.dataset)]




# # multi-label evaluation
# def multiLabelEval(model, loader, args):
#     model.eval()
#     accurate_cnt_micro = 0.0
#     accurate_cnt_hamming_loss = 0.0
#     accurate_cnt_exact_match = 0.0
#     with torch.no_grad():
#         for data in loader:
#             data_subgs, y = batch_data_to_device(data, args.device)
#             y_model = model(data_subgs)
#             y_model = (y_model > 0.5).cpu().numpy()
#             accurate_cnt_micro += f1_score(y_model, y.cpu().numpy(), average='micro')
#             accurate_cnt_hamming_loss += hamming_loss(y_model, y.cpu().numpy())
#             accurate_cnt_exact_match += accuracy_score(y_model, y.cpu().numpy())
#     return [accurate_cnt_micro / len(loader.dataset), accurate_cnt_hamming_loss / len(loader.dataset), accurate_cnt_exact_match / len(loader.dataset)]

