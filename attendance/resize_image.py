from PIL import Image

# 画像のパス
path = "./attendance/face_images/user1.jpg"
output_path = "./attendance/face_images/image_resized.jpg"

# 画像を開いてリサイズ
with Image.open(path) as img:
    img_resized = img.resize((160, 160))
    img_resized.save(output_path, format="JPEG")
