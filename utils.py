def batch_data_to_device(data, device):
    data_subgs, y = data
    for idx, data_subg in enumerate(data_subgs):
        data_subgs[idx] = data_subg.to(device)
    y = y.to(device)
    return [data_subgs, y]