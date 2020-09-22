from models import model
import data.transforms as transforms
import torch
from data import  ImageDataLoader, TextImageFromTextTableDataset, FixedSizeSampler
import multiprocessing
import os
import random
import numpy as np
from torch.optim import RMSprop
from models.ctc_loss import CTCLoss
from models.ctc_greedy_decoder import CTCGreedyDecoder
import tqdm

def worker_init_fn(_):
    # We need to reset the Numpy and Python PRNG, or we will get the
    # same numbers in each epoch (when the workers are re-generated)
    random.seed(torch.initial_seed() % 2 ** 31)
    np.random.seed(torch.initial_seed() % 2 ** 31)

#tr_txt_table = "/data/cristo/data_CRISTO_SALVADOR/TRANSCR/TXT-Lineas-filtradas"
tr_txt_table = "/data2/jose/projects/HTR/works/cristo/tr.txt"
img_dirs = "/data/cristo/data_CRISTO_SALVADOR/LINEAS_PGM_resized"
syms_path =  "/data2/jose/projects/HTR/works/cristo/syms" #Symbols table mapping from strings to integers
gpu = 1
batch_size = 64
EPOCHS = 20
width, height = int(1536.959604286892), int(82.0964550700742)
height_fixed = 10
train_samples_per_epoch = False
use_distortions = False
learning_rate = 0.0005
momentum = 0
rnn_units = 64
rnn_dropout = 0.5
rnn_layers = 3
delimiters = ["<space>"]
device = torch.device("cuda:{}".format(gpu - 1) if gpu else "cpu")
syms = transforms.text.SymbolsTable(syms_path)

model = model.CRNN(num_input_channels=1,
                 num_output_labels=len(syms),
                     rnn_units=rnn_units,
                 rnn_layers=rnn_layers,
                 rnn_dropout=rnn_dropout,
                 lin_dropout=0.5,
                   height=height_fixed)

print(model)
print("Model has {} parameters".format(sum(param.data.numel() for param in model.parameters() )))
model = model.to(device)

default_img_transform = transforms.Compose(
        [
            transforms.vision.Convert("L"),
            #transforms.vision.Invert(),
            transforms.vision.ToTensor(),
        ]
    )
if use_distortions:
    tr_img_transform = transforms.Compose(
        [
            transforms.vision.Convert("L"),
            transforms.vision.Invert(),
            transforms.vision.RandomBetaAffine(),
            transforms.vision.ToTensor(),
        ]
    )
else:
    tr_img_transform = default_img_transform

print("Training data transforms:\n{}", str(tr_img_transform))

tr_dataset = TextImageFromTextTableDataset(
    tr_txt_table,
    img_dirs,
    img_transform=tr_img_transform,
    txt_transform=transforms.text.ToTensor(syms),
)

tr_dataset_loader = ImageDataLoader(
    dataset=tr_dataset,
    image_channels=1,
    image_height=height,
    image_width=width,
    batch_size=batch_size,
    num_workers=multiprocessing.cpu_count(),
    shuffle=not bool(train_samples_per_epoch),
    sampler=FixedSizeSampler(tr_dataset, train_samples_per_epoch)
    if train_samples_per_epoch
    else None,
    worker_init_fn=worker_init_fn,
)

############## Train
optimizer=RMSprop(
            model.parameters(), lr=learning_rate, momentum=momentum
    )


criterion = CTCLoss()
# Train
for epoch in range(EPOCHS):
    epoch_loss = 0.0
    i = 0
    model.train()
    tr_dataset_loader_tqdm = tqdm.tqdm(tr_dataset_loader)
    for batch, sample in enumerate(tr_dataset_loader_tqdm):
        optimizer.zero_grad()
        img = sample['img'].to(device)
        txt = sample['txt']
        ids = sample['id']
        hyp = model(img)
        loss = criterion(hyp, txt)
        loss.backward()
        optimizer.step()
        epoch_loss += (loss / img.data.size()[0])
        if loss is not None:
            if torch.sum(torch.isnan(loss)).item() > 0:
                raise ValueError("The loss is NaN")
            if torch.sum(torch.isinf(loss)).item() > 0:
                raise ValueError("The loss is +/-Inf")
        #print(hyp)
        #exit()

    print("Epoch {} loss {} ".format(epoch, epoch_loss))
    epoch_loss = epoch_loss / (batch + 1)  # mean

tr_dataset_loader_tqdm = tqdm.tqdm(tr_dataset_loader)
model.eval()
decoder = CTCGreedyDecoder()
join_str = ""
separator = " | "
print_img_ids = True
for batch, sample in enumerate(tr_dataset_loader):
    img = sample['img'].to(device)
    txt = sample['txt']
    ids = sample['id']
    batch_output = model(img)
    batch_decode = decoder(batch_output)
    for img_id, out, gt in zip(ids, batch_decode, txt):
        out = [str(syms[val]) for val in out]
        out = join_str.join(str(x) for x in out)
        for d in delimiters:
            out = out.replace(d, " ")
        gt = [str(syms[val]) for val in gt]
        gt = join_str.join(str(x) for x in gt)
        for d in delimiters:
            gt = gt.replace(d, " ")
        print(
            "{}{}{}".format(out, separator, gt)
            if print_img_ids
            else out
        )
exit()