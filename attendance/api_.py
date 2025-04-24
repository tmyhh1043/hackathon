# attendance/api_.py
import base64
import numpy as np
import cv2
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import os
import json
import time
from attendance.model_train.util import *
from attendance.model_train.data_create import *
import warnings
# 顔画像が保存されている場所
# KNOWN_FACE_PATH = "attendance/face_images/user1.jpg"  # 必要に応じて動的にすることも可能
# KNOWN_FACE_PATH = "C:/Users/shouh/hackathon/attendance/face_images/user1.jpg"
username = {}
# username[0] = 'okada'
# username[1] = 'bouyama'
from django.utils.timezone import now
import datetime
from django.contrib.auth import get_user_model

User = get_user_model()
# ラベル0は岡田，ユーザネームはimgproc
# ラベル1は坊山，ユーザネームはABC
_cached_users = None
_last_updated = None
_cache_timeout = datetime.timedelta(minutes=10)

def get_users_cached():
    global _cached_users, _last_updated
    if _cached_users is None or _last_updated is None or (now() - _last_updated > _cache_timeout):
        _cached_users = list(User.objects.all().values('id', 'username', 'email'))
        _last_updated = now()
    return _cached_users

# APIとして使う場合
def get_users_api(request):
    from django.http import JsonResponse
    return JsonResponse(get_users_cached(), safe=False)

users = User.objects.all()
print(len(users))
name_ls = []
for u in users:
    name_ls.append(u.get_username())
    print(u.get_username())
print(name_ls, len(name_ls))
# exit('10000')
model_name = 'allcnn'
cos_sim = nn.CosineSimilarity()
def create_model():
    model = get_model(model_name, num_classes=2)
    return model

# folder_path = "face_images/"
# file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

@csrf_exempt
def face_login_api(request):
    if request.method == 'POST':
        try:
            # リクエストからBase64画像を取得してOpenCV形式に変換
            data = json.loads(request.body)
            image_data = data.get('image_data')

            format, imgstr = image_data.split(';base64,')
            image_bytes = base64.b64decode(imgstr)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
            checkpoint = torch.load('attendance/weight/{}/net/weight_save_9999.tar'.format(model_name), map_location=torch.device('cpu'))
            model = create_model()
            model.load_state_dict(checkpoint['state_dict'])

            input1 = cv2.resize(frame, (224, 224))
            input1 = torch.from_numpy(input1).float()  # ← ここ image1 は numpy の (224, 224, 3)

            # チャンネル順を (H, W, C) → (C, H, W) に変更（PyTorchの形式）
            input1 = input1.permute(2, 0, 1)  # (3, 224, 224)

            # バッチ次元追加 → (1, 3, 224, 224)
            input1 = input1.unsqueeze(0)
            t1 = time.time()
            output, feature = model(input1, mode='t-SNE')
            
            output = torch.softmax(output, dim=1)
            print(output)
            result = -1
            if output.max().item()>0.6:
                result = torch.argmax(output).item()
            t2 = time.time()
            print(t2-t1)
            if result != -1:
                print(output)
                print(f'{username[result]}が検出されました')
                # 顔一致 → ログイン処理（ここではuser1に固定）
                user = User.objects.get(username=name_ls[result])
                login(request, user)
                return JsonResponse({'success': True, 'message': 'ログイン成功'})
            else:
                return JsonResponse({'success': False, 'message': '顔が一致しません'})

        except Exception as e:
            print('--- 例外発生 ---')
            print(type(e))         # エラーの型（例: ValueError, KeyError）
            print(e)               # エラーメッセージの中身
            import traceback
            traceback.print_exc()  # エラーが起きた場所を表示（← これが超便利！）
            return JsonResponse({'success': False, 'error': str(e)})
    print('on return')
    return JsonResponse({'success': False, 'message': 'POSTのみ対応'})
