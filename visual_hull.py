"""Reconstrucao de uma malha aproximada a partir de seis silhuetas ortograficas."""

import numpy as np
import trimesh
from PIL import Image


VIEW_NAMES = ("frente", "tras", "esquerda", "direita", "cima", "baixo")


def _read_silhouette(path, threshold):
    with Image.open(path) as source:
        image = source.convert("RGBA")

    rgba = np.asarray(image, dtype=np.uint8)
    alpha = rgba[:, :, 3]
    if np.any(alpha < 250):
        mask = alpha > 16
    else:
        rgb = rgba[:, :, :3].astype(np.int16)
        height, width = rgb.shape[:2]
        border_size = max(1, min(height, width) // 20)
        border = np.concatenate(
            (
                rgb[:border_size].reshape(-1, 3),
                rgb[-border_size:].reshape(-1, 3),
                rgb[:, :border_size].reshape(-1, 3),
                rgb[:, -border_size:].reshape(-1, 3),
            )
        )
        background = np.median(border, axis=0)
        distance = np.sqrt(np.sum((rgb - background) ** 2, axis=2))
        mask = distance > threshold

    if not np.any(mask):
        raise ValueError(f"Nao foi possivel detectar a silhueta na imagem: {path}")

    rows, columns = np.where(mask)
    cropped = mask[rows.min() : rows.max() + 1, columns.min() : columns.max() + 1]
    return cropped


def _resize_mask(mask, shape):
    image = Image.fromarray((mask * 255).astype(np.uint8))
    resized = image.resize((shape[1], shape[0]), Image.Resampling.NEAREST)
    return np.asarray(resized) > 0


def _add_voxel_face(vertices, faces, vertex_ids, corners):
    face = []
    for corner in corners:
        if corner not in vertex_ids:
            vertex_ids[corner] = len(vertices)
            vertices.append(corner)
        face.append(vertex_ids[corner])
    faces.append((face[0], face[1], face[2]))
    faces.append((face[0], face[2], face[3]))


def _voxel_surface(occupancy, dimensions):
    nx, ny, nz = occupancy.shape
    width, depth, height = dimensions
    spacing = (width / nx, depth / ny, height / nz)
    origin = (-width / 2, -depth / 2, 0.0)
    vertices = []
    faces = []
    vertex_ids = {}

    for x, y, z in np.argwhere(occupancy):
        x0, x1 = x, x + 1
        y0, y1 = y, y + 1
        z0, z1 = z, z + 1

        if x == 0 or not occupancy[x - 1, y, z]:
            _add_voxel_face(vertices, faces, vertex_ids, ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)))
        if x == nx - 1 or not occupancy[x + 1, y, z]:
            _add_voxel_face(vertices, faces, vertex_ids, ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)))
        if y == 0 or not occupancy[x, y - 1, z]:
            _add_voxel_face(vertices, faces, vertex_ids, ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)))
        if y == ny - 1 or not occupancy[x, y + 1, z]:
            _add_voxel_face(vertices, faces, vertex_ids, ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)))
        if z == 0 or not occupancy[x, y, z - 1]:
            _add_voxel_face(vertices, faces, vertex_ids, ((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)))
        if z == nz - 1 or not occupancy[x, y, z + 1]:
            _add_voxel_face(vertices, faces, vertex_ids, ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)))

    vertices = np.asarray(vertices, dtype=float)
    vertices *= np.asarray(spacing)
    vertices += np.asarray(origin)
    mesh = trimesh.Trimesh(vertices=vertices, faces=np.asarray(faces), process=True)
    mesh.fix_normals()
    return mesh


def reconstruct_visual_hull(image_paths, width, depth, height, resolution=64, threshold=30):
    """Reconstrui um casco visual fechado; as imagens devem ser vistas ortograficas alinhadas."""
    if set(image_paths) != set(VIEW_NAMES):
        raise ValueError("Selecione uma imagem para cada uma das seis vistas.")
    if not all(float(value) > 0 for value in (width, depth, height)):
        raise ValueError("Largura, profundidade e altura devem ser maiores que zero.")
    if not 16 <= int(resolution) <= 128:
        raise ValueError("A resolucao deve estar entre 16 e 128 voxels na maior dimensao.")
    if not 1 <= int(threshold) <= 255:
        raise ValueError("O limiar de contraste deve estar entre 1 e 255.")

    width, depth, height = map(float, (width, depth, height))
    max_dimension = max(width, depth, height)
    nx = max(2, round(int(resolution) * width / max_dimension))
    ny = max(2, round(int(resolution) * depth / max_dimension))
    nz = max(2, round(int(resolution) * height / max_dimension))

    silhouettes = {
        name: _read_silhouette(image_paths[name], int(threshold))
        for name in VIEW_NAMES
    }

    front = _resize_mask(np.flipud(silhouettes["frente"]), (nz, nx))
    back = _resize_mask(np.flipud(np.fliplr(silhouettes["tras"])), (nz, nx))
    left = _resize_mask(np.flipud(np.fliplr(silhouettes["esquerda"])), (nz, ny))
    right = _resize_mask(np.flipud(silhouettes["direita"]), (nz, ny))
    top = _resize_mask(np.flipud(silhouettes["cima"]), (ny, nx))
    bottom = _resize_mask(np.fliplr(silhouettes["baixo"]), (ny, nx))

    occupancy = np.broadcast_to(front.T[:, None, :], (nx, ny, nz)).copy()
    occupancy &= np.broadcast_to(back.T[:, None, :], (nx, ny, nz))
    occupancy &= np.broadcast_to(left.T[None, :, :], (nx, ny, nz))
    occupancy &= np.broadcast_to(right.T[None, :, :], (nx, ny, nz))
    occupancy &= np.broadcast_to(top.T[:, :, None], (nx, ny, nz))
    occupancy &= np.broadcast_to(bottom.T[:, :, None], (nx, ny, nz))

    if not np.any(occupancy):
        raise ValueError(
            "As silhuetas nao se cruzam. Confira orientacao, enquadramento e dimensoes."
        )

    mesh = _voxel_surface(occupancy, (width, depth, height))
    if mesh.is_empty or not mesh.is_watertight:
        raise RuntimeError("A reconstrução gerou uma malha incompleta; revise as imagens.")
    return mesh, occupancy.shape
