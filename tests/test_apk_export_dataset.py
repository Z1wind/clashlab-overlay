# -*- coding: utf-8 -*-
import json, os, tempfile, unittest
import numpy as np, cv2
from tools.apk_export_to_dataset import crops_for_base

class T(unittest.TestCase):
    def test_crops(self):
        d = tempfile.mkdtemp()
        img = np.zeros((200, 400, 3), np.uint8)
        os.makedirs(os.path.join(d, 'img'), exist_ok=True)
        cv2.imwrite(os.path.join(d, 'img', 'b01.jpg'), img)
        base = {'image': 'img/b01.jpg', 'image_size': [400, 200],
                'corners_norm': [[0.2, 0.5], [0.5, 0.2], [0.8, 0.5], [0.5, 0.8]],
                'buildings': [{'type': 'cannon', 'tile': [20, 20]}]}
        crops, p = crops_for_base(base, d)
        self.assertEqual(len(crops), 1)
        self.assertEqual(crops[0][0].shape, (96, 96, 3))
        self.assertEqual(crops[0][1]['type'], 'cannon')

if __name__ == '__main__':
    unittest.main()