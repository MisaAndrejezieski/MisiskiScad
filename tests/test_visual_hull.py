import os
import tempfile
import unittest

import numpy as np
import trimesh
from PIL import Image

from visual_hull import VIEW_NAMES, reconstruct_visual_hull


class VisualHullTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.image_paths = {}
        image = np.zeros((32, 32, 3), dtype=np.uint8)
        image[8:24, 8:24] = 255
        for name in VIEW_NAMES:
            path = os.path.join(self.temp_dir.name, name + ".png")
            Image.fromarray(image).save(path)
            self.image_paths[name] = path

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_six_silhouettes_create_closed_mesh_at_requested_dimensions(self):
        mesh, grid_shape = reconstruct_visual_hull(
            self.image_paths, 50, 50, 50, resolution=32
        )

        self.assertEqual(grid_shape, (32, 32, 32))
        self.assertTrue(mesh.is_watertight)
        np.testing.assert_allclose(mesh.extents, [50, 50, 50])
        self.assertGreater(mesh.volume, 0)

    def test_incomplete_view_set_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "seis vistas"):
            reconstruct_visual_hull(
                {"frente": self.image_paths["frente"]},
                50,
                50,
                50,
            )

    def test_reconstructed_mesh_survives_stl_export_and_reload(self):
        mesh, _ = reconstruct_visual_hull(
            self.image_paths, 50, 40, 30, resolution=32
        )
        path = os.path.join(self.temp_dir.name, "model.stl")
        mesh.export(path)
        restored = trimesh.load_mesh(path, file_type="stl", process=True)

        self.assertTrue(restored.is_watertight)
        np.testing.assert_allclose(restored.extents, [50, 40, 30], atol=0.1)

    def test_silhouettes_without_foreground_are_rejected(self):
        blank = np.zeros((32, 32, 3), dtype=np.uint8)
        path = os.path.join(self.temp_dir.name, "blank.png")
        Image.fromarray(blank).save(path)
        paths = {name: path for name in VIEW_NAMES}

        with self.assertRaisesRegex(ValueError, "silhueta"):
            reconstruct_visual_hull(paths, 50, 50, 50)


if __name__ == "__main__":
    unittest.main()
