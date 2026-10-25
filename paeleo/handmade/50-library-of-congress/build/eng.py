"""Engraving primitives for the print stage: line screens whose width follows tone, cross-hatch, contour bands.
All arrays are float32 in [0,1]; ink = 1 means fully inked."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def blur(a, r):
    if r <= 0: return a
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255.

def blurf(a, r):
    """float-preserving blur via 16-bit trick (two 8-bit passes)"""
    hi = np.floor(np.clip(a, 0, 1) * 255) / 255.
    lo = (np.clip(a, 0, 1) - hi) * 255
    return blur(hi, r) + blur(lo, r) / 255.

def screen(tone, angle_deg, period, warp=None, warp_amp=0.0, aa=0.9, ox=0.0, oy=0.0):
    """classic line engraving: parallel lines whose half-width is proportional to tone."""
    h, w = tone.shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.deg2rad(angle_deg)
    u = ((x + ox) * np.cos(a) + (y + oy) * np.sin(a)) / period
    if warp is not None: u = u + warp_amp * warp
    dist = np.abs(u - np.floor(u) - 0.5) * period  # px from the line centre
    half = np.clip(tone, 0, 1) * period * 0.5
    return np.clip((half - dist) / aa + 0.5, 0, 1) * (tone > 0.02)

def engrave(tone, angle=-20, period=3.4, warp_amp=1.2, cross=0.55, cross_angle=None, aa=0.9, ox=0, oy=0):
    """tone → ink, with lines that bend over the form (warp from the blurred tone) and a cross-hatch in the darks"""
    warp = blurf(tone, 2.5)
    ink = screen(tone, angle, period, warp, warp_amp, aa, ox, oy)
    if cross is not None and cross < 1:
        t2 = np.clip((tone - cross) / (1 - cross), 0, 1)
        ca = angle + 62 if cross_angle is None else cross_angle
        ink = np.maximum(ink, screen(t2 * 0.85, ca, period * 1.05, warp, warp_amp * 0.6, aa, ox, oy))
    return ink

def poly_mask(shape, polys, scale=1.0, off=(0, 0)):
    h, w = shape
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    for P in polys:
        d.polygon([((p[0] - off[0]) * scale, (p[1] - off[1]) * scale) for p in P], fill=255)
    return np.asarray(im, np.float32) / 255.

def dilate(m, r):
    im = Image.fromarray((m > 0.5).astype(np.uint8) * 255)
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * r + 1)), np.float32) / 255.

def erode(m, r):
    im = Image.fromarray((m > 0.5).astype(np.uint8) * 255)
    return np.asarray(im.filter(ImageFilter.MinFilter(2 * r + 1)), np.float32) / 255.

def soft_mask(m, r=1.0):
    return np.clip(blur(m, r) * 1.0, 0, 1)

def contour(m, width=2.0):
    """an engraved outline band just inside the silhouette (anti-aliased)"""
    sm = blur(m, 0.8)
    inner = blur(erode(m, max(1, int(round(width)))), 0.8)
    return np.clip(sm - inner, 0, 1)

def stipple(tone, density=0.35, seed=0):
    rng = np.random.default_rng(seed)
    return (rng.random(tone.shape) < tone * density).astype(np.float32)
