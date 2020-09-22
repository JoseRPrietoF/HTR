from __future__ import absolute_import
import cv2
from PIL import Image
from torch.utils import data


class ImageDataset(data.Dataset):
    def __init__(self, imgs, transform=None):
        assert isinstance(imgs, (list, tuple))
        super(ImageDataset, self).__init__()
        self._imgs = imgs
        self._transform = transform

    def __getitem__(self, index):
        """Returns a dictionary containing the given image from the dataset.
        The image is associated with the key 'img'."""
        img_name = self._imgs[index]
        img = cv2.imread(img_name)
        #img = Image.open(img_name)
        # You may need to convert the color.
        #
        #img = img.transpose(1,0,2)
        #print(img.shape)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)

        if self._transform:
            img = self._transform(img)
        return {"img": img}

    def __len__(self):
        return len(self._imgs)