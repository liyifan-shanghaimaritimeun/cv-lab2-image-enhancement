# -*- coding: utf-8 -*-
"""
实验二：图像增强（整合版）
================================
将前期零散脚本整合为一个可直接运行的完整流程：
  2.1 导入依赖
  2.2 读取图像、取像素值、色彩空间转换
  2.3 添加椒盐噪声与高斯噪声
  2.4 均值 / 中值 / 高斯三种滤波对比
  2.5 手动实现彩色中值滤波（不调用 OpenCV）
  2.6 自定义高斯核 + 二维卷积（整合自前期 conv_2d 脚本）

运行：python 实验二_图像增强.py
所有图片保存到 output_images/ 与 result/
"""
import os
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import cv2
from numpy.lib.stride_tricks import sliding_window_view

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, 'output_images')
RES_DIR = os.path.join(BASE, 'result')
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

# ==================== 2.2 读取原始图像 ====================
img = cv2.imread(os.path.join(BASE, 'p1.jpg'))
print('图像尺寸:', img.shape)

(b, g, r) = img[100, 100]
print('像素(100,100) BGR =', b, g, r)

plt.figure(figsize=(5, 5))
plt.imshow(img)
plt.title('Original Image (BGR)')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'original_bgr.jpg'), dpi=300)
plt.close()

rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
plt.figure(figsize=(5, 5))
plt.imshow(rgb_img)
plt.title('RGB Image')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'rgb_image.jpg'), dpi=300)
plt.close()

gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
plt.figure(figsize=(5, 5))
plt.imshow(gray_img, cmap='gray')
plt.title('Gray Image')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'gray_image.jpg'), dpi=300)
plt.close()

plt.figure(figsize=(14, 4.6))
plt.subplot(1, 3, 1)
plt.imshow(img)
plt.title('Original Image (BGR)')
plt.axis('off')
plt.subplot(1, 3, 2)
plt.imshow(rgb_img)
plt.title('RGB Image')
plt.axis('off')
plt.subplot(1, 3, 3)
plt.imshow(gray_img, cmap='gray')
plt.title('Gray Image')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'color_space.jpg'), dpi=300)
plt.close()

# ==================== 2.3 添加噪声 ====================
def add_salt_pepper(image, amount=0.4):
    """椒盐噪声：随机把 amount 比例的像素置为纯黑或纯白"""
    out = image.astype(np.float64).copy()
    h, w = out.shape[:2]
    n = int(amount * h * w)
    ys = np.random.randint(0, h, n)
    xs = np.random.randint(0, w, n)
    half = n // 2
    out[ys[:half], xs[:half]] = 0.0
    out[ys[half:], xs[half:]] = 1.0
    return out


def add_gaussian_noise(image, mean=0.2, var=0.03):
    """高斯噪声：每个像素叠加服从 N(mean, var) 的随机偏差"""
    noise = np.random.normal(mean, np.sqrt(var), image.shape)
    return np.clip(image.astype(np.float64) + noise, 0.0, 1.0)


rgb_float = rgb_img.astype(np.float64) / 255.0
sp_noise_img = add_salt_pepper(rgb_float, amount=0.4)
gus_noise_img = add_gaussian_noise(rgb_float, mean=0.2, var=0.03)

plt.figure(figsize=(13, 4.2))
plt.subplot(1, 3, 1)
plt.imshow(rgb_img)
plt.title('Original Image')
plt.axis('off')
plt.subplot(1, 3, 2)
plt.imshow(sp_noise_img)
plt.title('S&P Noise')
plt.axis('off')
plt.subplot(1, 3, 3)
plt.imshow(gus_noise_img)
plt.title('Gaussian Noise')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'noise_comparison.jpg'), dpi=300)
plt.close()

# ==================== 2.4 三种滤波对比 ====================
mean_sp = cv2.blur(sp_noise_img, (5, 5))
mean_gus = cv2.blur(gus_noise_img, (5, 5))

sp_u8 = (sp_noise_img * 255).astype(np.uint8)
gus_u8 = (gus_noise_img * 255).astype(np.uint8)

mid_sp = cv2.medianBlur(sp_u8, 5)
mid_gus = cv2.medianBlur(gus_u8, 5)

gauss_sp = cv2.GaussianBlur(sp_u8, (5, 5), 0)
gauss_gus = cv2.GaussianBlur(gus_u8, (5, 5), 0)

fig, axes = plt.subplots(2, 3, figsize=(13, 8.6))
items = [
    (mean_sp, 'S&P Noise with Mean Filter'),
    (mid_sp, 'S&P Noise with Median Filter'),
    (gauss_sp, 'S&P Noise with Gaussian Filter'),
    (mean_gus, 'Gaussian Noise with Mean Filter'),
    (mid_gus, 'Gaussian Noise with Median Filter'),
    (gauss_gus, 'Gaussian Noise with Gaussian Filter'),
]
for ax, (im, title) in zip(axes.ravel(), items):
    ax.imshow(im)
    ax.set_title(title, fontsize=11)
    ax.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(RES_DIR, 'filter_results_2x3.jpg'), dpi=300)
plt.close()

# ==================== 2.5 手动实现彩色中值滤波 ====================
def manual_median_filter_color(image, kernel_size=5):
    """逐通道手动中值滤波，不调用 cv2.medianBlur"""
    pad = kernel_size // 2
    out = np.zeros_like(image, dtype=np.uint8)
    padded = np.pad(image, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
    h, w = image.shape[:2]
    block = 64
    for r0 in range(0, h, block):
        r1 = min(r0 + block, h)
        win = sliding_window_view(padded[r0:r1 + 2 * pad],
                                  (kernel_size, kernel_size), axis=(0, 1))
        out[r0:r1] = np.median(win, axis=(-2, -1)).astype(np.uint8)
    return out


t0 = time.time()
manual_mid = manual_median_filter_color(sp_u8, 5)
print('手动中值滤波耗时: %.2f s' % (time.time() - t0))

diff = np.abs(manual_mid.astype(np.int16) - mid_sp.astype(np.int16))
print('与 cv2.medianBlur 的最大像素差:', diff.max())

plt.figure(figsize=(10, 4.6))
plt.subplot(1, 2, 1)
plt.imshow(sp_noise_img)
plt.title('S&P Noise Image')
plt.axis('off')
plt.subplot(1, 2, 2)
plt.imshow(manual_mid)
plt.title('Manual Median Filter (k=5)')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(RES_DIR, 'manual_median.jpg'), dpi=300)
plt.close()

# ==================== 2.6 自定义高斯核卷积 ====================
def gauss(kernel_size, sigma):
    """按二维高斯函数逐点生成归一化卷积核"""
    kernel = np.zeros((kernel_size, kernel_size), dtype=np.float64)
    center = kernel_size // 2
    s = sigma ** 2
    for i in range(kernel_size):
        for j in range(kernel_size):
            x, y = i - center, j - center
            kernel[i, j] = np.exp(-(x ** 2 + y ** 2) / (2 * s))
    return kernel / kernel.sum()


k_gauss = gauss(7, 2)
print('自定义高斯核(7x7, sigma=2):')
print(np.round(k_gauss, 4))

conv_gus = cv2.filter2D(gus_noise_img.astype(np.float32), -1, k_gauss.astype(np.float32))
conv_gus = np.clip(conv_gus, 0, 1)

plt.figure(figsize=(12, 4.2))
plt.subplot(1, 3, 1)
plt.imshow(gus_noise_img)
plt.title('Gaussian Noise Image')
plt.axis('off')
plt.subplot(1, 3, 2)
plt.imshow(k_gauss, cmap='viridis')
plt.title('Custom Gaussian Kernel (7x7)')
plt.axis('off')
plt.subplot(1, 3, 3)
plt.imshow(conv_gus)
plt.title('Convolution Result')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(RES_DIR, 'custom_gaussian.jpg'), dpi=300)
plt.close()

print('\n实验二全部步骤执行完毕')
