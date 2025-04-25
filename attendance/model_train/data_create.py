import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, ConcatDataset
import os 
import numpy as np
# 前処理（画像サイズ統一、正規化など）
from torchvision import transforms

transform_train = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

transform_test = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

#dataloaderの生成
def dataloader(mode = None, path=''):
    if mode!=None: path = 'attendance/model_train/'
    # print(os.getcwd())
    # データセットを読み込む
    train_dataset = datasets.ImageFolder(root=path+'dataset_cut/train', transform=transform_train)
    val_dataset   = datasets.ImageFolder(root=path+'dataset_cut/val', transform=transform_test)

    # DataLoaderに変換
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=0)
    val_loader   = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=0)

    if mode == 'concat':
        concat_dataset = ConcatDataset([train_dataset, val_dataset])
        return DataLoader(concat_dataset, batch_size=32, shuffle=False, num_workers=0)

    return train_loader, val_loader
