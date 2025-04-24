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

# import cv2

# # カスケード分類器の読み込み（OpenCVが提供）
# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
# folder_path = "face_images/"
# # all_file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

# dataset_dir = "attendance/model_train/dataset"
# file_paths = []

# # 再帰的に走査
# for root, dirs, files in os.walk(dataset_dir):
#     for file in files:
#         file_path = os.path.join(root, file)
#         file_paths.append(file_path)
# print(len(file_paths))
# for id, file_path in enumerate(file_paths[28:]):
#     # 画像の読み込み
#     img = cv2.imread(file_path)
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     # 顔検出
#     faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

#     # # 白背景画像を作成（元画像と同じサイズ・3チャンネル）
#     # masked_img = np.full_like(img, fill_value=255)

#     # # 検出された顔の領域だけ元画像からコピー
#     # for (x, y, w, h) in faces:
#     #     masked_img[y:y+h, x:x+w] = img[y:y+h, x:x+w]

#     # # 結果を保存
#     h_ls = []
#     for (x, y, w, h) in faces:
#       h_ls.append(h)
#     if len(h_ls)==0:
#         break
#     i = np.argmax(h_ls)  
#     x, y, w, h = faces[i]    
#     face_img = img[y:y+h, x:x+w]
        
#     print(folder_path+str(id)+'.jpg')
#     cv2.imwrite(file_path, face_img)

def dataloader(mode = None, path=''):
    if mode!=None: path = 'attendance/model_train/'
    # print(os.getcwd())
    # データセットを読み込む
    train_dataset = datasets.ImageFolder(root=path+'dataset/train', transform=transform_train)
    val_dataset   = datasets.ImageFolder(root=path+'dataset/val', transform=transform_test)

    # DataLoaderに変換
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=0)
    val_loader   = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=0)

    if mode == 'concat':
        concat_dataset = ConcatDataset([train_dataset, val_dataset])
        return DataLoader(concat_dataset, batch_size=32, shuffle=False, num_workers=0)

    return train_loader, val_loader
# print(len(train_loader.dataset))
# print(train_dataset.classes)  # ['class1', 'class2']
# print(train_dataset.class_to_idx)  # {'class1': 0, 'class2': 1}
# images, labels = next(iter(train_loader))
# print(images.shape)  # torch.Size([32, 3, 160, 160])
# print(labels)        # tensor([0, 1, 0, ..., 1])
