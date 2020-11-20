import torch
from model.model import UNet
from dataset import LTSIDDataset
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
import transforms as trf
import numpy as np
import torch.optim as optim
import torch.nn as nn
import os.path
from pathlib import Path

np.random.seed(0) # Deterministic random
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

train_dir = './data/short/'
truth_dir = './data/long/'
checkpoint_dir = './checkpoint/'
checkpoint_path = checkpoint_dir + 'checkpoint.t7'
patch_size = 512
save_interval = 5   # epochs
batch_size = 4
initial_learning_rate = 1e-4
epochs = 4001

# Set up dataset and dataloader
print('Loading dataset...')
dataset = LTSIDDataset(train_dir, truth_dir, 
                        transforms=transforms.Compose([
                                                        trf.RandomCrop(patch_size),
                                                        trf.ToTensor(),
                                                        trf.RandomHorizontalFlip(p=0.5),
                                                        trf.RandomVerticalFlip(p=0.5),
                                                        trf.RandomTranspose(p=0.5),
                                                      ]))
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
print('Dataset loaded!')

# Set up model
model = UNet().to(device)

# Set up loss function
loss_func = nn.L1Loss()

# Set up optimizer
optimizer = optim.Adam(model.parameters(), lr=initial_learning_rate)

# Load model (if applicable)
start_epoch = 0
exist = os.path.exists(checkpoint_path)
if os.path.exists(checkpoint_path):
  checkpoint = torch.load(checkpoint_path)
  model.load_state_dict(checkpoint['state_dict'])
  optimizer.load_state_dict(checkpoint['optimizer'])
  start_epoch = checkpoint['epoch']

# Make model checkpoint dir
Path(checkpoint_dir).mkdir(exist_ok=True)

# Training loop
print('Starting training loop...')
for epoch in range(start_epoch, epochs):
  print('Starting epoch: %d' % epoch)
  if epoch > 2000:
    new_learning_rate = 1e-5
    print('Reducing learning rate to', new_learning_rate)
    optimizer.param_groups['lr'] = new_learning_rate # Reduce learning rate in late training

  epoch_loss = 0.0
  for idx, data in enumerate(dataloader):
    train, truth = data['train'].to(device), data['truth'].to(device)
    optimizer.zero_grad()

    outputs = model(train)
    loss = loss_func(outputs, truth)
    loss.backward()
    optimizer.step()

    epoch_loss = epoch_loss + loss
    
  print('Epoch: %5d | Loss: %.3f' % (epoch, epoch_loss))
  if epoch % save_interval == 0:
      state = {
          'epoch': epoch,
          'state_dict': model.state_dict(),
          'optimizer': optimizer.state_dict(),
      }
      torch.save(state, checkpoint_path)
      print('Saved state to ', checkpoint_path)

print('Training complete!')
# dataloader_iterator = iter(dataloader)
# data = next(dataloader_iterator)
# print(data['train'].shape)
# print(data['truth'].shape)

# print(torch.all(torch.eq(data['truth'][1], data['truth'][0])))

