"""SCION 03 Ernst · the person: a frock-coated mannequin of round cones (the magistrate of the plate), posed from the
score's circumstances.  Its head is a hybrid noun: while it commands, it wears the lion (a fragment pasted on in
fragments.py); when it sits and speaks softly, the lion has left for the keystone and its own plain head shows.

Local frame: F facing, Y up, S side.  Facing yaw psi: F = (cos psi, 0, sin psi); psi ~ 0 faces the porch (+x).
"""
import numpy as np
from sdf import cone, ellip
from dog import ik2, ell_axes, lerp

Y = np.array([0.0, 1.0, 0.0])
D2R = np.pi / 180


def frame(psi):
    F = np.array([np.cos(psi), 0.0, np.sin(psi)])
    S = np.cross(F, Y)
    return F, S


def build(q):
    """q: x, z, psi, sit (0..1), lean (rad), arm target 'hand' (world) or None, 'hand2' (world) or None, feet (world dict
    L/R), head_on (bool: draw own head), breath.  Returns prims, joints."""
    root = np.array([q['x'], 0.0, q['z']])
    F, S = frame(q['psi'])
    sit = q['sit']
    lean = q['lean']

    def W(v):
        return root + F * v[0] + Y * v[1] + S * v[2]

    prims = []; J = {}
    pel_h = lerp(0.95, 0.53, sit)
    pel = np.array([lerp(0.0, -0.05, sit), pel_h, 0.0])
    up = np.array([np.sin(lean), np.cos(lean), 0.0])
    chest = pel + up * 0.46
    neck = pel + up * 0.62
    head = pel + up * 0.76 + np.array([0.02, 0, 0])
    pel_w, chest_w, neck_w, head_w = W(pel), W(chest), W(neck), W(head)
    # legs: hips, knees by IK to the feet
    feet = q['feet']
    for k, side in (('L', 1), ('R', -1)):
        hip = W(pel + np.array([0.0, -0.05, 0.1 * side]))
        ft = np.asarray(feet[k], float)
        ankle = ft + Y * 0.08 - F * 0.05
        knee = ik2(hip, ankle, 0.46, 0.45, F + Y * 0.1)
        prims.append(cone('thigh' + k, hip, knee, 0.085, 0.065, 'cloth', F, k=0.03))
        prims.append(cone('shin' + k, knee, ankle, 0.06, 0.045, 'cloth', F, k=0.02))
        prims.append(cone('shoe' + k, ankle - F * 0.02 - Y * 0.04, ft + F * 0.12 + Y * 0.02, 0.05, 0.04, 'shoe', Y, k=0.02))
        J['knee' + k] = knee; J['foot' + k] = ft
    # the frock coat: chest barrel, a waist, the skirts to the knee (standing) or over the lap (sitting)
    ax = ell_axes(W(up) - root, F)
    prims.append(ellip('torso', chest_w, ax, (0.27, 0.2, 0.16), 'cloth2', k=0.0))
    prims.append(cone('waist', chest_w, pel_w, 0.17, 0.16, 'cloth2', F, k=0.06))
    hem_st = W(pel + np.array([-0.02, -0.42, 0]))
    hem_si = W(pel + np.array([0.36, -0.02, 0]))
    hem = lerp(hem_st, hem_si, sit)
    prims.append(cone('skirt', pel_w + Y * 0.05, hem, 0.17, lerp(0.22, 0.17, sit), 'cloth2', F, k=0.05))
    prims.append(cone('neck', neck_w - W(up) * 0 + (root * 0), head_w, 0.055, 0.05, 'skin', F, k=0.02))
    prims.append(cone('collar', W(pel + up * 0.585 + np.array([0.03, 0, 0])), W(pel + up * 0.585 + np.array([0.09, -0.05, 0])), 0.06, 0.03, 'shirt', Y, k=0.02))
    if q.get('head_on', True):
        hax = ell_axes(F * np.cos(q.get('nod', 0.0)) - Y * np.sin(q.get('nod', 0.0)), Y)
        prims.append(ellip('head', head_w, hax, (0.105, 0.125, 0.095), 'skin', k=0.02))
        prims.append(ellip('hair', head_w + Y * 0.045 - F * 0.025, hax, (0.11, 0.095, 0.1), 'hair', k=0.01))
        prims.append(ellip('nose', head_w + F * 0.1 + Y * 0.0, hax, (0.03, 0.035, 0.02), 'skin', k=0.012))
        prims.append(ellip('eye', head_w + F * 0.085 + Y * 0.025 + S * 0.035, hax, (0.012, 0.01, 0.012), 'eye', k=0.002))
    J['head'] = head_w; J['neck'] = neck_w; J['chest'] = chest_w; J['pelvis'] = pel_w; J['F'] = F; J['S'] = S
    # arms
    for k, side in (('R', -1), ('L', 1)):
        sh = W(pel + up * 0.56 + np.array([0.0, 0, 0.2 * side]))
        tgt = q.get('hand' if k == 'R' else 'hand2')
        if tgt is None:
            tgt = W(pel + np.array([0.06 + 0.25 * sit, 0.02 + 0.12 * sit, 0.23 * side]))
        tgt = np.asarray(tgt, float)
        el = ik2(sh, tgt, 0.31, 0.29, -F * 0.6 - Y * 0.5 + S * side * 0.6)
        prims.append(cone('uarm' + k, sh, el, 0.065, 0.05, 'cloth2', F, k=0.03))
        prims.append(cone('farm' + k, el, tgt, 0.05, 0.04, 'cloth2', F, k=0.02))
        if q.get('hands_on', {}).get(k, True):
            hd = tgt + (tgt - el) / max(np.linalg.norm(tgt - el), 1e-6) * 0.06
            prims.append(ellip('hand' + k, hd, ell_axes(tgt - el, Y), (0.065, 0.04, 0.025), 'skin', k=0.02))
        J['sh' + k] = sh; J['el' + k] = el; J['hand' + k] = tgt
    return prims, J
