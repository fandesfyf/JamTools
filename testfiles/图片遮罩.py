from PIL import Image, ImageFilter
import time


class MyGaussianBlur(ImageFilter.GaussianBlur):
    name = "GaussianBlur"

    def __init__(self, size,radius=2, bounds=None):
        super().__init__()
        self.radius = radius
        self.bounds = bounds
        self.size=size
        # print(size)

    def filter(self, image):
        print(1)
        if self.bounds:
            bounds1 = (0, 0, self.size[0], self.bounds[1])
            # print(bounds1)
            clips = image.crop(bounds1).gaussian_blur(self.radius)
            image.paste(clips, bounds1)
            bounds2 = (0, self.bounds[1], self.bounds[0], self.bounds[3])
            clips = image.crop(bounds2).gaussian_blur(self.radius)
            image.paste(clips, bounds2)
            bounds3 = (0, self.bounds[3], self.size[0], self.size[1])
            clips = image.crop(bounds3).gaussian_blur(self.radius)
            image.paste(clips, bounds3)
            bounds4 = (self.bounds[2], self.bounds[1], self.size[0], self.bounds[3])
            clips = image.crop(bounds4).gaussian_blur(self.radius)
            image.paste(clips, bounds4)
            return image
        else:
            return image.gaussian_blur(self.radius)


st = time.process_time()
image = Image.open('p.jpg')
bounds = (150, 130, 280, 250)
image = image.filter(MyGaussianBlur(image.size,radius=2, bounds=bounds))
# print(1)

# image = image.filter(MyGaussianBlur(radius=2, bounds=bounds2))
# image = image.filter(MyGaussianBlur(radius=2, bounds=bounds3))
# image = image.filter(MyGaussianBlur(radius=2, bounds=bounds4))

print(time.process_time() - st)
image.show()
