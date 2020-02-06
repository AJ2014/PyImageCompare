import cv2
import numpy as np
from matplotlib import pyplot as plt
from skimage.measure import compare_ssim

img1 = cv2.imread('future-skin-red/res/mipmap-mdpi/menu_music_background_press.png', cv2.IMREAD_UNCHANGED)
img2 = cv2.imread('launcher/launcher/mipmap-mdpi/menu_music_background_press.png', cv2.IMREAD_UNCHANGED)
img3 = cv2.imread('launcher/launcher/mipmap-mdpi/menu_music_background_select.png', cv2.IMREAD_UNCHANGED)
print('multichannel')
score2 = compare_ssim(img1, img2, multichannel=True)
score3 = compare_ssim(img1, img3, multichannel=True)
print('score2={}, score3={}'.format(score2, score3))

#to alpha
alpha1 = img1[:,:,3]
alpha2 = img2[:,:,3]
alpha3 = img3[:,:,3]
print('alpha')
alphaScore2 = compare_ssim(alpha1, alpha2, multichannel=True)
alphaScore3 = compare_ssim(alpha1, alpha3, multichannel=True)
print('score2={}, score3={}'.format(alphaScore2, alphaScore3))
#to bgr
bgr1 = img1[:,:,:3]
bgr2 = img2[:,:,:3]
bgr3 = img3[:,:,:3]
print('bgr')
bgrScore2 = compare_ssim(bgr1, bgr2, multichannel=True)
bgrScore3 = compare_ssim(bgr1, bgr3, multichannel=True)
print('score2={}, score3={}'.format(bgrScore2, bgrScore3))
#to gray
gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
gray3 = cv2.cvtColor(img3, cv2.COLOR_BGR2GRAY)
print('gray')
grayScore2 = compare_ssim(gray1, gray2, multichannel=True)
grayScore3 = compare_ssim(gray1, gray3, multichannel=True)
print('score2={}, score3={}'.format(grayScore2, grayScore3))
#threshold
(thresh, im_bw1) = cv2.threshold(img1, 1, 255, cv2.THRESH_BINARY)
(thresh, im_bw2) = cv2.threshold(img2, 1, 255, cv2.THRESH_BINARY)
(thresh, im_bw3) = cv2.threshold(img3, 1, 255, cv2.THRESH_BINARY)
print('threshold')
thsScore2 = compare_ssim(im_bw1, im_bw2, multichannel=True)
thsScore3 = compare_ssim(im_bw1, im_bw3, multichannel=True)
print('score2={}, score3={}'.format(thsScore2, thsScore3))

plt.subplot(5, 3, 1)
plt.imshow(img1, 'gray')
plt.title('img1')

plt.subplot(5, 3, 2)
plt.imshow(img2, 'gray')
plt.title('img2={:f}'.format(score2))

plt.subplot(5, 3, 3)
plt.imshow(img3, 'gray')
plt.title('img3={:f}'.format(score3))

plt.subplot(5, 3, 4)
plt.imshow(alpha1, 'gray')
plt.title('alpha1')

plt.subplot(5, 3, 5)
plt.imshow(alpha2, 'gray')
plt.title('alpha2={:f}'.format(alphaScore2))

plt.subplot(5, 3, 6)
plt.imshow(alpha3, 'gray')
plt.title('alpha3={:f}'.format(alphaScore3))

plt.subplot(5, 3, 7)
plt.imshow(gray1, 'gray')
plt.title('gray1')

plt.subplot(5, 3, 8)
plt.imshow(gray2, 'gray')
plt.title('gray2={:f}'.format(grayScore2))

plt.subplot(5, 3, 9)
plt.imshow(gray3, 'gray')
plt.title('gray3={:f}'.format(grayScore3))

plt.subplot(5, 3, 10)
plt.imshow(im_bw1, 'gray')
plt.title('ths1')

plt.subplot(5, 3, 11)
plt.imshow(im_bw2, 'gray')
plt.title('ths2={:f}'.format(thsScore2))

plt.subplot(5, 3, 12)
plt.imshow(im_bw3, 'gray')
plt.title('ths3={:f}'.format(thsScore3))

plt.subplot(5, 3, 13)
plt.imshow(bgr1, 'gray')
plt.title('bgr1')

plt.subplot(5, 3, 14)
plt.imshow(bgr2, 'gray')
plt.title('bgr2={:f}'.format(bgrScore2))

plt.subplot(5, 3, 15)
plt.imshow(bgr3, 'gray')
plt.title('bgr3={:f}'.format(bgrScore3))

plt.subplots_adjust(hspace=1, wspace=0.1)
plt.show()
