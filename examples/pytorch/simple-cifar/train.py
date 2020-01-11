#!/usr/bin/env python3

# This example is based on the PyTorch CIFAR example provided at
#     https://github.com/pytorch/examples/blob/master/mnist/main.py

import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.optim.lr_scheduler import StepLR

import dbxlogger as dbx

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout2d(0.25)
        self.dropout2 = nn.Dropout2d(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output


def train(log, model, device, train_loader, optimizer):
    model.train()

    for batch_idx, (data, target) in enumerate(train_loader):
        if batch_idx % 5 == 0:
            event = log.new_event("batch/%d/stats" % batch_idx, save_duration=True)

        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()

        # full event paths is epoch/<epoch_id>/batch/<batch_idx>/stats
        if batch_idx % 5 == 0:
            log(event, {"train_loss": loss.item()})

def test(log, model, device, test_loader):
    event = log.new_event("test", save_duration=True)
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction='sum').item()  # sum up batch loss
            pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)
    log(event, {
        "avg_test_loss": test_loss,
        "test_acc": 100. * correct / len(test_loader.dataset),
        "num_correct": correct,
        "num_total": len(test_loader.dataset),
    })

def main():
    # Training settings
    parser = argparse.ArgumentParser(description='PyTorch MNIST Example with dbxlogger')

    # add dbx arguments (-o or --savedir, --name)
    dbx.add_arguments_to(parser)

    parser.add_argument('--batch-size', type=int, default=64, metavar='N',
                        help='input batch size for training (default: 64)')
    parser.add_argument('--test-batch-size', type=int, default=1000, metavar='N',
                        help='input batch size for testing (default: 1000)')
    parser.add_argument('--epochs', type=int, default=14, metavar='N',
                        help='number of epochs to train (default: 10)')
    parser.add_argument('--lr', type=float, default=1.0, metavar='LR',
                        help='learning rate (default: 1.0)')
    parser.add_argument('--gamma', type=float, default=0.7, metavar='M',
                        help='Learning rate step gamma (default: 0.7)')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA training')
    parser.add_argument('--seed', type=int, default=1, metavar='S',
                        help='random seed (default: 1)')
    parser.add_argument("--data-path", type=str, default="./data")

    args = parser.parse_args()
    use_cuda = not args.no_cuda and torch.cuda.is_available()

    exp = dbx.exp_from_args(
        args,
        args_to_ignore=["no_cuda", "data_path"],
        env=False)

    exp.save()
    logger = exp.logger()

    torch.manual_seed(args.seed)

    device = torch.device("cuda" if use_cuda else "cpu")

    kwargs = {'num_workers': 1, 'pin_memory': True} if use_cuda else {}
    train_loader = torch.utils.data.DataLoader(
        datasets.MNIST(args.data_path, train=True, download=True,
                       transform=transforms.Compose([
                           transforms.ToTensor(),
                           transforms.Normalize((0.1307,), (0.3081,))
                       ])),
        batch_size=args.batch_size, shuffle=True, **kwargs)
    test_loader = torch.utils.data.DataLoader(
        datasets.MNIST(args.data_path, train=False, transform=transforms.Compose([
                           transforms.ToTensor(),
                           transforms.Normalize((0.1307,), (0.3081,))
                       ])),
        batch_size=args.test_batch_size, shuffle=True, **kwargs)

    model = Net().to(device)
    optimizer = optim.Adadelta(model.parameters(), lr=args.lr)

    scheduler = StepLR(optimizer, step_size=1, gamma=args.gamma)
    for epoch in range(1, args.epochs + 1):
        epoch_logger = logger.sub("epoch/%d" % epoch)

        # create epoch event here to automatically track timing
        epoch_event = epoch_logger.new_event("summary", save_duration=True) # full event name "/epoch/<epoch_num>/summary"

        # using logger.sub("train"), so the logger inside train() logs under
        # "epoch/<epoch_num>/train/..."
        train(epoch_logger.sub("train"), model, device, train_loader, optimizer)
        test(epoch_logger, model, device, test_loader)

        logger(epoch_event, {"lr": get_current_lr(optimizer)})

        scheduler.step()

    with exp.file("mnist_cnn.pt", "wb") as f:
        torch.save(model.state_dict(), f)

def get_current_lr(optimizer):
    """Get the current learning rate from the optimizer."""
    for g in optimizer.param_groups:
        return g["lr"]

if __name__ == '__main__':
    main()
