import torch
import torch.nn.functional as F
import torch.nn as nn
import torch.optim as optim
from util import *
import os
from data_create import *
import warnings
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--model', default='allcnn')
parser.add_argument('--num_classes', default=2, help='認識したいユーザ数')
args = parser.parse_args()
# 警告を非表示にする
warnings.filterwarnings("ignore", category=UserWarning)
def test(epoch,net, data_loader, mode='Test'):
    net.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_idx, (inputs, targets) in enumerate(data_loader):
            # inputs, targets = inputs.cuda(), targets.cuda()
            outputs = net(inputs)
            _, predicted = torch.max(outputs, 1)            
                       
            total += targets.size(0)
            correct += predicted.eq(targets).cpu().sum().item()                 
    acc = 100.*correct/total
    print("\n| %s Epoch #%d\t Accuracy: %.2f%%" %(mode, epoch,acc))  
    return acc
# 重み保存のため
def save_checkpoint(state, filename='checkpoint.pth.tar'):
    torch.save(state, filename)
# モデル定義
def create_model(class_num):
    model = get_model(model_name, num_classes=class_num)
    return model

# 損失関数で使う関数の用意
CEloss = nn.CrossEntropyLoss() 

model_name = args.model
num_classes = args.num_classes
print(f"Number of Classes: {num_classes}")
print('| Building net')
model= create_model(num_classes)
epochs = 30
lr = 0.01
step_size = 15
train_loader, test_loader = dataloader()
parameters = model.parameters()
optimizer = optim.SGD(parameters, lr=lr, momentum=0.9, weight_decay=5e-4)

path_name=f'../../weight/'
dir_name=f'{model_name}/'
os.makedirs(path_name+dir_name+'net/', exist_ok=True)
dir_name = path_name + dir_name
# bestの保存変数
best = 0

# 学習のループ
for epoch in range(epochs+1):   
    lr=lr
    if epoch >= step_size:
        lr /= 10      
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr            

    warmup(epoch,model, train_loader, optimizer)  


    acc = test(epoch,model,test_loader)

    # 以下重み保存
    if ((epoch == epochs)):  
        # save_checkpointは84
        save_checkpoint({
            'epoch': epoch + 1,
            'arch': create_model,
            'state_dict': model.state_dict(),
            'optimizer' : optimizer.state_dict(),
        }, filename='{}/net/weight_save_{:04d}.tar'.format(dir_name, epoch))
        print(f'save_weigh_last:{dir_name}')
    if acc > best:
        best = acc
        save_checkpoint({
                'epoch': epoch + 1,
                'arch': create_model,
                'state_dict': model.state_dict(),
                'optimizer' : optimizer.state_dict(),
            }, filename='{}/net/weight_save_9999.tar'.format(dir_name))
    print(f'save_weigh_best\nepoch:{epoch}\tacc:{best}\n')

