#!/usr/bin/env python3
"""
ALLWAYS Handmade Film Production Engine (v2 — Critic-Verified & Cut-Free)
Manually crafts and renders films across:
  - Series A: SCION 055–065 (11 Conceptual Microfilms)
  - Series B: B-ROLL OF CIVILIZATION (12 ALLWAYS Proposed Works)
  - Series C: SCION 066–074 (Structural & Found-Footage Cinema)
  - Series D: SCION 075–082 (Observational & Collective Documentaries)
  - Series E: SCION 083–094 (Framing, Gesture, City Rhythms & Video Essays)
  - Series F: SCION 095–113 (Interactive & Database Cinema Proofs)

v2 Upgrades after Independent SCION Critic Tribunal Audit:
  1. Automatic Cut-Free Window Clamping via `forage/clip_clean_windows.json` so no
     segment ever crosses an internal montage cut inside an archival .mp4.
  2. Unicode glyph sanitization (`→` -> `->`, `×` -> `x`) eliminating all `□` boxes.
  3. Exact EDL timecode synchronization (`start_sec`, `end_sec`) including Opening
     and Closing cards + embedded `critic_tribunal` records in every manifest.
  4. Upgraded visual operators:
     - `circle_reg` with `anchor_xy` translation so off-center circles lock to (640, 352)
     - `reframe` (`tight`, `tight_to_wide`, `wide`) for single-source social geometry (SCION 060)
     - `erasure` with background plate + Telea inpainting so moving figures truly vanish (BROLL 01)
     - `triptych` for 3-panel synchronized rhythms (BROLL 06, SCION 066–113)
     - `scale_powers`, `nostalgia_offset`, `clock_sync`, `interactive_state` for SCION 066–113
"""

import json
import math
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

STUDIO_DIR = Path("/Users/gaia/WORLDBUILDING-TERMS/allways_studio")
FORAGE_DIR = STUDIO_DIR / "forage"
CLIPS_DIR = STUDIO_DIR / "clips"
FILMS_DIR = STUDIO_DIR / "films"
MANIFESTS_DIR = STUDIO_DIR / "manifests"

FILMS_DIR.mkdir(parents=True, exist_ok=True)
MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720
FPS = 24
SR = 44100

# Load fonts
FONT_SERIF_PATH = "/System/Library/Fonts/Supplemental/Georgia.ttf"
FONT_SERIF_BOLD_PATH = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
FONT_SERIF_ITALIC_PATH = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
FONT_MONO_PATH = "/System/Library/Fonts/Menlo.ttc"

FONT_TITLE = ImageFont.truetype(FONT_SERIF_PATH, 42)
FONT_SUBTITLE = ImageFont.truetype(FONT_SERIF_ITALIC_PATH, 22)
FONT_BODY = ImageFont.truetype(FONT_SERIF_PATH, 21)
FONT_CAPTION = ImageFont.truetype(FONT_SERIF_PATH, 23)
FONT_MONO_SM = ImageFont.truetype(FONT_MONO_PATH, 13)
FONT_MONO_MD = ImageFont.truetype(FONT_MONO_PATH, 15)
FONT_MONO_LG = ImageFont.truetype(FONT_MONO_PATH, 18)

# ALLWAYS palette
COL_BG = (17, 21, 19)        # #111513
COL_PANEL = (25, 32, 28)     # #19201c
COL_PAPER = (240, 234, 220)  # #f0eadc
COL_MUTED = (190, 197, 186)  # #bec5ba
COL_MINT = (167, 206, 186)   # #a7ceba
COL_GOLD = (223, 204, 157)   # #dfcc9d
COL_RUST = (231, 157, 123)   # #e79d7b
COL_LINE = (59, 71, 61)      # #3b473d

# Load metadata pool & clean windows
POOL_META = json.load(open(FORAGE_DIR / "candidate_pool_metadata.json"))
TRANSCRIPTS = json.load(open(FORAGE_DIR / "cineosis_transcripts.json"))
CLEAN_WINDOWS_PATH = FORAGE_DIR / "clip_clean_windows.json"
CLEAN_WINDOWS = json.load(open(CLEAN_WINDOWS_PATH)) if CLEAN_WINDOWS_PATH.exists() else {}


def sanitize_text(s: str) -> str:
    if not s:
        return ""
    return (
        str(s)
        .replace("\u2192", "->")
        .replace("\u2190", "<-")
        .replace("\u2194", "<->")
        .replace("\u00d7", "x")
        .replace("\u2212", "-")
    )


def resolve_clip(prefix: str) -> dict:
    for cid, meta in POOL_META.items():
        if cid.startswith(prefix):
            mp4_path = CLIPS_DIR / f"{cid}.mp4"
            if mp4_path.exists():
                return {**meta, "path": str(mp4_path)}
    for p in CLIPS_DIR.glob(f"{prefix}*.mp4"):
        cid = p.stem
        meta = POOL_META.get(cid, {"id": cid, "title": "Archival Record", "year": None})
        return {**meta, "path": str(p)}
    raise FileNotFoundError(f"Could not resolve clip prefix: {prefix}")


def get_cut_free_window(clip_path: str, req_in: float, req_dur: float, custom_window: bool = False) -> tuple:
    """
    Returns (safe_in, safe_out) guaranteed not to cross any internal cut detected in
    clip_clean_windows.json unless custom_window=True.
    """
    cid = Path(clip_path).stem
    info = CLEAN_WINDOWS.get(cid)
    if not info:
        return req_in, req_in + req_dur

    src_dur = float(info.get("duration", req_in + req_dur))
    if custom_window:
        safe_in = max(0.05, min(req_in, max(0.05, src_dur - 0.5)))
        safe_out = min(src_dur - 0.05, safe_in + req_dur)
        return safe_in, max(safe_in + 0.2, safe_out)

    windows = info.get("windows", [])
    if not windows:
        cin = float(info.get("clean_in", 0.05))
        cout = float(info.get("clean_out", src_dur - 0.05))
        windows = [{"in": cin, "out": cout, "dur": max(0.1, cout - cin)}]

    # Check if requested [req_in, req_in + req_dur] fits inside any single cut-free window
    for w in windows:
        win_in = float(w["in"])
        win_out = float(w["out"])
        if req_in >= win_in - 0.15 and (req_in + req_dur) <= win_out + 0.15:
            s_in = max(win_in + 0.04, min(req_in, win_out - 0.25))
            s_out = min(win_out - 0.04, s_in + req_dur)
            return s_in, max(s_in + 0.2, s_out)

    # Otherwise check if any window contains req_in and has >= max(3.5, req_dur * 0.85)
    for w in windows:
        win_in = float(w["in"])
        win_out = float(w["out"])
        if win_in - 0.2 <= req_in <= win_out - 1.5 and (win_out - win_in) >= max(3.5, req_dur * 0.85):
            s_in = max(win_in + 0.04, min(req_in, win_out - min(req_dur, win_out - win_in - 0.08)))
            s_out = min(win_out - 0.04, s_in + req_dur)
            return s_in, max(s_in + 0.2, s_out)

    # Fallback: use the longest clean window in the clip
    best_w = max(windows, key=lambda x: float(x["dur"]))
    win_in = float(best_w["in"])
    win_out = float(best_w["out"])
    if win_in <= req_in <= win_out - 1.2:
        s_in = max(win_in + 0.04, req_in)
    else:
        s_in = win_in + 0.04
    s_out = min(win_out - 0.04, s_in + req_dur)
    return s_in, max(s_in + 0.2, s_out)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list:
    text = sanitize_text(text)
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test = " ".join(cur + [w])
        bbox = font.getbbox(test)
        if (bbox[2] - bbox[0]) <= max_w or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def render_card_frame(
    kicker: str,
    title: str,
    subtitle: str,
    body: str,
    footer: str = "ALLWAYS · PAELEO / SCION · NEARMATCH",
    accent: tuple = COL_MINT,
) -> np.ndarray:
    kicker = sanitize_text(kicker)
    title = sanitize_text(title)
    subtitle = sanitize_text(subtitle)
    body = sanitize_text(body)
    footer = sanitize_text(footer)

    img = Image.new("RGB", (W, H), COL_BG)
    dr = ImageDraw.Draw(img)
    dr.rectangle([48, 44, W - 48, H - 44], outline=COL_LINE, width=1)
    dr.line([80, 110, W - 80, 110], fill=COL_LINE, width=1)
    dr.text((80, 74), kicker.upper(), font=FONT_MONO_MD, fill=accent)
    dr.text((80, 136), title, font=FONT_TITLE, fill=COL_PAPER)
    if subtitle:
        dr.text((80, 194), subtitle, font=FONT_SUBTITLE, fill=COL_GOLD)
    y = 248 if subtitle else 210
    for paragraph in body.split("\n"):
        if not paragraph.strip():
            y += 14
            continue
        for line in wrap_text(paragraph, FONT_BODY, W - 180):
            if y < H - 125:
                dr.text((80, y), line, font=FONT_BODY, fill=COL_MUTED)
                y += 30
    dr.line([80, H - 96, W - 80, H - 96], fill=COL_LINE, width=1)
    dr.text((80, H - 78), footer, font=FONT_MONO_SM, fill=COL_MUTED)
    return np.array(img, dtype=np.uint8)


def fit_frame(bgr: np.ndarray, target_w: int, target_h: int, crop_mode: str = "contain", crop_box: list = None) -> np.ndarray:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    sh, sw = rgb.shape[:2]
    if sh == 0 or sw == 0:
        return np.zeros((target_h, target_w, 3), dtype=np.uint8)
    if crop_box and len(crop_box) == 4:
        # [x0_frac, y0_frac, x1_frac, y1_frac]
        x0 = max(0, min(sw - 2, int(crop_box[0] * sw)))
        y0 = max(0, min(sh - 2, int(crop_box[1] * sh)))
        x1 = max(x0 + 2, min(sw, int(crop_box[2] * sw)))
        y1 = max(y0 + 2, min(sh, int(crop_box[3] * sh)))
        rgb = rgb[y0:y1, x0:x1]
        sh, sw = rgb.shape[:2]

    if crop_mode == "cover":
        scale = max(target_w / sw, target_h / sh)
        nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
        resized = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)
        x0 = (nw - target_w) // 2
        y0 = (nh - target_h) // 2
        return resized[y0 : y0 + target_h, x0 : x0 + target_w]
    else:
        scale = min(target_w / sw, target_h / sh)
        nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
        resized = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)
        canvas = np.full((target_h, target_w, 3), 12, dtype=np.uint8)
        x0 = (target_w - nw) // 2
        y0 = (target_h - nh) // 2
        canvas[y0 : y0 + nh, x0 : x0 + nw] = resized
        return canvas


def read_clip_frames(
    clip_path: str,
    in_s: float,
    dur_s: float,
    target_w: int,
    target_h: int,
    crop_mode: str = "contain",
    custom_window: bool = False,
    crop_box: list = None,
) -> list:
    n_frames = max(1, int(round(dur_s * FPS)))
    safe_in, safe_out = get_cut_free_window(clip_path, in_s, dur_s, custom_window=custom_window)
    avail_dur = max(0.15, safe_out - safe_in)

    cap = cv2.VideoCapture(clip_path)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_src = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1)

    frames = []
    last_valid = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    prev_idx = -1
    for i in range(n_frames):
        frac = i / max(1, n_frames - 1)
        # Map cleanly inside [safe_in, safe_out] so we never cross a cut
        play_span = min(dur_s, avail_dur)
        t = safe_in + frac * play_span
        frame_idx = int(round(t * src_fps))
        frame_idx = max(0, min(total_src - 1, frame_idx))
        if frame_idx != prev_idx:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, bgr = cap.read()
            if ok and bgr is not None:
                last_valid = fit_frame(bgr, target_w, target_h, crop_mode=crop_mode, crop_box=crop_box)
            prev_idx = frame_idx
        frames.append(last_valid.copy())
    cap.release()
    return frames


def add_hud_overlay(
    rgb: np.ndarray,
    top_left: str = "",
    top_right: str = "",
    bottom_left: str = "",
    bottom_right: str = "",
    center_caption: str = "",
    accent: tuple = COL_MINT,
) -> np.ndarray:
    top_left = sanitize_text(top_left)
    top_right = sanitize_text(top_right)
    bottom_left = sanitize_text(bottom_left)
    bottom_right = sanitize_text(bottom_right)
    center_caption = sanitize_text(center_caption)

    im = Image.fromarray(rgb)
    dr = ImageDraw.Draw(im, "RGBA")
    if top_left or top_right:
        dr.rectangle([0, 0, W, 36], fill=(11, 14, 12, 205))
        if top_left:
            dr.text((18, 9), top_left, font=FONT_MONO_SM, fill=accent)
        if top_right:
            bbox = FONT_MONO_SM.getbbox(top_right)
            tw = bbox[2] - bbox[0]
            dr.text((W - tw - 18, 9), top_right, font=FONT_MONO_SM, fill=COL_MUTED)
    if bottom_left or bottom_right:
        dr.rectangle([0, H - 52, W, H], fill=(11, 14, 12, 220))
        if bottom_left:
            dr.text((18, H - 36), bottom_left[:96], font=FONT_MONO_MD, fill=COL_PAPER)
        if bottom_right:
            bbox = FONT_MONO_SM.getbbox(bottom_right)
            tw = bbox[2] - bbox[0]
            dr.text((W - tw - 18, H - 34), bottom_right, font=FONT_MONO_SM, fill=COL_GOLD)
    if center_caption:
        bbox = FONT_CAPTION.getbbox(center_caption)
        cw = bbox[2] - bbox[0]
        dr.rectangle([(W - cw) // 2 - 18, H - 106, (W + cw) // 2 + 18, H - 60], fill=(17, 21, 19, 232), outline=COL_GOLD)
        dr.text(((W - cw) // 2, H - 96), center_caption, font=FONT_CAPTION, fill=COL_PAPER)
    return np.array(im, dtype=np.uint8)


def extract_clip_audio(clip_path: str, in_s: float, dur_s: float) -> np.ndarray:
    n_samples = int(round(dur_s * SR))
    if n_samples <= 0:
        return np.zeros((0, 2), dtype=np.float32)
    safe_in, safe_out = get_cut_free_window(clip_path, in_s, dur_s)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_wav = tmp.name
    try:
        cmd = [
            "ffmpeg", "-y", "-ss", f"{safe_in:.3f}", "-t", f"{dur_s:.3f}",
            "-i", clip_path, "-vn", "-ac", "2", "-ar", str(SR),
            "-acodec", "pcm_s16le", tmp_wav,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        if os.path.exists(tmp_wav) and os.path.getsize(tmp_wav) > 100:
            with wave.open(tmp_wav, "rb") as wf:
                raw = wf.readframes(wf.getnframes())
                arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                if wf.getnchannels() == 2:
                    arr = arr.reshape(-1, 2)
                else:
                    arr = np.column_stack([arr, arr])
                if len(arr) < n_samples:
                    pad = np.zeros((n_samples - len(arr), 2), dtype=np.float32)
                    arr = np.vstack([arr, pad])
                else:
                    arr = arr[:n_samples]
                return arr
    except Exception:
        pass
    finally:
        if os.path.exists(tmp_wav):
            try:
                os.unlink(tmp_wav)
            except OSError:
                pass
    return np.zeros((n_samples, 2), dtype=np.float32)


def synth_room_tone_and_foley(dur_s: float, kind: str = "room", seed: int = 42, freq: float = 180.0) -> np.ndarray:
    n = int(round(dur_s * SR))
    if n <= 0:
        return np.zeros((0, 2), dtype=np.float32)
    rng = np.random.default_rng(seed)
    t = np.linspace(0, dur_s, n, endpoint=False, dtype=np.float32)
    brown = np.cumsum(rng.normal(0, 0.0018, n).astype(np.float32))
    brown = brown - np.linspace(brown[0], brown[-1], n, dtype=np.float32)
    max_b = np.max(np.abs(brown)) or 1.0
    room = (brown / max_b) * 0.015

    sig = room.copy()
    if kind == "tap":
        env1 = np.exp(-t * 28.0) * np.sin(2 * np.pi * freq * t)
        sig += 0.14 * env1
    elif kind == "pulse":
        pulse_env = 0.5 * (1.0 + np.sin(2 * np.pi * 2.0 * t)) ** 4
        sig += 0.06 * pulse_env * np.sin(2 * np.pi * freq * t)
    elif kind == "projector":
        sprocket = 0.025 * (0.5 + 0.5 * np.sin(2 * np.pi * 24.0 * t)) * rng.normal(0, 1.0, n).astype(np.float32)
        sig += sprocket
    elif kind == "breath":
        swell = np.sin(np.pi * np.clip(t / max(dur_s, 0.1), 0, 1)) ** 2
        air = rng.normal(0, 0.018, n).astype(np.float32) * swell
        sig += air

    fade = min(int(0.04 * SR), n // 4)
    if fade > 0:
        sig[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        sig[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    return np.column_stack([sig, sig])


def mix_shot_audio(clip_path: str, in_s: float, dur_s: float, foley_kind: str = "room", seed: int = 42, freq: float = 180.0, mute_source: bool = False) -> np.ndarray:
    foley = synth_room_tone_and_foley(dur_s, kind=foley_kind, seed=seed, freq=freq)
    if mute_source or not clip_path:
        return foley
    src = extract_clip_audio(clip_path, in_s, dur_s)
    rms = float(np.sqrt(np.mean(src ** 2))) if len(src) else 0.0
    if rms > 0.002:
        gain = min(2.5, 0.14 / max(rms, 0.01))
        mixed = np.clip(src * gain + foley * 0.4, -0.95, 0.95)
    else:
        mixed = foley
    fade = min(int(0.04 * SR), len(mixed) // 4)
    if fade > 0:
        mixed[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)[:, None]
        mixed[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]
    return mixed


def encode_film(frames: list, audio_chunks: list, out_mp4: Path):
    full_audio = np.vstack(audio_chunks) if audio_chunks else np.zeros((int(len(frames) / FPS * SR), 2), dtype=np.float32)
    target_samples = int(round((len(frames) / FPS) * SR))
    if len(full_audio) < target_samples:
        full_audio = np.vstack([full_audio, np.zeros((target_samples - len(full_audio), 2), dtype=np.float32)])
    else:
        full_audio = full_audio[:target_samples]

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_w:
        wav_path = tmp_w.name
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        pcm = np.clip(full_audio * 32767.0, -32768, 32767).astype(np.int16)
        wf.writeframes(pcm.tobytes())

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "-",
        "-i", wav_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "12", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest",
        str(out_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for fr in frames:
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    proc.wait()
    if os.path.exists(wav_path):
        os.unlink(wav_path)


def build_standard_shot(seg: dict, show_hud: bool = True) -> tuple:
    c = resolve_clip(seg["clip"])
    dur = float(seg["dur"])
    in_s = float(seg.get("in_s", 0.5))
    custom_win = bool(seg.get("custom_window", False))
    crop_box = seg.get("crop_box", None)
    safe_in, safe_out = get_cut_free_window(c["path"], in_s, dur, custom_window=custom_win)
    raw_frames = read_clip_frames(
        c["path"], in_s, dur, W, H,
        crop_mode=seg.get("crop", "contain"),
        custom_window=custom_win,
        crop_box=crop_box,
    )
    src_tag = f"SOURCE: {c['id'][:8]} · {c.get('title') or 'Archive'} ({c.get('year') or 'undated'})"
    out_frames = []
    for fr in raw_frames:
        if show_hud:
            fr = add_hud_overlay(
                fr,
                top_left=seg.get("phase", ""),
                top_right=src_tag,
                bottom_left=seg.get("action", ""),
                bottom_right=seg.get("nearmatch", ""),
                center_caption=seg.get("caption", ""),
            )
        elif seg.get("caption"):
            fr = add_hud_overlay(fr, center_caption=seg["caption"])
        out_frames.append(fr)
    aud = mix_shot_audio(
        c["path"], safe_in, dur,
        foley_kind=seg.get("foley", "room"),
        seed=abs(hash(c["id"])) % 10000,
        freq=float(seg.get("freq", 180.0)),
        mute_source=bool(seg.get("mute_source", False)),
    )
    meta_entry = {
        "type": "shot",
        "clip_id": c["id"],
        "source_title": c.get("title"),
        "source_year": c.get("year"),
        "source_page": c.get("page"),
        "in_s": round(safe_in, 2),
        "out_s": round(safe_out, 2),
        "dur_s": dur,
        "phase": sanitize_text(seg.get("phase", "")),
        "action": sanitize_text(seg.get("action", "")),
        "nearmatch": sanitize_text(seg.get("nearmatch", "")),
    }
    return out_frames, aud, meta_entry


def build_reframe_shot(seg: dict) -> tuple:
    """
    For SCION 060 (Losers — Social Position Through Montage) & SCION 068 (Powers of Ten):
    Extracts tight-cropped vs wide-context views from the EXACT SAME continuous archival
    recording so the viewer sees how widening the frame redistributes social/spatial meaning.
    """
    c = resolve_clip(seg["clip"])
    dur = float(seg["dur"])
    in_s = float(seg.get("in_s", 0.5))
    custom_win = bool(seg.get("custom_window", False))
    reframe_mode = seg.get("reframe_mode", "tight")  # tight, tight_to_wide, wide, wide_to_tight
    rect = seg.get("focus_rect", [0.04, 0.14, 0.44, 0.88])  # [x0, y0, x1, y1] in normalized coords

    base_frames = read_clip_frames(c["path"], in_s, dur, W, H, crop_mode="cover", custom_window=custom_win)
    n = len(base_frames)
    out_frames = []
    for i, fr in enumerate(base_frames):
        p = i / max(1, n - 1)
        # Smooth cosine easing
        ease = 0.5 - 0.5 * math.cos(math.pi * p)
        if reframe_mode == "tight":
            t_blend = 0.0
        elif reframe_mode == "wide":
            t_blend = 1.0
        elif reframe_mode == "tight_to_wide":
            t_blend = ease
        else:  # wide_to_tight
            t_blend = 1.0 - ease

        x0 = int((rect[0] * (1.0 - t_blend) + 0.0 * t_blend) * W)
        y0 = int((rect[1] * (1.0 - t_blend) + 0.0 * t_blend) * H)
        x1 = int((rect[2] * (1.0 - t_blend) + 1.0 * t_blend) * W)
        y1 = int((rect[3] * (1.0 - t_blend) + 1.0 * t_blend) * H)
        x0, y0 = max(0, min(W - 16, x0)), max(0, min(H - 16, y0))
        x1, y1 = max(x0 + 16, min(W, x1)), max(y0 + 16, min(H, y1))

        cropped = fr[y0:y1, x0:x1]
        canvas = cv2.resize(cropped, (W, H), interpolation=cv2.INTER_LINEAR)

        # In wide or widening mode, draw a subtle mint frame showing where the tight crop was
        if t_blend > 0.25:
            bx0, by0 = int(rect[0] * W), int(rect[1] * H)
            bx1, by1 = int(rect[2] * W), int(rect[3] * H)
            cv2.rectangle(canvas, (bx0, by0), (bx1, by1), COL_MINT, 2, lineType=cv2.LINE_AA)

        src_tag = f"SOURCE: {c['id'][:8]} · {c.get('title') or 'Archive'} ({c.get('year') or 'undated'})"
        canvas = add_hud_overlay(
            canvas,
            top_left=seg.get("phase", f"REFRAME: {reframe_mode.upper()}"),
            top_right=src_tag,
            bottom_left=seg.get("action", ""),
            bottom_right=seg.get("nearmatch", f"SAME SOURCE RECORD · {reframe_mode.upper()}"),
        )
        out_frames.append(canvas)

    aud = mix_shot_audio(c["path"], in_s, dur, foley_kind="room")
    return out_frames, aud, {
        "type": "reframe_shot",
        "clip_id": c["id"],
        "source_title": c.get("title"),
        "source_year": c.get("year"),
        "source_page": c.get("page"),
        "reframe_mode": reframe_mode,
        "dur_s": dur,
        "phase": sanitize_text(seg.get("phase", "")),
        "action": sanitize_text(seg.get("action", "")),
        "nearmatch": sanitize_text(seg.get("nearmatch", "")),
    }


def build_split_shot(seg: dict) -> tuple:
    ca = resolve_clip(seg["clip_a"])
    cb = resolve_clip(seg["clip_b"])
    dur = float(seg["dur"])
    in_a = float(seg.get("in_a", 0.5))
    in_b = float(seg.get("in_b", 0.5))
    hold_a_at = float(seg.get("hold_a_at", dur))
    hold_b_at = float(seg.get("hold_b_at", dur))

    half_w = W // 2 - 2
    panel_h = H - 88
    fa_list = read_clip_frames(ca["path"], in_a, dur, half_w, panel_h, crop_mode="cover", custom_window=bool(seg.get("custom_window_a", False)))
    fb_list = read_clip_frames(cb["path"], in_b, dur, half_w, panel_h, crop_mode="cover", custom_window=bool(seg.get("custom_window_b", False)))

    hold_a_idx = min(len(fa_list) - 1, max(0, int(hold_a_at * FPS)))
    hold_b_idx = min(len(fb_list) - 1, max(0, int(hold_b_at * FPS)))

    out_frames = []
    for i in range(len(fa_list)):
        canvas = np.full((H, W, 3), 14, dtype=np.uint8)
        pa = fa_list[min(i, hold_a_idx)]
        pb = fb_list[min(i, hold_b_idx)]
        canvas[36 : 36 + panel_h, 0:half_w] = pa
        canvas[36 : 36 + panel_h, W - half_w : W] = pb
        canvas[36 : 36 + panel_h, half_w : W - half_w] = COL_GOLD
        lbl_a = f"L: {ca['id'][:8]} · {(ca.get('title') or '')[:24]} ({ca.get('year') or 'undated'})"
        lbl_b = f"R: {cb['id'][:8]} · {(cb.get('title') or '')[:24]} ({cb.get('year') or 'undated'})"
        canvas = add_hud_overlay(
            canvas,
            top_left=lbl_a,
            top_right=lbl_b,
            bottom_left=seg.get("action", ""),
            bottom_right=seg.get("nearmatch", "NEARMATCH SPLIT"),
        )
        out_frames.append(canvas)

    aud_a = mix_shot_audio(ca["path"], in_a, dur, foley_kind="room", seed=101)
    aud_b = mix_shot_audio(cb["path"], in_b, dur, foley_kind="room", seed=202)
    if hold_a_at < dur:
        cut_s = int(hold_a_at * SR)
        aud_a[cut_s:] *= 0.15
    if hold_b_at < dur:
        cut_s = int(hold_b_at * SR)
        aud_b[cut_s:] *= 0.15
    stereo = np.column_stack([aud_a[:, 0] * 0.85, aud_b[:, 1] * 0.85])
    meta_entry = {
        "type": "split_shot",
        "clip_a": {"id": ca["id"], "title": ca.get("title"), "year": ca.get("year"), "page": ca.get("page")},
        "clip_b": {"id": cb["id"], "title": cb.get("title"), "year": cb.get("year"), "page": cb.get("page")},
        "dur_s": dur,
        "phase": sanitize_text(seg.get("phase", "SPLIT COMPARISON")),
        "action": sanitize_text(seg.get("action", "")),
        "nearmatch": sanitize_text(seg.get("nearmatch", "")),
    }
    return out_frames, stereo, meta_entry


def build_triptych_shot(seg: dict) -> tuple:
    """
    Synchronized 3-panel triptych (e.g. BROLL 06 Kinetic 3-workshop lock, or SCION 066/078/095).
    """
    clips = [resolve_clip(p) for p in seg["clips"][:3]]
    in_list = seg.get("in_list", [0.5, 0.5, 0.5])
    dur = float(seg["dur"])
    pw = W // 3 - 4
    ph = H - 92
    panel_frames = [
        read_clip_frames(c["path"], float(in_list[idx] if idx < len(in_list) else 0.5), dur, pw, ph, crop_mode="cover")
        for idx, c in enumerate(clips)
    ]
    n = len(panel_frames[0])
    out_frames = []
    for i in range(n):
        canvas = np.full((H, W, 3), 14, dtype=np.uint8)
        for idx in range(len(clips)):
            x0 = 2 + idx * (W // 3)
            canvas[38 : 38 + ph, x0 : x0 + pw] = panel_frames[idx][min(i, len(panel_frames[idx]) - 1)]
            if idx > 0:
                canvas[38 : 38 + ph, x0 - 2 : x0] = COL_GOLD
        canvas = add_hud_overlay(
            canvas,
            top_left=seg.get("phase", "SYNCHRONIZED TRIPTYCH"),
            top_right=" | ".join(f"{c['id'][:6]}({c.get('year') or '?'})" for c in clips),
            bottom_left=seg.get("action", ""),
            bottom_right=seg.get("nearmatch", "THREE-STREAM COORDINATION"),
        )
        out_frames.append(canvas)

    aud = mix_shot_audio(clips[0]["path"], float(in_list[0]), dur, foley_kind=seg.get("foley", "pulse"), freq=float(seg.get("freq", 220.0)))
    return out_frames, aud, {
        "type": "triptych_shot",
        "clips": [{"id": c["id"], "title": c.get("title"), "year": c.get("year")} for c in clips],
        "dur_s": dur,
        "phase": sanitize_text(seg.get("phase", "")),
        "action": sanitize_text(seg.get("action", "")),
        "nearmatch": sanitize_text(seg.get("nearmatch", "")),
    }


def build_circle_reg_shot(seg: dict) -> tuple:
    c = resolve_clip(seg["clip"])
    dur = float(seg["dur"])
    in_s = float(seg.get("in_s", 0.5))
    reg_mode = seg.get("reg_mode", "locked")  # locked, irregular_release, exit, unregistered
    anchor_xy = seg.get("anchor_xy", [0.5, 0.5])  # normalized (cx, cy) of circular object in source frame
    custom_win = bool(seg.get("custom_window", False))
    raw_frames = read_clip_frames(c["path"], in_s, dur, W, H, crop_mode="cover", custom_window=custom_win)
    out_frames = []
    n = len(raw_frames)
    target_cx, target_cy = W // 2, H // 2 - 8

    for i, fr in enumerate(raw_frames):
        p = i / max(1, n - 1)
        # First shift source anchor_xy to (target_cx, target_cy)
        src_cx = int(anchor_xy[0] * W)
        src_cy = int(anchor_xy[1] * H)
        shift_x = target_cx - src_cx
        shift_y = target_cy - src_cy
        if abs(shift_x) > 4 or abs(shift_y) > 4:
            M_shift = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            fr_centered = cv2.warpAffine(fr, M_shift, (W, H), borderMode=cv2.BORDER_REFLECT_101)
        else:
            fr_centered = fr

        if reg_mode == "locked":
            zoom = float(seg.get("zoom", 1.18))
            zw, zh = int(W * zoom), int(H * zoom)
            zfr = cv2.resize(fr_centered, (zw, zh), interpolation=cv2.INTER_LINEAR)
            x0, y0 = (zw - W) // 2, (zh - H) // 2
            canvas = zfr[y0 : y0 + H, x0 : x0 + W].copy()
            cv2.circle(canvas, (target_cx, target_cy), 185, COL_MINT, 2, lineType=cv2.LINE_AA)
            cv2.circle(canvas, (target_cx, target_cy), 4, COL_GOLD, -1, lineType=cv2.LINE_AA)
        elif reg_mode == "irregular_release":
            zoom = 1.24 - 0.24 * p
            zw, zh = int(W * zoom), int(H * zoom)
            zfr = cv2.resize(fr_centered, (zw, zh), interpolation=cv2.INTER_LINEAR)
            x0, y0 = (zw - W) // 2, (zh - H) // 2
            canvas = zfr[y0 : y0 + H, x0 : x0 + W].copy()
            cv2.circle(canvas, (target_cx, target_cy), int(185 / zoom), COL_RUST, 2, lineType=cv2.LINE_AA)
        elif reg_mode == "exit":
            dx = int(p * 340)
            M = np.float32([[1, 0, dx], [0, 1, 0]])
            canvas = cv2.warpAffine(fr_centered, M, (W, H), borderValue=(15, 18, 16))
            cv2.circle(canvas, (target_cx + dx, target_cy), 185, COL_GOLD, 2, lineType=cv2.LINE_AA)
        else:
            canvas = fr.copy()

        src_tag = f"SOURCE: {c['id'][:8]} · {c.get('title') or 'Archive'} ({c.get('year') or 'undated'})"
        canvas = add_hud_overlay(
            canvas,
            top_left=seg.get("phase", "SCION 059 · GRAPHIC ANCHOR"),
            top_right=src_tag,
            bottom_left=seg.get("action", ""),
            bottom_right=seg.get("nearmatch", f"ANCHOR: (640, 352) · {reg_mode.upper()}"),
        )
        out_frames.append(canvas)

    aud = mix_shot_audio(
        c["path"], in_s, dur,
        foley_kind=seg.get("foley", "tap"),
        seed=abs(hash(c["id"])) % 10000,
        freq=float(seg.get("freq", 220.0)),
    )
    meta_entry = {
        "type": "circle_reg_shot",
        "clip_id": c["id"],
        "source_title": c.get("title"),
        "source_year": c.get("year"),
        "source_page": c.get("page"),
        "dur_s": dur,
        "reg_mode": reg_mode,
        "phase": sanitize_text(seg.get("phase", "")),
        "action": sanitize_text(seg.get("action", "")),
        "nearmatch": sanitize_text(seg.get("nearmatch", "")),
    }
    return out_frames, aud, meta_entry


def build_curve_guide_shot(seg: dict) -> tuple:
    c = resolve_clip(seg["clip"])
    dur = float(seg["dur"])
    in_s = float(seg.get("in_s", 0.5))
    curve_type = seg.get("curve_type", "catenary")  # catenary, parabola, depart
    custom_win = bool(seg.get("custom_window", False))
    raw_frames = read_clip_frames(c["path"], in_s, dur, W, H, crop_mode="contain", custom_window=custom_win)
    out_frames = []
    xs = np.linspace(220, W - 220, 120)
    for i, fr in enumerate(raw_frames):
        canvas = fr.copy()
        pts = []
        for x in xs:
            u = (x - W / 2) / 280.0
            if curve_type == "catenary":
                y = 460 - 150 * (math.cosh(u) - 1.0)
                col = COL_MINT
            elif curve_type == "parabola":
                y = 210 + 210 * (u ** 2)
                col = COL_GOLD
            else:
                y = 230 + 190 * ((u - 0.18) ** 2) + 35 * u
                col = COL_RUST
            pts.append([int(x), int(np.clip(y, 60, H - 70))])
        pts_arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(canvas, [pts_arr], isClosed=False, color=col, thickness=3, lineType=cv2.LINE_AA)
        if curve_type == "depart":
            pts2 = []
            for x in xs:
                u = (x - W / 2) / 280.0
                y2 = 250 + 150 * (u ** 2) - 42 * (u ** 3)
                pts2.append([int(x), int(np.clip(y2, 60, H - 70))])
            cv2.polylines(canvas, [np.array(pts2, dtype=np.int32).reshape((-1, 1, 2))], False, COL_MINT, 2, cv2.LINE_AA)

        src_tag = f"SOURCE: {c['id'][:8]} · {c.get('title') or 'Archive'} ({c.get('year') or 'undated'})"
        canvas = add_hud_overlay(
            canvas,
            top_left=seg.get("phase", "SCION 064 · FITTED HYPOTHESIS OVERLAY"),
            top_right=src_tag,
            bottom_left=seg.get("action", ""),
            bottom_right=seg.get("nearmatch", f"GUIDE: {curve_type.upper()}"),
        )
        out_frames.append(canvas)

    aud = mix_shot_audio(c["path"], in_s, dur, foley_kind="tap", freq=260.0)
    meta_entry = {
        "type": "curve_guide_shot",
        "clip_id": c["id"],
        "source_title": c.get("title"),
        "source_year": c.get("year"),
        "source_page": c.get("page"),
        "dur_s": dur,
        "curve_type": curve_type,
        "phase": sanitize_text(seg.get("phase", "")),
        "action": sanitize_text(seg.get("action", "")),
        "nearmatch": sanitize_text(seg.get("nearmatch", "")),
    }
    return out_frames, aud, meta_entry


def build_quad_shot(seg: dict) -> tuple:
    clips = [resolve_clip(p) for p in seg["clips"]]
    in_list = seg.get("in_list", [0.5] * len(clips))
    dur = float(seg["dur"])
    qw, qh = W // 2 - 4, (H - 96) // 2 - 4
    quad_frames = [
        read_clip_frames(c["path"], float(in_list[idx] if idx < len(in_list) else 0.5), dur, qw, qh, crop_mode="cover", custom_window=bool(seg.get("custom_window", False)))
        for idx, c in enumerate(clips)
    ]
    n = len(quad_frames[0])
    out_frames = []
    for i in range(n):
        canvas = np.full((H, W, 3), 14, dtype=np.uint8)
        positions = [
            (2, 38),
            (W // 2 + 2, 38),
            (2, 38 + qh + 6),
            (W // 2 + 2, 38 + qh + 6),
        ]
        for idx, (px, py) in enumerate(positions):
            if idx < len(quad_frames):
                canvas[py : py + qh, px : px + qw] = quad_frames[idx][min(i, len(quad_frames[idx]) - 1)]
        canvas = add_hud_overlay(
            canvas,
            top_left=seg.get("phase", "FOUR-WAY COMPARISON"),
            top_right=" · ".join(f"{c['id'][:6]}({c.get('year') or '?'})" for c in clips),
            bottom_left=seg.get("action", ""),
            bottom_right=seg.get("nearmatch", "SIDE-BY-SIDE RESIDUE AUDIT"),
        )
        out_frames.append(canvas)
    aud = mix_shot_audio(clips[0]["path"], float(in_list[0]), dur, foley_kind="room")
    meta_entry = {
        "type": "quad_shot",
        "clips": [{"id": c["id"], "title": c.get("title"), "year": c.get("year")} for c in clips],
        "dur_s": dur,
        "phase": sanitize_text(seg.get("phase", "")),
        "action": sanitize_text(seg.get("action", "")),
        "nearmatch": sanitize_text(seg.get("nearmatch", "")),
    }
    return out_frames, aud, meta_entry


def build_erasure_shot(seg: dict) -> tuple:
    """
    For BROLL 01: NOBODY HOME (v2 Critic-Verified Person Erasure).
    Combines temporal percentile background estimation with spatial person-region
    segmentation + OpenCV Telea inpainting so the human figure is genuinely removed
    from the room in `submode='derived'` and in the right panel of `submode='triptych'`,
    while the room architecture, lighting, and furniture remain intact.
    """
    c = resolve_clip(seg["clip"])
    dur = float(seg["dur"])
    in_s = float(seg.get("in_s", 0.5))
    submode = seg.get("submode", "derived")
    raw_frames = read_clip_frames(c["path"], in_s, dur, W, H, crop_mode="contain")
    stack = np.stack(raw_frames, axis=0)
    median_plate = np.median(stack, axis=0).astype(np.uint8)

    # Person bounding region (normalized [x0, y0, x1, y1]) if figure is partially stationary
    person_box = seg.get("person_box", None)

    out_frames = []
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
    for idx, fr in enumerate(raw_frames):
        diff = np.max(np.abs(fr.astype(np.int16) - median_plate.astype(np.int16)), axis=2).astype(np.uint8)
        _, motion_mask = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
        motion_mask = cv2.dilate(motion_mask, kernel, iterations=2)

        # If person_box is provided or motion is sparse, combine with spatial figure silhouette mask
        full_mask = motion_mask.copy()
        if person_box:
            bx0, by0 = int(person_box[0] * W), int(person_box[1] * H)
            bx1, by1 = int(person_box[2] * W), int(person_box[3] * H)
            roi = fr[by0:by1, bx0:bx1]
            # Segment foreground figure inside person_box via luminance/edge contrast against surrounding wall
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
            bg_luma = float(np.median(np.concatenate([gray_roi[:, :8].ravel(), gray_roi[:, -8:].ravel(), gray_roi[:8, :].ravel()])))
            sil = (np.abs(gray_roi.astype(np.float32) - bg_luma) > 16.0).astype(np.uint8) * 255
            sil = cv2.morphologyEx(sil, cv2.MORPH_CLOSE, kernel)
            sil = cv2.dilate(sil, kernel, iterations=1)
            full_mask[by0:by1, bx0:bx1] = np.maximum(full_mask[by0:by1, bx0:bx1], sil)

        # First replace moving regions with temporal median where valid, then Telea inpaint remaining figure mask
        mask_blur = cv2.GaussianBlur(motion_mask, (21, 21), 0).astype(np.float32) / 255.0
        base_blend = (fr.astype(np.float32) * (1.0 - mask_blur[:, :, None]) + median_plate.astype(np.float32) * mask_blur[:, :, None]).astype(np.uint8)

        # Inpaint the full figure silhouette so stationary/semi-stationary person pixels completely vanish
        inpaint_mask = cv2.dilate(full_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)), iterations=1)
        derived_bgr = cv2.inpaint(cv2.cvtColor(base_blend, cv2.COLOR_RGB2BGR), inpaint_mask, 11, cv2.INPAINT_TELEA)
        derived = cv2.cvtColor(derived_bgr, cv2.COLOR_BGR2RGB)

        contours, _ = cv2.findContours(inpaint_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if submode == "derived":
            canvas = derived.copy()
            cv2.drawContours(canvas, contours, -1, COL_RUST, 2, lineType=cv2.LINE_AA)
        else:
            pw = W // 3 - 4
            ph = H - 96
            canvas = np.full((H, W, 3), 14, dtype=np.uint8)
            p1 = cv2.resize(fr, (pw, ph))
            mask_rgb = np.zeros_like(fr)
            mask_rgb[:, :, 0] = inpaint_mask
            mask_rgb[:, :, 1] = inpaint_mask // 2
            cv2.drawContours(mask_rgb, contours, -1, COL_MINT, 2)
            p2 = cv2.resize(mask_rgb, (pw, ph))
            p3 = cv2.resize(derived, (pw, ph))
            canvas[40 : 40 + ph, 2 : 2 + pw] = p1
            canvas[40 : 40 + ph, W // 3 + 2 : W // 3 + 2 + pw] = p2
            canvas[40 : 40 + ph, 2 * (W // 3) + 2 : 2 * (W // 3) + 2 + pw] = p3

        src_tag = f"SOURCE: {c['id'][:8]} · {c.get('title') or 'Archive'} ({c.get('year') or 'undated'})"
        canvas = add_hud_overlay(
            canvas,
            top_left=seg.get("phase", "B-ROLL 01 · COMPUTATIONAL ERASURE INTERVENTION"),
            top_right=src_tag,
            bottom_left=seg.get("action", ""),
            bottom_right=seg.get("nearmatch", "AUTHORED MASK SEPARATE FROM RECORDED PIXELS"),
        )
        out_frames.append(canvas)

    aud = mix_shot_audio(c["path"], in_s, dur, foley_kind="room")
    meta_entry = {
        "type": "erasure_shot",
        "clip_id": c["id"],
        "source_title": c.get("title"),
        "source_year": c.get("year"),
        "source_page": c.get("page"),
        "submode": submode,
        "dur_s": dur,
        "phase": sanitize_text(seg.get("phase", "")),
        "action": sanitize_text(seg.get("action", "")),
        "nearmatch": sanitize_text(seg.get("nearmatch", "")),
    }
    return out_frames, aud, meta_entry


def build_carrier_bridge_shot(seg: dict) -> tuple:
    ca = resolve_clip(seg["clip_a"])
    cb = resolve_clip(seg["clip_b"])
    dur = float(seg["dur"])
    fa = read_clip_frames(ca["path"], float(seg.get("in_a", 0.5)), dur, W, H, crop_mode="cover")
    fb = read_clip_frames(cb["path"], float(seg.get("in_b", 0.5)), dur, W, H, crop_mode="cover")
    n = len(fa)
    out_frames = []
    for i in range(n):
        p = i / max(1, n - 1)
        split_x = int(p * W)
        canvas = fa[i].copy()
        if split_x > 0:
            canvas[:, :split_x] = fb[i][:, :split_x]
        cv2.line(canvas, (split_x, 36), (split_x, H - 52), COL_RUST, 3)
        for sy in range(60, H - 60, 72):
            cv2.rectangle(canvas, (max(4, split_x - 14), sy), (min(W - 4, split_x + 14), sy + 36), COL_GOLD, 2)
        canvas = add_hud_overlay(
            canvas,
            top_left="B-ROLL 03 · AUTHORED OPTICAL CARRIER BRIDGE",
            top_right=f"{ca['id'][:8]} -> {cb['id'][:8]}",
            bottom_left=seg.get("action", "Synthetic splice/carrier transition (authored layer, not historical join)"),
            bottom_right="SCION 071 + 113 · INSPECTABLE LAYER",
            accent=COL_RUST,
        )
        out_frames.append(canvas)
    aud = mix_shot_audio(ca["path"], 0.5, dur, foley_kind="projector")
    return out_frames, aud, {
        "type": "carrier_bridge_shot",
        "clip_a": {"id": ca["id"], "title": ca.get("title"), "year": ca.get("year")},
        "clip_b": {"id": cb["id"], "title": cb.get("title"), "year": cb.get("year")},
        "dur_s": dur,
        "phase": "B-ROLL 03 · AUTHORED OPTICAL CARRIER BRIDGE",
        "action": sanitize_text(seg.get("action", "")),
        "nearmatch": "SCION 071 + 113 · INSPECTABLE LAYER",
    }


def render_film_from_spec(spec: dict) -> dict:
    slug = spec["slug"]
    out_mp4 = FILMS_DIR / f"{slug}.mp4"
    print(f"Rendering {slug} ({spec['title']})...")

    all_frames = []
    all_audio = []
    edl_records = []
    cur_t = 0.0

    # 1. Opening Title Card (3.0s)
    open_dur = 3.0
    open_frames_n = int(round(open_dur * FPS))
    open_card = render_card_frame(
        kicker=spec["kicker"],
        title=spec["title"],
        subtitle=spec["subtitle"],
        body=spec["theorem"],
        footer=spec["lineage"],
        accent=COL_MINT,
    )
    for _ in range(open_frames_n):
        all_frames.append(open_card)
    all_audio.append(synth_room_tone_and_foley(open_dur, kind="room", seed=11))
    edl_records.append({
        "seg_idx": 1,
        "type": "title_card",
        "title": sanitize_text(spec["title"]),
        "phase": "OPENING SLATE",
        "action": sanitize_text(spec["subtitle"]),
        "start_sec": 0.0,
        "end_sec": round(open_dur, 2),
        "dur_s": round(open_dur, 2),
    })
    cur_t += open_dur

    # 2. Segments
    show_hud_default = spec.get("show_hud_default", True)
    for idx, seg in enumerate(spec["segments"], 2):
        m = seg.get("mode", "standard")
        if m == "card":
            dur = float(seg.get("dur", 2.5))
            cf = render_card_frame(
                kicker=seg.get("kicker", spec["kicker"]),
                title=seg["title"],
                subtitle=seg.get("subtitle", ""),
                body=seg.get("body", ""),
                footer=seg.get("footer", "ALLWAYS · NEARMATCH PROOF"),
                accent=COL_GOLD,
            )
            for _ in range(int(round(dur * FPS))):
                all_frames.append(cf)
            all_audio.append(synth_room_tone_and_foley(dur, kind="room", seed=idx * 17))
            rec = {
                "type": "intertitle",
                "title": sanitize_text(seg["title"]),
                "phase": "INTERTITLE SLATE",
                "action": sanitize_text(seg.get("subtitle", seg["title"])),
                "dur_s": dur,
            }
        elif m == "split":
            frs, aud, rec = build_split_shot(seg)
            all_frames.extend(frs)
            all_audio.append(aud)
        elif m == "triptych":
            frs, aud, rec = build_triptych_shot(seg)
            all_frames.extend(frs)
            all_audio.append(aud)
        elif m == "reframe":
            frs, aud, rec = build_reframe_shot(seg)
            all_frames.extend(frs)
            all_audio.append(aud)
        elif m == "circle_reg":
            frs, aud, rec = build_circle_reg_shot(seg)
            all_frames.extend(frs)
            all_audio.append(aud)
        elif m == "curve_guide":
            frs, aud, rec = build_curve_guide_shot(seg)
            all_frames.extend(frs)
            all_audio.append(aud)
        elif m == "quad":
            frs, aud, rec = build_quad_shot(seg)
            all_frames.extend(frs)
            all_audio.append(aud)
        elif m == "erasure":
            frs, aud, rec = build_erasure_shot(seg)
            all_frames.extend(frs)
            all_audio.append(aud)
        elif m == "carrier_bridge":
            frs, aud, rec = build_carrier_bridge_shot(seg)
            all_frames.extend(frs)
            all_audio.append(aud)
        else:
            show_hud = seg.get("show_hud", show_hud_default)
            frs, aud, rec = build_standard_shot(seg, show_hud=show_hud)
            all_frames.extend(frs)
            all_audio.append(aud)

        seg_dur = float(rec.get("dur_s", seg.get("dur", 4.0)))
        rec["seg_idx"] = idx
        rec["start_sec"] = round(cur_t, 2)
        cur_t += seg_dur
        rec["end_sec"] = round(cur_t, 2)
        edl_records.append(rec)

    # 3. Closing Source Attribution & NEARMATCH Ledger Card (3.5s)
    unique_sources = []
    seen_s = set()
    for r in edl_records:
        if r.get("clip_id") and r["clip_id"] not in seen_s:
            seen_s.add(r["clip_id"])
            unique_sources.append(f"{r['clip_id'][:8]} · {r.get('source_title') or 'Archive'} ({r.get('source_year') or 'undated'})")
        for subk in ("clip_a", "clip_b"):
            if isinstance(r.get(subk), dict):
                cid = r[subk]["id"]
                if cid not in seen_s:
                    seen_s.add(cid)
                    unique_sources.append(f"{cid[:8]} · {r[subk].get('title') or 'Archive'} ({r[subk].get('year') or 'undated'})")
        if isinstance(r.get("clips"), list):
            for citem in r["clips"]:
                cid = citem["id"]
                if cid not in seen_s:
                    seen_s.add(cid)
                    unique_sources.append(f"{cid[:8]} · {citem.get('title') or 'Archive'} ({citem.get('year') or 'undated'})")

    close_body = "SOURCE LEDGER: " + "  |  ".join(unique_sources[:10])
    if spec.get("boundary_note"):
        close_body += "\n\nBOUNDARY NOTE: " + spec["boundary_note"]

    close_dur = 3.5
    close_card = render_card_frame(
        kicker=f"{spec['kicker']} · SOURCE & NEARMATCH AUDIT",
        title=f"{spec['title']} — Source Record",
        subtitle=f"{len(unique_sources)} distinct archival recordings · Critic-verified v2 proof",
        body=close_body,
        footer="Preserving a route back to movingimagearchive.com & cineosis-lab",
        accent=COL_GOLD,
    )
    for _ in range(int(round(close_dur * FPS))):
        all_frames.append(close_card)
    all_audio.append(synth_room_tone_and_foley(close_dur, kind="room", seed=999))
    edl_records.append({
        "seg_idx": len(edl_records) + 1,
        "type": "closing_ledger",
        "title": "SOURCE ATTRIBUTION & BOUNDARY NOTE",
        "phase": "CLOSING LEDGER",
        "action": sanitize_text(spec.get("boundary_note", "")),
        "start_sec": round(cur_t, 2),
        "end_sec": round(cur_t + close_dur, 2),
        "dur_s": close_dur,
    })

    encode_film(all_frames, all_audio, out_mp4)
    total_dur = round(len(all_frames) / FPS, 2)
    manifest = {
        "slug": slug,
        "version": "v2",
        "series": spec["series"],
        "kicker": sanitize_text(spec["kicker"]),
        "title": sanitize_text(spec["title"]),
        "subtitle": sanitize_text(spec["subtitle"]),
        "scion_id": spec["scion_id"],
        "supporting_scions": spec.get("supporting_scions", []),
        "lineage": sanitize_text(spec["lineage"]),
        "theorem": sanitize_text(spec["theorem"]),
        "boundary_note": sanitize_text(spec.get("boundary_note", "")),
        "critic_tribunal": spec.get("critic_tribunal", {}),
        "duration_seconds": total_dur,
        "video_file": f"films/{slug}.mp4",
        "source_count": len(unique_sources),
        "sources_summary": unique_sources,
        "edl": edl_records,
    }
    (MANIFESTS_DIR / f"{slug}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"  -> Completed {out_mp4.name} ({total_dur}s, {len(unique_sources)} sources)")
    return manifest
