# attendance/api_.py
import base64
import numpy as np
import cv2
from deepface import DeepFace
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import os

# 顔画像が保存されている場所
KNOWN_FACE_PATH = "face_images/user1.jpg"  # 必要に応じて動的にすることも可能

@csrf_exempt
def face_login_api(request):
    if request.method == 'POST':
        try:
            # JSON から画像データを取り出す
            data = request.json() if hasattr(request, 'json') else json.loads(request.body)
            image_data = data.get('image_data')

            # Base64 → OpenCV画像に変換
            format, imgstr = image_data.split(';base64,')
            image_bytes = base64.b64decode(imgstr)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # 顔照合
            result = DeepFace.verify(
                img1_path=frame,
                img2_path=KNOWN_FACE_PATH,
                enforce_detection=True,
                model_name='Facenet'  # おすすめ：Facenet, ArcFace, VGG-Face
            )
            print('in')
            if result["verified"]:
                # 顔一致 → ログイン処理（ここではuser1に固定）
                user = User.objects.get(username='user1')
                login(request, user)
                return JsonResponse({'success': True, 'message': 'ログイン成功'})
            else:
                return JsonResponse({'success': False, 'message': '顔が一致しません'})

        except Exception as e:
            print('exept in')
            return JsonResponse({'success': False, 'error': str(e)})
    print('on return')
    return JsonResponse({'success': False, 'message': 'POSTのみ対応'})
