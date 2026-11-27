# -*- coding: utf-8 -*-
import json, os, tempfile, unittest
import numpy as np, cv2
from tools.apk_export_to_dataset import crops_for_base

class T(unittest.TestCase):
    def _mk(self, corners_norm, tile):
        d = tempfile.mkdtemp()
        img = np.zeros((200, 400, 3), np.uint8)
        os.makedirs(os.path.join(d, 'img'), exist_ok=True)
        cv2.imwrite(os.path.join(d, 'img', 'b01.jpg'), img)
        base = {'image': 'img/b01.jpg', 'image_size': [400, 200],
                'corners_norm': corners_norm,
                'buildings': [{'type': 'cannon', 'tile': tile}]}
        return crops_for_base(base, d)

    def test_crops(self):
        crops, p = self._mk([[0.2, 0.5], [0.5, 0.2], [0.8, 0.5], [0.5, 0.8]], [20, 20])
        self.assertEqual(len(crops), 1)
        self.assertEqual(crops[0][0].shape, (96, 96, 3))
        self.assertEqual(crops[0][1]['type'], 'cannon')

    def test_corners_outside_image(self):
        # 角点可以落在图片外（v0.2.6 新行为）：不应崩溃，仍产出 96x96 裁剪
        crops, p = self._mk([[-0.1, 0.5], [0.5, -0.1], [1.1, 0.5], [0.5, 1.1]], [20, 20])
        self.assertEqual(len(crops), 1)
        self.assertEqual(crops[0][0].shape, (96, 96, 3))

    def test_bundle_export(self):
        d = tempfile.mkdtemp()
        img = np.zeros((200, 400, 3), np.uint8)
        os.makedirs(os.path.join(d, 'img'), exist_ok=True)
        cv2.imwrite(os.path.join(d, 'img', 'b01.jpg'), img)
        base = {'image': 'img/b01.jpg', 'image_size': [400, 200],
                'corners_norm': [[0.2, 0.5], [0.5, 0.2], [0.8, 0.5], [0.5, 0.8]],
                'buildings': [{'type': 'cannon', 'tile': [10, 10]}, {'type': 'mortar', 'tile': [30, 30]}]}
        doc = {'version': 2, 'count': 1, 'bases': [base]}
        p = os.path.join(d, 'annot_all.json')
        json.dump(doc, open(p, 'w', encoding='utf-8'))
        from tools.apk_export_to_dataset import load_export
        bases = load_export(p)
        self.assertEqual(len(bases), 1)
        crops, _ = crops_for_base(bases[0], d)
        self.assertEqual(len(crops), 2)

if __name__ == '__main__':
    unittest.main()