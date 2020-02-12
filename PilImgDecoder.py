from PIL import Image

filepath = '../com_loading_100.png'
img = Image.open(filepath)

print('mode={}, size={}, category={}, format={}'.format(img.mode, img.size, img.category, img.format))

print(str(img))

