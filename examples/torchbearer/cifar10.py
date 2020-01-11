import argparse

import torch
import torch.nn as nn
import torchvision
import torch.optim as optim
from torchvision import transforms

import torchbearer
from torchbearer import Trial
from torchbearer.cv_utils import DatasetValidationSplitter

import dbxlogger as dbx
from dbxlogger.integrations.torchbearer_print import DbxCallbackPrint
from dbxlogger.integrations.torchbearer import DbxCallback


class SimpleModel(nn.Module):
    def __init__(self):
        super(SimpleModel, self).__init__()
        self.convs = nn.Sequential(
            nn.Conv2d(3, 16, stride=2, kernel_size=3),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.Conv2d(16, 32, stride=2, kernel_size=3),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 64, stride=2, kernel_size=3),
            nn.BatchNorm2d(64),
            nn.ReLU()
        )

        self.classifier = nn.Linear(576, 10)

    def forward(self, x):
        x = self.convs(x)
        x = x.view(-1, 576)
        return self.classifier(x)


def datasets(batch_size, data_path):
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                        std=[0.229, 0.224, 0.225])

    dataset = torchvision.datasets.CIFAR10(root=data_path, train=True, download=True,
                                            transform=transforms.Compose([transforms.ToTensor(), normalize]))

    dataset.targets = dataset.targets[:96]
    dataset.data = dataset.data[:96, :, :, :]

    splitter = DatasetValidationSplitter(len(dataset), 0.1)
    trainset = splitter.get_train_dataset(dataset)
    valset = splitter.get_val_dataset(dataset)

    traingen = torch.utils.data.DataLoader(trainset, pin_memory=True, batch_size=batch_size, shuffle=True, num_workers=10)
    valgen = torch.utils.data.DataLoader(valset, pin_memory=True, batch_size=batch_size, shuffle=True, num_workers=10)


    testset = torchvision.datasets.CIFAR10(root=data_path, train=False, download=True,
                                           transform=transforms.Compose([transforms.ToTensor(), normalize]))
    testgen = torch.utils.data.DataLoader(testset, pin_memory=True, batch_size=batch_size, shuffle=False, num_workers=10)

    return traingen, valgen, testgen

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-bs", type=int, help="batch size", default=128)
    parser.add_argument("-lr", type=float, help="learning rate", default=0.001)
    parser.add_argument("-epochs", type=int, help="num epochs", default=5)
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA training')
    parser.add_argument('--seed', type=int, default=1, metavar='S',
                        help='random seed (default: 1)')
    parser.add_argument("--data-path", type=str, default="./data")

    dbx.add_arguments_to(parser)
    args = parser.parse_args()

    model = SimpleModel()
    traingen, valgen, testgen = datasets(args.bs, args.data_path)

    device = 'cuda' if torch.cuda.is_available() and not args.no_cuda else 'cpu'
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr)
    loss = nn.CrossEntropyLoss()

    exp = dbx.exp_from_args(
        args,
        kind="torchbearer-cifar",
        args_to_ignore=["no_cuda", "data_path"],
        env=False)
    exp.save()
    exp.print_info()

    callbacks = [DbxCallback(exp)]

    trial = Trial(model, optimizer, loss, metrics=['acc', 'loss'], callbacks=callbacks).to(device)
    trial.with_generators(train_generator=traingen, val_generator=valgen, test_generator=testgen)
    history = trial.run(epochs=args.epochs, verbose=1)

if __name__ == "__main__":
    main()
