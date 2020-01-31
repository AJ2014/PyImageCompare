import cv2
import numpy as np
from matplotlib import pyplot as plt
from skimage.measure import compare_ssim

img = cv2.imread('gray/ac_button_alternativemode03_normal.png', cv2.IMREAD_UNCHANGED)

ret,thresh1 = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
ret,thresh2 = cv2.threshold(img,127,255,cv2.THRESH_BINARY_INV)
ret,thresh3 = cv2.threshold(img,127,255,cv2.THRESH_TRUNC)
ret,thresh4 = cv2.threshold(img,127,255,cv2.THRESH_TOZERO)
ret,thresh5 = cv2.threshold(img,127,255,cv2.THRESH_TOZERO_INV)
alphaImg = img[:,:,3]
rgbImg = img[:,:,:3]

img2 = cv2.imread('blue/ac_button_alternativemode03_press.png', cv2.IMREAD_UNCHANGED)

ret,thresh21 = cv2.threshold(img2,127,255,cv2.THRESH_BINARY)
ret,thresh22 = cv2.threshold(img2,127,255,cv2.THRESH_BINARY_INV)
ret,thresh23 = cv2.threshold(img2,127,255,cv2.THRESH_TRUNC)
ret,thresh24 = cv2.threshold(img2,127,255,cv2.THRESH_TOZERO)
ret,thresh25 = cv2.threshold(img2,127,255,cv2.THRESH_TOZERO_INV)
alphaImg2 = img2[:,:,3]
rgbImg2 = img2[:,:,:3]

titles = ['Original Image{:d}','BINARY{:d}','BINARY_INV{:d}','TRUNC{:d}','TOZERO{:d}','TOZERO_INV{:d}', 'ALPHA{:d}', 'RGB{:d}']
images = [img, thresh1, thresh2, thresh3, thresh4, thresh5, alphaImg, rgbImg]
images2 = [img2, thresh21, thresh22, thresh23, thresh24, thresh25, alphaImg2, rgbImg2]

plt.subplot(1, 2, 1),plt.hist(img.ravel(),256,[0,256])
plt.subplot(1, 2, 2),plt.hist(img2.ravel(),256,[0,256])
plt.show()

for i, j in zip(range(0, 24, 3), range(0, 8)):
    plt.subplot(8,3,i+1),plt.imshow(images[j])
    plt.title(titles[j].format(i + 1))
    plt.xticks([]),plt.yticks([])

    plt.subplot(8,3,i+2),plt.imshow(images2[j])
    plt.title(titles[j].format(i + 2))
    plt.xticks([]),plt.yticks([])

    bgrScore, diff = compare_ssim(images[j], images2[j], multichannel=True, full=True)
    diff = (diff * 255).astype("uint8")
    plt.subplot(8,3,i+3),plt.imshow(diff)
    plt.title('ssim={}'.format(bgrScore))
    plt.xticks([]),plt.yticks([])

plt.subplots_adjust(hspace=1, wspace=0.1)
plt.show()

cv2.waitKey(0)
cv2.destroyAllWindows()
