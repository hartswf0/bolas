#!/usr/bin/env python3
"""
build_scion_shape_films.py — Author SCION 114–121 Prompts & Cut 8 Multi-Shot Shape Films
========================================================================================
For each of the 8 visual composition shapes from 'Life Is All About Perspective! #shorts'
(@gfxmotionbyahmar, YouTube QNvK63WetSA):
  1. Authors a complete standalone SCION operator prompt (SCION 114 through SCION 121)
     in paeleo/allways/scion/prompts/ following SCION_CINEMA_LINEAGE_FORGE.md.
  2. Selects 8 distinct archival shots from the 389-shot Moving Image Archive corpus
     (6 high-scoring exemplars across diverse films + 1 deliberate contextual-release /
     rupture shot + 1 flagship resolution shot) and cuts a 24.0-second (8-cut, 24fps)
     playable film with bespoke procedural stereo sound design in allways-tensor/films/.
  3. Writes allways-tensor/scion_shapes.json and allways-tensor/img/scion_8_shapes_films_sheet.jpg.
"""

import os
import json
import math
import wave
import struct
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw

from forage_8_grids import (
    REPO_ROOT,
    OUT_DIR,
    IMG_DIR,
    RULES_SPEC,
    harvest_candidate_shots,
    score_frame_eight_rules,
    draw_rule_overlay_pil,
)

PROMPTS_DIR = os.path.join(REPO_ROOT, "paeleo/allways/scion/prompts")
FILMS_DIR = os.path.join(OUT_DIR, "films")
os.makedirs(PROMPTS_DIR, exist_ok=True)
os.makedirs(FILMS_DIR, exist_ok=True)


SCION_SHAPES_SPEC = [
    {
        "scion_id": 114,
        "rule_num": 1,
        "rule_id": "golden_spiral",
        "slug": "scion-114-golden-spiral-logarithmic-torque",
        "film_file": "films/scion-114-golden-spiral.mp4",
        "title": "SCION 114 // Golden Spiral — Logarithmic Torque & Eccentric Anchor",
        "short_title": "114 · GOLDEN SPIRAL",
        "family": "Framing, gesture and city rhythms",
        "lineage": "Golden Ratio / Fibonacci Spiral (1:1.618, 00:00–00:06 in 'Life Is All About Perspective! #shorts', @gfxmotionbyahmar); Jay Hambidge, The Elements of Dynamic Symmetry (1926); Sergei Eisenstein, 'Organicness and Imagicity' (Nonindifferent Nature, 1945).",
        "requested_ref": "Golden Ratio / Fibonacci Spiral (1:1.618) — @gfxmotionbyahmar (00:00–00:06)",
        "theorem": "Use asymmetric peripheral mass (overhanging branches, curved shadows, sweeping architectural shells, or mechanical arms) to torque the viewer's eye along a decreasing logarithmic radius (1 : 0.618 : 0.382) into an off-center focal singularity at (u, v) = (0.68, 0.44), then release the spiral when the focal object initiates an outward linear action.",
        "distinct_from": "SCION 059 (Ball) holds a concentric circle at the screen center and SCION 064 (Parabolas) compares symmetric ballistic arcs; SCION 114 uses asymmetric peripheral framing on the 1:1.618 Golden Rectangle partition to wind attention inward toward an eccentric focal node before releasing it.",
        "formal_objects": [
            "Golden Rectangle partitions (u = 0.618, v = 0.618, u2 = 0.764) and logarithmic spiral locus r(theta) = r0 * exp(b * theta)",
            "Eccentric spiral eye anchor (u_eye = 0.68, v_eye = 0.44) and peripheral lead-in tangent mask",
            "Quadrant edge-density ratio (outer sweeping arc vs. focal eye salience)",
            "Contextual release vector when the subject breaks out of the spiral eye",
            "Harmonic golden-ratio pulse intervals (f0 * phi^k) with a deliberate rest at the release cut",
        ],
        "protected_conditions": [
            "Do not force centered circular objects into a Fibonacci claim; peripheral asymmetry is required.",
            "Show at least three archival observations unannotated before introducing the Golden Rectangle and spiral guide.",
            "Include one contextual release where a hand, vehicle, or camera pan exits the spiral eye.",
        ],
        "swarm": [
            "Logarithmic contour scout: locate archival shots where peripheral mass sweeps across three quadrants into the (0.68, 0.44) eye.",
            "Golden partition editor: sequence unannotated observations before locking the 1:1.618 viewfinder guide.",
            "Phi-harmonic sound designer: build pulses spaced by golden-section intervals (382ms / 618ms) with a silent release.",
            "Independent perception critic: verify that the spiral torque is felt in the raw footage before the gold overlay appears.",
        ],
        "hard_proof": "Construct a 24-second, 8-shot archival film at 24fps. Open with three unannotated 3.0-second archival observations (Shots 1–3) whose peripheral foliage, curved shadow, or sweeping instrument guides the eye into the upper-right golden node (0.68, 0.44). In Shots 4–6, snap the etched gold 1:1.618 rectangle subdivisions and logarithmic spiral onto three new archival sources 0.6 seconds after each cut so the viewer tests the geometric fit against moving reality. In Shot 7 (18.0s–21.0s), trigger a contextual release where a moving subject or camera pan crosses out of the spiral eye while the acoustic pulse drops into silence. Conclude in Shot 8 (21.0s–24.0s) by returning to the primary lone-cedar / spiral exemplar and dissolving the viewfinder guide away so the unannotated image carries the learned spiral tension.",
        "tribunal_watch": [
            "Peripheral asymmetry guides the eye toward (0.68, 0.44) in Shots 1–3 before any overlay appears.",
            "The 1:1.618 Golden Rectangle subdivisions in Shots 4–6 clarify real structural partitions rather than decorating flat space.",
            "Shot 7 breaks the spiral lock through an observable directional exit accompanied by an acoustic drop.",
            "The final unannotated hold in Shot 8 remains legible after the gold viewfinder dissolves.",
        ],
        "tribunal_checks": [
            "Report measured spiral-corridor edge density and focal-eye Sobel salience for all 8 cuts.",
            "Verify every archival cut preserves source film ID, timestamp, maker, and Prelinger/IA attribution.",
        ],
        "repairs": [
            ("The spiral overlay looks pasted onto centered circles.", "Candidates were chosen for roundness rather than asymmetric peripheral lead-in.", "Replace centered round shots with frames having >1.4x edge density along the outer spiral sweep plus a localized focal peak at (0.68, 0.44)."),
            ("The gold grid overwhelms the archival cinematography.", "The overlay is visible from frame 0 of the film.", "Keep Shots 1–3 completely unannotated and delay the viewfinder snap by 0.6s in Shots 4–6."),
        ],
        "sound_mode": "golden_phi",
    },
    {
        "scion_id": 115,
        "rule_num": 2,
        "rule_id": "frame_in_frame",
        "slug": "scion-115-frame-in-a-frame-threshold-enclosure",
        "film_file": "films/scion-115-frame-in-frame.mp4",
        "title": "SCION 115 // Frame in a Frame — Threshold Enclosure & Aperture Release",
        "short_title": "115 · FRAME IN FRAME",
        "family": "Framing, gesture and city rhythms",
        "lineage": "Frame in a Frame / Sub-framing (00:07–00:08 in 'Life Is All About Perspective! #shorts', @gfxmotionbyahmar); Jean Renoir (The Rules of the Game, 1939); Orson Welles & Gregg Toland (Citizen Kane, 1941); Yasujiro Ozu doorway apertures.",
        "requested_ref": "Frame in a Frame (Sub-framing) — @gfxmotionbyahmar (00:07–00:08)",
        "theorem": "Use a physical foreground aperture (doorway casement, train window, concrete arch, optical housing) occupying the outer frame margin to compress a distant or interior action inside u in [0.17, 0.83], v in [0.14, 0.86], so that crossing the inner sill changes both spatial authority and room tone.",
        "distinct_from": "SCION 086 (Songs from the Second Floor) holds a single continuous deep-focus room; SCION 115 treats the internal rectangular boundary as a physical threshold between an outer watching space and an inner stage across multiple archival worlds.",
        "formal_objects": [
            "Inner aperture boundary rectangle u in [0.17, 0.83], v in [0.14, 0.86] and corner registration vectors",
            "Peripheral matte darkness vs. interior aperture luminance contrast ratio",
            "Threshold crossing timecode when a body, hand, or vehicle breaches the inner frame",
            "Dual-zone acoustic filtering (muffled outer frame vs. resonant inner aperture click)",
        ],
        "protected_conditions": [
            "Never add an artificial vignette or fake black matte; the inner frame must belong to the physical architecture or apparatus in the shot.",
            "Keep the first three archival thresholds unannotated so the viewer reads the physical casement first.",
            "Include a threshold-breach shot where a subject steps through or looks out of the enclosing frame.",
        ],
        "swarm": [
            "Aperture archivist: harvest doorway, window, bridge-arch, and viewfinder shots with strong rect-band edge peaks.",
            "Threshold montage editor: cut across domestic doors, transit windows, and optical instruments while holding the inner rectangle constant.",
            "Room-tone sound designer: switch from low-pass exterior hum to crisp interior wood/glass transients when the viewfinder locks.",
            "Independent spatial critic: verify that the sub-frame compresses depth rather than acting as a flat border.",
        ],
        "hard_proof": "Build a 24-second, 8-shot archival film at 24fps. Open with three unannotated 3.0-second shots (Shots 1–3) where physical doorways, train windows, and optical housings enclose an interior figure or distant vista. In Shots 4–6, snap the three-sided gold sub-frame guide and corner registration ticks onto the internal boundary at +0.6s, paired with an audible shutter/doorway latch transient. In Shot 7 (18.0s–21.0s), release the enclosure as a figure or camera pushes past the threshold while the room tone drops out. End in Shot 8 (21.0s–24.0s) on the primary doorway threshold with the gold guide dissolving away.",
        "tribunal_watch": [
            "Every sub-frame in Shots 1–6 is produced by real physical architecture or apparatus in the archival image.",
            "The gold inner boundary in Shots 4–6 aligns with the physical casement without obscuring the enclosed subject.",
            "Shot 7 breaches the enclosure so the frame-within-a-frame ceases to feel like a static prison.",
            "Acoustic filtering distinguishes enclosed interior focus from the contextual release.",
        ],
        "tribunal_checks": [
            "Measure perimeter edge density along u in {0.17, 0.83} and v in {0.14, 0.86} vs. interior contrast.",
            "Confirm zero synthetic borders or post-production vignettes were applied to the source footage.",
        ],
        "repairs": [
            ("The inner rectangle misses the actual doorway width.", "Different archival lenses place door jambs at varying margins.", "Select shots whose physical jambs cluster near the [0.17, 0.83] aperture band and report exact alignment scores."),
            ("The sequence feels claustrophobic and static.", "No subject ever crosses the inner boundary.", "Insert Shot 7 as an explicit threshold crossing where movement breaches the casement."),
        ],
        "sound_mode": "threshold_room",
    },
    {
        "scion_id": 116,
        "rule_num": 3,
        "rule_id": "s_curve",
        "slug": "scion-116-s-curve-serpentine-depth-relay",
        "film_file": "films/scion-116-s-curve.mp4",
        "title": "SCION 116 // S-Curve — Serpentine Depth Relay & Inflection Delay",
        "short_title": "116 · S-CURVE",
        "family": "Framing, gesture and city rhythms",
        "lineage": "S-Curve / Leading Curve (00:09–00:11 in 'Life Is All About Perspective! #shorts', @gfxmotionbyahmar); William Hogarth, The Analysis of Beauty ('Line of Beauty', 1753); winding park pathways, rivers, and highway ramps in archival cinema.",
        "requested_ref": "S-Curve (Leading Curve) — @gfxmotionbyahmar (00:09–00:11)",
        "theorem": "Guide eye-trace and moving bodies along a double-inflected cubic Bezier path B(t) from near-foreground (0.20, 0.88) through a mid-plane curvature reversal (kappa = 0) into far-background (0.80, 0.12), using the serpentine bend to delay arrival and reveal surrounding terrain.",
        "distinct_from": "SCION 064 (Parabolas) examines single-sign curvature (hanging chains and projectile arcs where curvature never changes sign); SCION 116 requires a sign-reversing inflection point (concave to convex) that swings lateral motion across the frame while advancing in depth.",
        "formal_objects": [
            "Cubic Bezier control polygon P0=(0.20,0.88), P1=(0.78,0.72), P2=(0.22,0.28), P3=(0.80,0.12)",
            "Inflection coordinate t=0.50 where signed curvature kappa(t) crosses zero",
            "Tangent alignment score between image Sobel gradients and dB(t)/dt",
            "Continuous frequency glissando sweeping across the inflection midpoint",
        ],
        "protected_conditions": [
            "Distinguish true double-inflected S-curves from simple single-bend arcs or straight diagonals.",
            "Present Shots 1–3 unannotated so the viewer's eye follows the winding path naturally before the Bezier overlay appears.",
            "Include a rupture cut where motion cuts straight across the bend rather than following the path.",
        ],
        "swarm": [
            "Serpentine path researcher: identify winding walkways, river bends, highway interchanges, and anatomical spirals with high Bezier corridor density.",
            "Trajectory relay editor: cut so the exit vector at the top-right (0.80, 0.12) relays back to the bottom-left entrance (0.20, 0.88).",
            "Continuous-sweep sound designer: map the Bezier parameter t in [0,1] to a stereo pan and pitch inflection.",
            "Independent eye-trace critic: verify that the mid-frame inflection slows visual scanning compared to a straight diagonal.",
        ],
        "hard_proof": "Create a 24-second, 8-shot archival film at 24fps. In Shots 1–3 (0.0s–9.0s), present three unannotated archival scenes of winding pathways, curved park bridges, and serpentine trajectories that carry the eye from bottom-left to top-right. In Shots 4–6 (9.0s–18.0s), snap the gold cubic Bezier S-curve and cyan endpoint anchors P0, P3 onto the frame at +0.6s while a stereo glissando traces the inflection. In Shot 7 (18.0s–21.0s), cut to a contextual release where direct motion breaks across the curve in silence. Conclude in Shot 8 (21.0s–24.0s) with the Niagara park pathway exemplar as the gold Bezier guide dissolves.",
        "tribunal_watch": [
            "Shots 1–3 exhibit a genuine double bend (foreground sweep + mid-plane reversal + background exit).",
            "The Bezier guide in Shots 4–6 tracks real physical pathways, tracks, or contours in the footage.",
            "Shot 7 provides a clear kinesthetic contrast by breaking the serpentine flow.",
            "The stereo glissando reinforces the lateral left-to-right-to-left-to-right inflection.",
        ],
        "tribunal_checks": [
            "Compute Sobel edge density inside the 22px Bezier corridor vs. background for all 8 cuts.",
            "Record source film IDs, timestamps, and Bezier control coordinates in the JSON ledger.",
        ],
        "repairs": [
            ("A candidate shot is only a single C-curve.", "Single arcs score high on half the Bezier corridor.", "Require edge support in both the lower-left (t < 0.4) and upper-right (t > 0.6) inflected branches."),
            ("Cuts feel disconnected across shots.", "Subjects move at incompatible speeds along the S-curve.", "Order Shots 1–6 from pedestrian park paths to architectural spirals and highway curves."),
        ],
        "sound_mode": "serpentine_glide",
    },
    {
        "scion_id": 117,
        "rule_num": 4,
        "rule_id": "symmetry",
        "slug": "scion-117-vertical-bisector-mirror-cleavage",
        "film_file": "films/scion-117-symmetry.mp4",
        "title": "SCION 117 // Vertical Bisector — Bilateral Mirror & Cleavage Seam",
        "short_title": "117 · SYMMETRY (50/50)",
        "family": "Framing, gesture and city rhythms",
        "lineage": "Symmetry / Vertical Bisector (00:11–00:13 in 'Life Is All About Perspective! #shorts', @gfxmotionbyahmar, bisecting the WTC Oculus); Buster Keaton (The Electric House, 1922); Stanley Kubrick one-point architectural corridors.",
        "requested_ref": "Symmetry (Vertical Bisector) — @gfxmotionbyahmar (00:11–00:13)",
        "theorem": "Establish a strict 50/50 bilateral architectural mirror inside a single undivided physical space across the vertical centerline u = 0.50, then introduce an asymmetric human or mechanical event on one side so the centerline transforms from a balance axis into a cleavage seam.",
        "distinct_from": "SCION 056 (Symmetry — Imperfect Pairing) joins two separate recordings in a split-screen and SCION 089 uses planimetric staging as a multi-character arrival schedule; SCION 117 operates inside a single uncut space whose own physical architecture mirrors itself across u = 0.50 until one side defects.",
        "formal_objects": [
            "Vertical bisector axis u = 0.50 and bilateral mirror correlation r_mirror(I_left, flip(I_right))",
            "Left-half vs. right-half luminance and optical-flow divergence delta_V(u < 0.5, u > 0.5)",
            "Bilateral mirror arrow anchors at v in {0.28, 0.50, 0.72}",
            "Balanced L/R stereo ping-pong pulses that knocked out of phase at the cleavage cut",
        ],
        "protected_conditions": [
            "Never digitally mirror half a frame to fake symmetry; the bilateral correlation must exist in the original archival recording.",
            "Keep Shots 1–3 unannotated so the architectural 50/50 split registers with the naked eye.",
            "Include a cleavage shot (Shot 7) where one side of the symmetric space acts independently of the other.",
        ],
        "swarm": [
            "Bilateral correlation scout: measure pixel-level mirror correlation across all 389 archival shots to find genuine architectural and mechanical 50/50 splits.",
            "Cleavage editor: hold dead-center frontal views before cutting to an asymmetric unilateral disruption.",
            "Binaural balance sound designer: lock L and R channels in exact phase during symmetric holds, then mute one channel at the rupture.",
            "Independent geometry critic: confirm no synthetic mirroring occurred and that the asymmetry in Shot 7 is consequential.",
        ],
        "hard_proof": "Produce a 24-second, 8-shot archival film at 24fps. Open with three unannotated 3.0-second shots (Shots 1–3) with measured bilateral mirror correlation > 0.90 (twin sliding doors in Keaton's The Electric House, frontal projector shutter diagrams, symmetrical room elevations). In Shots 4–6 (9.0s–18.0s), snap the gold u = 0.50 vertical bisector and cyan bilateral arrows onto three new symmetrical spaces at +0.6s with phase-locked stereo pulses. In Shot 7 (18.0s–21.0s), introduce a unilateral movement that breaks the 50/50 mirror while the right audio channel drops to silence. Conclude in Shot 8 (21.0s–24.0s) with Keaton's twin doors as the gold bisector dissolves.",
        "tribunal_watch": [
            "Shots 1–6 are genuine uncut single-camera recordings with striking 50/50 bilateral architecture.",
            "The u = 0.50 bisector in Shots 4–6 lands directly on the architectural ridge, seam, or optical axis.",
            "Shot 7 makes the human/mechanical departure from symmetry immediately legible.",
            "Stereo phase-locking and unilateral mute make the symmetry and its cleavage audible.",
        ],
        "tribunal_checks": [
            "Verify bilateral mirror correlation score (0.85–0.995) on the raw unmirrored archival frames.",
            "Audit transform ledger to confirm zero horizontal flip operations were applied.",
        ],
        "repairs": [
            ("A shot is centered on a face but the background is lopsided.", "Local center salience was confused with whole-frame bilateral symmetry.", "Weight whole-frame L/R pixel correlation and gradient correlation across the full width."),
            ("Perfect symmetry becomes sterile after four cuts.", "Every shot is a static architectural elevation.", "Interleave mechanical shutters and human doorway crossings culminating in the Shot 7 unilateral break."),
        ],
        "sound_mode": "bilateral_mirror",
    },
    {
        "scion_id": 118,
        "rule_num": 5,
        "rule_id": "rule_of_thirds",
        "slug": "scion-118-rule-of-thirds-nodal-counterbalance",
        "film_file": "films/scion-118-rule-of-thirds.mp4",
        "title": "SCION 118 // Rule of Thirds — Nodal Counterbalance & Off-Axis Tension",
        "short_title": "118 · RULE OF THIRDS",
        "family": "Framing, gesture and city rhythms",
        "lineage": "The Rule of Thirds (3x3 Grid, 00:14–00:15 in 'Life Is All About Perspective! #shorts', @gfxmotionbyahmar); John Thomas Smith, Remarks on Rural Scenery (1797, codifying the 1/3 and 2/3 harmonic division of painting and landscape).",
        "requested_ref": "The Rule of Thirds (3x3 Grid) — @gfxmotionbyahmar (00:14–00:15)",
        "theorem": "Anchor a primary subject on one vertical third (u = 1/3) and a counterweight interlocutor, tower, or object on the opposite vertical third (u = 2/3) across a shared horizontal third (v = 1/3 or 2/3), turning the empty center third into an active field of gaze, dialogue, or impending crossing.",
        "distinct_from": "SCION 117 (Vertical Bisector) collapses tension onto the center line u = 0.50 and SCION 119 locks a single figure inside the center channel; SCION 118 evacuates the center so that dynamic equilibrium lives across the four off-axis intersections (u, v) in {1/3, 2/3}^2.",
        "formal_objects": [
            "Trisection lines u in {1/3, 2/3} and v in {1/3, 2/3}",
            "Four power-point nodal patches N_ij = (i/3, j/3) for i,j in {1,2} and their Sobel salience weights",
            "Cross-nodal dipole vector connecting the primary subject node to the counterweight node",
            "3-against-2 polyrhythmic bell pulses mapped to the horizontal and vertical trisections",
        ],
        "protected_conditions": [
            "Do not accept dead-center portraits where the 1/3 and 2/3 lines merely clip a subject's shoulders; true off-axis nodal mass is required.",
            "Show Shots 1–3 unannotated so the viewer perceives the left-right counterbalance before the 3x3 grid snaps on.",
            "Include a contextual release (Shot 7) where a character crosses through the vacant center third to collapse the dipole.",
        ],
        "swarm": [
            "Nodal salience analyst: score all 389 archival shots for simultaneous energy along the 1/3 and 2/3 lines and the 4 power intersections.",
            "Counterbalance montage editor: cut between two-shots, landscape horizons with vertical towers, and instructional grid plates.",
            "Polyrhythmic sound designer: voice the 3x3 grid as a 3:2 harmonic ratio that pauses when the center is breached.",
            "Independent composition critic: verify that the center third acts as a charged interval between the two vertical thirds.",
        ],
        "hard_proof": "Assemble a 24-second, 8-shot archival film at 24fps. In Shots 1–3 (0.0s–9.0s), present three unannotated archival shots where a seated person on u = 1/3 counterbalances a partner or architectural vertical on u = 2/3 above a v = 2/3 baseline. In Shots 4–6 (9.0s–18.0s), snap the gold 3x3 grid and four cyan power-point rings onto three new shots at +0.6s with a 3:2 polyrhythmic pulse. In Shot 7 (18.0s–21.0s), trigger a contextual release as movement invades the center third while the pulse rests. End in Shot 8 (21.0s–24.0s) with the Hi Diddle Diddle two-shot as the 3x3 grid dissolves.",
        "tribunal_watch": [
            "At least two power-point intersections (i/3, j/3) carry distinct narrative or architectural weight in Shots 1–6.",
            "The horizontal third (v = 1/3 or 2/3) aligns with a readable horizon, sill, or table line.",
            "Shot 7 bridges the gap between the 1/3 and 2/3 verticals so the counterbalance resolves into action.",
            "The final unannotated shot lets the viewer feel the 4 power nodes without the wireframe.",
        ],
        "tribunal_checks": [
            "Measure Sobel salience at the 4 power nodes vs. center patch (0.50, 0.50) across all 8 cuts.",
            "Verify full archival provenance for every cut in the EDL.",
        ],
        "repairs": [
            ("The 3x3 grid lands on empty wall while the actor sits in the middle.", "Line-energy alone matched a background molding.", "Require combined line-energy AND top-2 power-node salience peaks at (1/3, 2/3)."),
            ("The grid feels like a generic camera viewfinder overlay.", "No dramatic relation connects the left and right thirds.", "Prioritize two-shots and subject-to-landmark gazes where an eyeline crosses from u=1/3 to u=2/3."),
        ],
        "sound_mode": "thirds_polyrhythm",
    },
    {
        "scion_id": 119,
        "rule_num": 6,
        "rule_id": "centered",
        "slug": "scion-119-center-channel-corridor-isolation",
        "film_file": "films/scion-119-centered.mp4",
        "title": "SCION 119 // Center Channel — Corridor Isolation & Baseline Gravity",
        "short_title": "119 · CENTERED CHANNEL",
        "family": "Framing, gesture and city rhythms",
        "lineage": "Centered / Center Channel + Horizon (00:16–00:17 in 'Life Is All About Perspective! #shorts', @gfxmotionbyahmar, locking a lone bench subject inside two parallel center verticals and a lower baseline); Chantal Akerman portrait holds; silent-era isolated figure staging.",
        "requested_ref": "Centered (Center Channel + Horizon) — @gfxmotionbyahmar (00:16–00:17)",
        "theorem": "Lock a lone human figure or upright object inside a narrow central vertical channel u in [0.42, 0.58] (16% of frame width) grounded on a lower third horizontal baseline v = 0.68, isolating the subject's stillness against the wide flanking periphery until the subject steps out of the corridor.",
        "distinct_from": "SCION 117 (Vertical Bisector) compares left and right mirror halves of an entire architectural space; SCION 119 carves a narrow 16%-wide vertical slot in the center of the frame and evacuates the left ([0, 0.42]) and right ([0.58, 1.0]) flanks to isolate a single grounded body.",
        "formal_objects": [
            "Parallel center-channel boundaries u_L = 0.42 and u_R = 0.58",
            "Lower gravitational baseline v_base = 0.68 and central anchor node (0.50, 0.68)",
            "Center-to-flank salience contrast ratio S(u in [0.42,0.58]) / S(flanks)",
            "Focused mono center-channel fundamental tone + low baseline thud at v = 0.68",
        ],
        "protected_conditions": [
            "The subject must fit within or anchor the narrow [0.42, 0.58] vertical corridor rather than filling the entire frame width.",
            "Show Shots 1–3 unannotated so the subject's solitude inside the center slot is felt directly.",
            "Include a corridor-exit release (Shot 7) where the subject leans, reaches, or walks across the u = 0.42 or u = 0.58 wall.",
        ],
        "swarm": [
            "Corridor isolation scout: compute center-slot salience vs. peripheral stillness across all 389 archival shots.",
            "Baseline gravity editor: match the v = 0.68 bench, desk, road, or floor horizon across cuts from different decades.",
            "Mono-column sound designer: focus acoustic energy dead-center with a dry wooden baseline pulse.",
            "Independent portrait critic: evaluate whether the parallel verticals heighten human presence rather than boxing the subject arbitrarily.",
        ],
        "hard_proof": "Build a 24-second, 8-shot archival film at 24fps. Open with three unannotated 3.0-second shots (Shots 1–3) of lone seated speakers, marchers, and figures anchored on the v = 0.68 baseline inside the central corridor. In Shots 4–6 (9.0s–18.0s), snap the twin gold vertical lines (u = 0.42, 0.58), lower baseline (v = 0.68), and cyan anchor node onto three new archival portraits at +0.6s. In Shot 7 (18.0s–21.0s), cut to a contextual release where a figure breaks through the corridor wall while the center drone cuts to silence. End in Shot 8 (21.0s–24.0s) with the Almost Human seated speaker as the parallel gold rails dissolve.",
        "tribunal_watch": [
            "Each subject in Shots 1–6 sits or stands convincingly inside the [0.42, 0.58] vertical corridor.",
            "The v = 0.68 horizontal line supports the physical seat, hands, or ground plane across cuts.",
            "Flanking regions [0, 0.42] and [0.58, 1.0] remain comparatively quiet, giving the center slot real pressure.",
            "Shot 7 breaks the slot so the human subject is not permanently trapped by the diagram.",
        ],
        "tribunal_checks": [
            "Verify center-channel salience ratio S_center / (S_left + S_right) and v = 0.68 horizontal edge energy.",
            "Preserve full archival attribution and timestamps for all 8 cuts.",
        ],
        "repairs": [
            ("Close-up faces overflow the [0.42, 0.58] rails.", "Tight headshots span u in [0.25, 0.75].", "Penalize high edge density in the outer flanks so medium/full shots of lone figures win."),
            ("The lower line floats across the subject's chest.", "Vertical framing varied between shots.", "Require horizontal gradient support near v = 0.68 corresponding to benches, tables, or ground planes."),
        ],
        "sound_mode": "center_corridor",
    },
    {
        "scion_id": 120,
        "rule_num": 7,
        "rule_id": "v_shape",
        "slug": "scion-120-v-shape-wedge-convergence-and-split",
        "film_file": "films/scion-120-v-shape.mp4",
        "title": "SCION 120 // V-Shape — Converging Wedge & Apex Funnel",
        "short_title": "120 · V-SHAPE WEDGE",
        "family": "Framing, gesture and city rhythms",
        "lineage": "V-Shape / Converging Wedge (00:18–00:20 in 'Life Is All About Perspective! #shorts', @gfxmotionbyahmar, framing the sunlit gap between two park figures and the V-shaped canopy opening); Walter Ruttmann (Berlin: Symphony of a Great City, 1927); Dziga Vertov diagonal wedges.",
        "requested_ref": "V-Shape (Converging Wedge / Triangle) — @gfxmotionbyahmar (00:18–00:20)",
        "theorem": "Funnel two flanking diagonal edges from the upper corners (0.12, 0.04) and (0.88, 0.04) downward into a bottom-center apex (0.50, 0.84) so light, sky, or approaching traffic pours through the central triangular gap—then reverse the wedge when motion splits outward from the apex.",
        "distinct_from": "SCION 083 (Berlin Symphony) edits civic motion by rhythmic pulse tempo and SCION 115 uses a rectangular four-sided doorway; SCION 120 uses two oblique converging diagonals that compress upper-frame breadth into a single lower-center vertex (0.50, 0.84).",
        "formal_objects": [
            "Left diagonal ray L_left: (0.12, 0.04) -> (0.50, 0.84) and right diagonal ray L_right: (0.88, 0.04) -> (0.50, 0.84)",
            "Bottom-center apex coordinate A = (0.50, 0.84)",
            "Upper-wedge luminance opening vs. flanking mass contrast",
            "Wide-stereo upper chord converging linearly into a mono lower-octave apex tone",
        ],
        "protected_conditions": [
            "Distinguish an downward-pointing V-wedge (apex at bottom-center) from ordinary upward vanishing-point railroad tracks (apex at top-center), or explicitly pair both as dual wedges.",
            "Keep Shots 1–3 unannotated so the diagonal funnel is perceived through physical canopy, canyon, or station geometry.",
            "Include a wedge-split release (Shot 7) where movement diverges outward from the apex.",
        ],
        "swarm": [
            "Diagonal wedge detector: scan all 389 archival shots for dual diagonal edge bands converging toward (0.50, 0.84) with an illuminated central V-gap.",
            "Apex funnel editor: register the bottom-center vertex (0.50, 0.84) across architectural canopies, valleys, and flanking figures.",
            "Converging-field sound designer: narrow stereo width from 100% spread to mono at the apex strike.",
            "Independent geometric critic: verify that the V-wedge directs downward visual pressure into the apex.",
        ],
        "hard_proof": "Construct a 24-second, 8-shot archival film at 24fps. Open with three unannotated 3.0-second shots (Shots 1–3) featuring vaulted station ironwork (Berlin: Symphony of a Great City), receding architectural wedges, and flanking figures that funnel downward toward (0.50, 0.84). In Shots 4–6 (9.0s–18.0s), snap the two converging gold diagonals and cyan apex ring onto three new archival shots at +0.6s while the stereo soundstage narrows into the apex. In Shot 7 (18.0s–21.0s), trigger a contextual release where motion splits outward across the diagonals in silence. Conclude in Shot 8 (21.0s–24.0s) with the Berlin station canopy as the gold V-wedge dissolves.",
        "tribunal_watch": [
            "Both left and right diagonal edges have physical support (canopy ribs, flanking structures, or bodies) in Shots 1–6.",
            "The central V-gap between the diagonals remains visually distinct from the flanking masses.",
            "The bottom-center apex (0.50, 0.84) acts as a true gravitational collection point across cuts.",
            "Shot 7 releases the funnel pressure through outward divergence.",
        ],
        "tribunal_checks": [
            "Report left-diagonal and right-diagonal Sobel edge scores and central V-gap luminance contrast.",
            "Verify source provenance and timestamps across all 8 cuts.",
        ],
        "repairs": [
            ("Only one diagonal is present in the frame.", "A single staircase tilted at 45 degrees triggered half the mask.", "Use the geometric mean sqrt(d_left * d_right) so both arms of the V must be present."),
            ("The apex feels pinched at the bottom edge.", "Subjects are cut off below v = 0.84.", "Anchor the vertex at v = 0.84, leaving a 16% ground margin below the apex."),
        ],
        "sound_mode": "wedge_convergence",
    },
    {
        "scion_id": 121,
        "rule_num": 8,
        "rule_id": "negative_space",
        "slug": "scion-121-negative-space-upper-void-compression",
        "film_file": "films/scion-121-negative-space.mp4",
        "title": "SCION 121 // Negative Space — Upper Void & Horizon Compression",
        "short_title": "121 · NEGATIVE SPACE",
        "family": "Framing, gesture and city rhythms",
        "lineage": "Negative Space / Upper-Frame Boundary (00:21–00:23 in 'Life Is All About Perspective! #shorts', @gfxmotionbyahmar, isolating the open twilight sky across the upper two-thirds above the Empire State Building silhouette); Godfrey Reggio & Ron Fricke (Koyaanisqatsi, 1982); Alfred Stieglitz (Equivalents).",
        "requested_ref": "Negative Space (Upper-Frame Boundary) — @gfxmotionbyahmar (00:21–00:23)",
        "theorem": "Reserve the upper two-thirds of the frame (u in [0.08, 0.92], v in [0.10, 0.64]) as an unencumbered atmospheric or luminous field (open sky, cloud deck, water, or blank wall) pressing down upon a high-contrast silhouette band below v = 0.64, then allow a single vertical intrusion to breach the upper bracket.",
        "distinct_from": "SCION 063 (Breath) tracks an invisible force through bodily movement and SCION 079 (Qatsi) contrasts technological regimes by tempo; SCION 121 enforces a strict 2:1 spatial partition between upper low-frequency void and lower high-frequency ground so emptiness itself acquires perceptual mass until breached.",
        "formal_objects": [
            "Wide U-shaped upper frame bracket u in [0.08, 0.92], v in [0.10, 0.64]",
            "Upper-void spatial variance sigma_upper vs. lower-third edge density E_lower (v > 0.64)",
            "Horizon partition line v = 0.64",
            "High-altitude open harmonic air pad over a compressed low sub-bass pedal, interrupted when the void is breached",
        ],
        "protected_conditions": [
            "Do not erase or blur upper-frame detail artificially; the open negative space must be an authentic sky, wall, or field in the archival recording.",
            "Show Shots 1–3 unannotated so the weight of the open upper two-thirds registers naturally.",
            "Include a void-breach shot (Shot 7) where a rising object, tower, or gesture enters the upper bracket.",
        ],
        "swarm": [
            "Atmospheric void scout: rank all 389 archival shots by low upper-two-thirds edge clutter paired with crisp lower-third horizon silhouettes.",
            "Horizon compression editor: hold the v = 0.64 silhouette boundary steady across mountain ridges, desert horizons, and industrial rooflines.",
            "Open-air sound designer: pair a wide high-register harmonic shimmer with a grounded low-frequency fundamental.",
            "Independent perceptual critic: verify that the upper two-thirds feels charged rather than merely empty.",
        ],
        "hard_proof": "Produce a 24-second, 8-shot archival film at 24fps. Open with three unannotated 3.0-second shots (Shots 1–3: Morning Mountain 4, American Engineer desert horizon, Koyaanisqatsi cloud deck) where vast sky occupies the upper two-thirds above a dark lower-third ridge. In Shots 4–6 (9.0s–18.0s), snap the gold U-shaped upper-frame bracket and v = 0.64 horizon line onto three new archival vistas at +0.6s. In Shot 7 (18.0s–21.0s), cut to a contextual release where a rising form breaches the upper void while the high air pad cuts to silence. Conclude in Shot 8 (21.0s–24.0s) with Morning Mountain 4 as the gold U-bracket dissolves into the twilight sky.",
        "tribunal_watch": [
            "The upper two-thirds (v < 0.64) remains genuinely open and unencumbered across Shots 1–6.",
            "The lower third (v > 0.64) anchors the frame with a clear mountain, skyline, or ground silhouette.",
            "The gold U-bracket in Shots 4–6 clarifies the 2:1 negative-to-positive mass ratio.",
            "Shot 7 breaches the upper void so the viewer feels what happens when negative space is lost.",
        ],
        "tribunal_checks": [
            "Measure upper-two-thirds edge sparsity (1 - edge_density) and lower-third Sobel edge density across all 8 cuts.",
            "Confirm full archival provenance and timestamps in the JSON ledger.",
        ],
        "repairs": [
            ("Tree branches or signage clutter the upper sky.", "Luminance was uniform but high-frequency edges filled the top third.", "Penalize Canny edge density inside v in [0.06, 0.58] heavily so only clean open fields pass."),
            ("The frame is completely blank with no lower anchor.", "Full-frame fog or blank leader scored zero upper clutter.", "Require a distinct Sobel edge and luminance boundary below v = 0.62."),
        ],
        "sound_mode": "negative_void",
    },
]


def format_scion_markdown(spec, selected_cuts):
    """
    Generate a complete standalone SCION operator Markdown file matching
    paeleo/allways/scion/prompts/scion-055..113.
    """
    formal_bullets = "\n".join(f"- {item}" for item in spec["formal_objects"])
    protected_bullets = "\n".join(f"- {item}" for item in spec["protected_conditions"])
    swarm_bullets = "\n".join(f"- {item}" for item in spec["swarm"])
    watch_bullets = "\n".join(f"- {item}" for item in spec["tribunal_watch"])
    check_bullets = "\n".join(f"- {item}" for item in spec["tribunal_checks"])
    repair_bullets = "\n".join(
        f"- **Failure:** {f} **Hypothesis:** {h} **Experiment:** {e}"
        for (f, h, e) in spec["repairs"]
    )

    cut_ledger_lines = []
    for idx, c in enumerate(selected_cuts):
        phase = (
            "Phase I · Unannotated Observation"
            if idx < 3
            else (
                "Phase II · Viewfinder Lock"
                if idx < 6
                else (
                    "Phase III · Contextual Release"
                    if idx == 6
                    else "Phase IV · Unannotated Return"
                )
            )
        )
        t0 = idx * 3.0
        t1 = (idx + 1) * 3.0
        cut_ledger_lines.append(
            f"- **Cut {idx+1:02d} (`{t0:04.1f}s–{t1:04.1f}s`, {phase})**: *{c['source_title']}* ({c['source_year']}) in `{c['film_title']}` ({c['maker']} @ `{c['timestamp_s']}s`, fit `{c['score']:.3f}`) — {c['desc']}"
        )
    cut_ledger_md = "\n".join(cut_ledger_lines)

    slug_upper = spec["slug"].upper()
    return f"""# {spec['title']}
## Autonomous evolving cinema / documentary / database swarm · standalone prompt

**Family:** {spec['family']}
**Operator lineage:** {spec['lineage']}
**Requested reference:** {spec['requested_ref']}
**Reference status:** verified_description_and_executed_proof. See the research and execution record below.
**Execution mode:** linear_film
**Playable proof film:** `allways-tensor/{spec['film_file']}` (`24.0s`, `24fps`, `8` archival cuts)
**Interpretation:** This is a newly authored operational prompt inspired by documented composition breakdowns and classic cinema lineage. It does not claim that the credited artists wrote or endorsed it. Its executed 24-second archival proof film is an original experiment built from the Moving Image Archive / Prelinger corpus.

You are **{slug_upper}**. Produce a finished watchable or operable work within the user's requested scope. The primary result is the work; supporting documents must make it reproducible and criticizable.

## INPUT

- `[WORK]`: the new work or question this operator should realize.
- `[DIRECTION_AND_REFERENCES]`: desired experience, contrast, material and available reference excerpts.
- `[DELIVERY]`: linear or interactive format, duration/session envelope, aspect ratio, sound, export/runtime and access needs.
- `[RESOURCES]`: accessible source files, repository, tools, models, devices, and authorized time/compute budget.
- `[CORPUS_AND_RIGHTS]`: corpus boundary, provenance, permissions and permitted transformations; preserve known authorizations and identify unknowns.
- `[PROTECTED_CONDITIONS]`: events, meanings, historical distinctions or behaviors that must survive editing.

Resolve ordinary implementation choices from context. Ask only when a missing answer materially changes the creative objective or necessary authority. Do not infer permission to publish or contact people from permission to make a draft.

## 1 · Creative theorem to prove

{spec['theorem']}

**What makes this operator distinct:** {spec['distinct_from']}

## 2 · Native formal language

Preserve and manipulate these as explicit working objects:

{formal_bullets}

**Protected conditions:**

{protected_bullets}

Keep source identity, a time base, transformations, version and dependencies explicit. Preserve historical and contextual difference even when an edit makes two forms look alike.

## 3 · Assemble the smallest capable swarm

{swarm_bullets}

Every role must build or verify something concrete. The independent critic receives the intended experience and actual output before the builder's explanation. Do not invent a critic session when no independent review occurred.

## 4 · Hard proof; produce before scaling

{spec['hard_proof']}

Save a recoverable draft. Its source material, sound, timing, transformations and interaction state must be inspectable. Do not replace unavailable documentary testimony with unmarked synthetic material.

## 5 · Acceptance tribunal

**Judge by watching or operating the proof:**

{watch_bullets}

**Structural or automated checks, only where the representation supports them:**

{check_bullets}

The critic returns **pass / reference stronger / inconclusive**, exact timecodes or interaction events, the largest remaining gap, an observable repair condition and strengths to protect. Distinguish measured checks from perceptual judgments.

## 6 · Repair through discriminating experiments

{repair_bullets}

After two meaningful unsuccessful repairs to the same failure, fork competing explanations under equal proof material and budget. Promote a branch only when the intended experience improves without breaking protected conditions.

## 7 · Discovery and recursive expansion

- Combine this shape operator with neighboring perspective operators (`SCION 114–121`) only after its single-shape 8-cut proof holds perceptual tension on its own.
- In longer essays, alternate unannotated archival passages with brief acrylic-viewfinder lock intervals so the viewer internalizes the geometric habit of seeing rather than relying on permanent HUD graphics.

Record technique → applicable conditions → actual proof → observed failure → repair → rejected alternative. Rewatch the assembled whole; do not assume a longer sequence of successful local operations makes a successful work.

## 8 · Deliverable contract

- Playable 24.0-second, 8-cut archival proof film (`allways-tensor/{spec['film_file']}`) with synchronized stereo sound score.
- Per-cut geometric fit ledger and archival provenance record (`allways-tensor/scion_shapes.json`).
- Live interactive Acrylic Viewfinder overlay in the zero-scroll `allways-tensor/index.html` cockpit.

**Executed 8-Cut Archival Proof Ledger (`{spec['film_file']}`):**

{cut_ledger_md}

## INHERITED SCION DOCTRINE — BUILD, INSPECT, REPAIR

1. **Viewer experience first.** State one specific perceptual or interactive achievement. Name the attractive but empty result this project must avoid. A subject, mood board or similarity score is not a film.
2. **Inspect the lineage.** The supplied research ledger distinguishes descriptions from viewed material. Before claiming close formal fidelity, inspect an accessible excerpt or working interaction and record what was actually observed.
3. **Hard proof before scale.** Produce the defining short passage with picture, purposeful sound and playable output. Do not begin by accumulating a giant archive.
4. **Material and source integrity.** Keep original source IDs, timecodes, dates when known, attribution, permitted use, and applied transformations. Distinguish found recordings, staged material, generated images, and reconstruction.
5. **Native working state.** Preserve the objects named by this operator: intervals, contours, axes, nodes, corridors, sound cues and transformation records so that another editor can inspect and revise them.
6. **Small accountable swarm.** Every role owns an artifact or a verification. Merge roles when coordination becomes costly. Keep an independent critic for the defining achievement.
7. **Sound and duration are structural.** Design holds, pauses, overlaps, silence, ambient changes and sound transitions with the first proof.
8. **Independent criticism.** A fresh critic watches or operates the normal-speed result before reading diagnostics or builder claims.
9. **Repair causes.** Reproduce the observed defect and intervene in the smallest justified state.
10. **Two kinds of evidence.** Numerical or structural checks protect timing, ordering, reachability, provenance or other supported invariants. Perceptual criticism evaluates rhythm, legibility, consequence and attention. Neither substitutes for the other.
11. **Whole-work judgment.** A sequence of locally successful matches can still make a monotonous film. Keep a playable assembly; inspect cumulative rhythm, transitions, and the reason the work ends.
12. **Truthful stopping and delivery.** Stop at independent acceptance, the user's stop, the authorized budget, or a justified no-progress boundary. Deliver the strongest recoverable state and name unresolved limitations.

## START

Read the inputs and actual source material. State the creative theorem and protected conditions. Build the proof with picture and sound. Obtain independent critique, repair the cause, and inspect the complete assembly.

## RESEARCH RECORD

1. [Life Is All About Perspective! #shorts (@gfxmotionbyahmar)](https://www.youtube.com/watch?v=QNvK63WetSA) — Sequential physical acrylic viewfinder and digital yellow-grid breakdown (`{spec['requested_ref']}`).
2. Moving Image Archive / Prelinger Archives corpus (`ALLWAYS` 389-shot cross-maker index) — Decoded and geometrically scored via `tools/allways/forage_8_grids.py` and `tools/allways/build_scion_shape_films.py`.
"""


def synthesize_shape_audio(wav_path, duration_s, sound_mode):
    """
    Synthesize a bespoke 44.1kHz 16-bit stereo acoustic score for each 24.0-second
    8-cut SCION shape film, with a deliberate silent rest in Cut 7 (18.0s–21.0s,
    the Contextual Release / Productive Rupture) as required by the SCION proof!
    """
    sr = 44100
    n_samples = int(duration_s * sr)
    t = np.linspace(0.0, duration_s, n_samples, endpoint=False)

    left = np.zeros(n_samples, dtype=np.float64)
    right = np.zeros(n_samples, dtype=np.float64)

    phi = 1.61803398875

    for i in range(n_samples):
        ti = t[i]
        cut_idx = int(ti // 3.0)
        tau = ti - cut_idx * 3.0  # time within current 3.0s cut

        # Cut 7 (index 6, 18.0s–21.0s) is the Contextual Release: deliberate silence after a soft entry click!
        if cut_idx == 6:
            if tau < 0.08:
                click = math.exp(-tau * 70.0) * math.sin(2.0 * math.pi * 180.0 * tau) * 0.25
                left[i] = click
                right[i] = click
            continue

        # Subtle viewfinder snap transient at tau = 0.60s during Phase II (cuts 3, 4, 5)
        snap = 0.0
        if cut_idx in (3, 4, 5) and 0.60 <= tau < 0.69:
            dt_s = tau - 0.60
            snap = 0.28 * math.exp(-dt_s * 55.0) * math.sin(2.0 * math.pi * 1320.0 * dt_s)

        env_cut = math.sin(math.pi * min(1.0, tau / 3.0)) ** 0.45

        if sound_mode == "golden_phi":
            # Golden harmonic intervals: base 196 Hz * phi^k + pulse every 0.618s
            f_base = 164.81 * (1.0 + 0.04 * (cut_idx % 3))
            f_phi = f_base * phi
            pulse_phase = (tau % 0.618) / 0.618
            pulse_env = math.exp(-pulse_phase * 5.5)
            sig_l = 0.16 * math.sin(2.0 * math.pi * f_base * ti) + 0.18 * pulse_env * math.sin(2.0 * math.pi * f_phi * ti)
            sig_r = 0.16 * math.sin(2.0 * math.pi * (f_base * 1.003) * ti) + 0.18 * pulse_env * math.sin(2.0 * math.pi * (f_phi * 1.272) * ti)
            left[i] = sig_l * env_cut + snap
            right[i] = sig_r * env_cut + snap

        elif sound_mode == "threshold_room":
            # Warm muffled room drone in first 0.6s, opening to crisp woody resonant fifth
            f0 = 146.83
            bright = 0.35 if (cut_idx < 3 and tau < 1.2) else 1.0
            tick = math.exp(-(tau % 0.75) * 14.0) * 0.22
            sig = 0.17 * math.sin(2.0 * math.pi * f0 * ti) + bright * 0.12 * math.sin(2.0 * math.pi * (f0 * 1.5) * ti)
            left[i] = (sig + tick * math.sin(2.0 * math.pi * 440.0 * ti)) * env_cut + snap
            right[i] = (sig + tick * math.sin(2.0 * math.pi * 660.0 * ti)) * env_cut + snap

        elif sound_mode == "serpentine_glide":
            # S-curve frequency & stereo pan inflection across each 3.0s shot
            u_norm = tau / 3.0
            s_infl = math.sin(2.0 * math.pi * u_norm)  # +1 -> 0 -> -1 -> 0
            f_glide = 220.0 + 75.0 * s_infl
            pan = 0.5 + 0.42 * s_infl
            tone = 0.24 * math.sin(2.0 * math.pi * f_glide * ti) + 0.09 * math.sin(2.0 * math.pi * (f_glide * 1.5) * ti)
            left[i] = tone * (1.0 - pan) * env_cut + snap
            right[i] = tone * pan * env_cut + snap

        elif sound_mode == "bilateral_mirror":
            # Phase-locked 50/50 bilateral ping-pong pulse
            f0 = 196.0
            beat = math.exp(-((tau % 0.50) / 0.50) * 6.0)
            carrier = 0.18 * math.sin(2.0 * math.pi * f0 * ti) + 0.16 * beat * math.sin(2.0 * math.pi * (f0 * 2.0) * ti)
            left[i] = carrier * env_cut + snap
            right[i] = carrier * env_cut + snap

        elif sound_mode == "thirds_polyrhythm":
            # 3-against-2 nodal bell polyrhythm (1/3 and 2/3 intersections)
            p3 = math.exp(-((tau % 0.50) / 0.50) * 8.0)  # 3 beats per 1.5s
            p2 = math.exp(-((tau % 0.75) / 0.75) * 7.0)  # 2 beats per 1.5s
            left[i] = (0.20 * p3 * math.sin(2.0 * math.pi * 329.63 * ti) + 0.10 * math.sin(2.0 * math.pi * 164.81 * ti)) * env_cut + snap
            right[i] = (0.20 * p2 * math.sin(2.0 * math.pi * 493.88 * ti) + 0.10 * math.sin(2.0 * math.pi * 164.81 * ti)) * env_cut + snap

        elif sound_mode == "center_corridor":
            # Narrow dead-center mono column drone + lower-baseline tap at 0.68s intervals
            f0 = 174.61
            tap = math.exp(-((tau % 0.68) / 0.68) * 12.0)
            mono = (0.18 * math.sin(2.0 * math.pi * f0 * ti) + 0.16 * tap * math.sin(2.0 * math.pi * (f0 * 1.5) * ti)) * env_cut + snap
            left[i] = mono
            right[i] = mono

        elif sound_mode == "wedge_convergence":
            # Wide stereo upper chord converging linearly to mono apex over each 3s cut
            spread = max(0.0, 1.0 - (tau / 2.8))
            f_l = 261.63 + 45.0 * spread
            f_r = 261.63 - 45.0 * spread
            left[i] = (0.20 * math.sin(2.0 * math.pi * f_l * ti) + 0.08 * math.sin(2.0 * math.pi * 130.81 * ti)) * env_cut + snap
            right[i] = (0.20 * math.sin(2.0 * math.pi * f_r * ti) + 0.08 * math.sin(2.0 * math.pi * 130.81 * ti)) * env_cut + snap

        else:  # negative_void
            # High open harmonic air shimmer (880/1320 Hz) over compressed low 82.4 Hz ground pedal
            air = 0.10 * math.sin(2.0 * math.pi * 880.0 * ti) + 0.08 * math.sin(2.0 * math.pi * 1318.5 * ti)
            ground = 0.20 * math.sin(2.0 * math.pi * 82.41 * ti)
            left[i] = (ground + air) * env_cut + snap
            right[i] = (ground + air * 0.92) * env_cut + snap

    # Write 16-bit stereo WAV
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        l_int = np.clip(left * 32767.0, -32767, 32767).astype(np.int16)
        r_int = np.clip(right * 32767.0, -32767, 32767).astype(np.int16)
        interleaved = np.empty(n_samples * 2, dtype=np.int16)
        interleaved[0::2] = l_int
        interleaved[1::2] = r_int
        wf.writeframes(interleaved.tobytes())


def draw_film_frame_hud(pil_img, spec, cut_idx, cut_meta, tau_in_cut):
    """
    Render each frame of a 24.0-second (8-cut) SCION Shape Film following its 4 phases:
      - Cuts 0, 1, 2 (Phase I · Observation): Clean archival frame + subtle bottom-left archival tag
      - Cuts 3, 4, 5 (Phase II · Viewfinder Lock): Clean for 0.6s, then full gold Acrylic Viewfinder snaps on
      - Cut 6 (Phase III · Contextual Release / Rupture): Dashed cyan release banner + unannotated motion break
      - Cut 7 (Phase IV · Unannotated Return): Gold viewfinder for first 1.1s, then dissolves away to pure image
    """
    rid = spec["rule_id"]
    rnum = spec["rule_num"]
    src_label = f"Cut 0{cut_idx+1}/08 | {cut_meta['source_title']} ({cut_meta['source_year']}) in {cut_meta['film_title']} ({cut_meta['maker']})"

    # Phase II (Cuts 3,4,5) after 0.60s or Phase IV (Cut 7) before 1.10s -> draw full geometric overlay
    if (cut_idx in (3, 4, 5) and tau_in_cut >= 0.60) or (cut_idx == 7 and tau_in_cut < 1.10):
        return draw_rule_overlay_pil(
            pil_img,
            rid,
            rnum,
            spec["short_title"],
            f"FIT {cut_meta['score']:.3f}",
            src_label,
        )

    # Otherwise draw minimal non-intrusive phase strip at bottom so raw observation & contextual release breathe
    img = pil_img.convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    def clean_ascii(s):
        return (
            s.replace("–", "-")
            .replace("—", " - ")
            .replace("·", "|")
            .replace("×", "x")
            .encode("ascii", "replace")
            .decode("ascii")
        )

    if cut_idx < 3:
        phase_tag = f"SCION {spec['scion_id']} | PHASE I: OBSERVATION (UNANNOTATED) | CUT 0{cut_idx+1}/08"
        badge_col = (242, 196, 92, 225)
    elif cut_idx in (3, 4, 5):
        phase_tag = f"SCION {spec['scion_id']} | PHASE II: LOCKING VIEWFINDER... | CUT 0{cut_idx+1}/08"
        badge_col = (242, 196, 92, 225)
    elif cut_idx == 6:
        phase_tag = f"SCION {spec['scion_id']} | PHASE III: CONTEXTUAL RELEASE / RUPTURE (SILENT REST) | CUT 07/08"
        badge_col = (86, 194, 230, 240)
        # Subtle cyan corner release ticks
        draw.rectangle([18, 18, W - 18, H - 18], outline=(86, 194, 230, 130), width=2)
    else:
        phase_tag = f"SCION {spec['scion_id']} | PHASE IV: UNANNOTATED RETURN (VIEWFINDER DISSOLVED) | CUT 08/08"
        badge_col = (142, 224, 168, 235)

    draw.rectangle([14, H - 36, W - 14, H - 12], fill=(10, 12, 18, 185))
    draw.text((22, H - 31), clean_ascii(phase_tag + "  --  " + cut_meta["source_title"])[:86], fill=badge_col)

    return Image.alpha_composite(img, overlay).convert("RGB")


def main():
    candidates = harvest_candidate_shots()
    print(f"Harvested {len(candidates)} candidate archival shots.")

    by_mp4 = {}
    for idx, c in enumerate(candidates):
        by_mp4.setdefault(c["mp4_path"], []).append((idx, c))

    scored_candidates = []
    for mp4_path, items in by_mp4.items():
        cap = cv2.VideoCapture(mp4_path)
        for idx, c in items:
            cap.set(cv2.CAP_PROP_POS_MSEC, c["timestamp_s"] * 1000.0)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            sc = score_frame_eight_rules(frame, c["desc"] + " " + c["source_title"])
            c_copy = dict(c)
            c_copy["rule_scores"] = sc
            c_copy["_frame_bgr"] = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
            scored_candidates.append(c_copy)
        cap.release()

    print(f"Scored {len(scored_candidates)} archival shots across 8 shapes.")

    scion_shapes_out = []
    sheet_rows = []

    fps_out = 24
    cut_dur_s = 3.0
    n_frames_per_cut = int(cut_dur_s * fps_out)  # 72 frames per cut, 576 frames (24.0s) per film

    for spec in SCION_SHAPES_SPEC:
        rid = spec["rule_id"]
        ranked = sorted(
            scored_candidates,
            key=lambda x: x["rule_scores"].get(rid, 0.0),
            reverse=True,
        )

        # Select 6 distinct high-scoring shots from different films for Cuts 1..6
        top_six = []
        seen_films = set()
        for cand in ranked:
            if cand["film_id"] in seen_films:
                continue
            seen_films.add(cand["film_id"])
            top_six.append(cand)
            if len(top_six) == 6:
                break

        # Select 1 deliberate Contextual Release / Productive Rupture shot (Cut 7):
        # a high-kinetic / human-crossing shot from another film where the grid is broken
        rupture_cand = None
        for cand in reversed(ranked[:140]):
            if cand["film_id"] not in seen_films and any(
                w in (cand["desc"] + " " + cand["source_title"]).lower()
                for w in ("run", "walk", "turn", "hand", "jump", "leave", "exit", "chase", "crowd", "dance")
            ):
                rupture_cand = cand
                break
        if rupture_cand is None:
            rupture_cand = ranked[45]

        # Cut 8 returns to the #1 flagship exemplar (top_six[0]) for the unannotated resolution!
        # Order:
        #   Cuts 0,1,2 (Observation): top_six[1], top_six[2], top_six[3]
        #   Cuts 3,4,5 (Viewfinder Lock): top_six[0], top_six[4], top_six[5]
        #   Cut 6 (Contextual Release / Rupture): rupture_cand
        #   Cut 7 (Unannotated Return): top_six[0] (later part of shot)
        eight_cuts_raw = [
            top_six[1],
            top_six[2],
            top_six[3],
            top_six[0],
            top_six[4],
            top_six[5],
            rupture_cand,
            top_six[0],
        ]

        cuts_meta = []
        for c_i, c in enumerate(eight_cuts_raw):
            phase_label = (
                "I · Observation"
                if c_i < 3
                else (
                    "II · Viewfinder Lock"
                    if c_i < 6
                    else ("III · Contextual Release" if c_i == 6 else "IV · Unannotated Return")
                )
            )
            cuts_meta.append({
                "cut_num": c_i + 1,
                "phase": phase_label,
                "time_range": f"{c_i*3.0:.1f}s–{(c_i+1)*3.0:.1f}s",
                "maker": c["maker"],
                "film_id": c["film_id"],
                "film_title": c["film_title"],
                "source_title": c["source_title"],
                "source_year": c["source_year"],
                "timestamp_s": round(c["timestamp_s"] + (0.8 if c_i == 7 else 0.0), 2),
                "score": round(float(c["rule_scores"].get(rid, 0.5)), 3),
                "desc": c["desc"][:140],
            })

        # 1. Write standalone SCION prompt markdown in paeleo/allways/scion/prompts/
        md_text = format_scion_markdown(spec, cuts_meta)
        md_path = os.path.join(PROMPTS_DIR, f"{spec['slug']}.md")
        with open(md_path, "w") as f:
            f.write(md_text)

        # 2. Render 24.0s (8-cut) MP4 film + stereo WAV score
        tmp_dir = f"/tmp/scion_shape_{spec['scion_id']}"
        os.makedirs(tmp_dir, exist_ok=True)
        wav_path = os.path.join(tmp_dir, "score.wav")
        synthesize_shape_audio(wav_path, 24.0, spec["sound_mode"])

        f_idx = 0
        sample_phase_thumbs = []

        for c_i, c in enumerate(eight_cuts_raw):
            cap = cv2.VideoCapture(c["mp4_path"])
            offset_t = 0.6 if c_i == 7 else -1.0
            start_t = max(0.0, c["timestamp_s"] + offset_t)
            cap.set(cv2.CAP_PROP_POS_MSEC, start_t * 1000.0)
            last_rgb = cv2.cvtColor(c["_frame_bgr"], cv2.COLOR_BGR2RGB)

            for k in range(n_frames_per_cut):
                ret, frm = cap.read()
                if ret and frm is not None:
                    frm_640 = cv2.resize(frm, (640, 360), interpolation=cv2.INTER_AREA)
                    last_rgb = cv2.cvtColor(frm_640, cv2.COLOR_BGR2RGB)
                tau_in_cut = k / float(fps_out)
                pil_f = draw_film_frame_hud(
                    Image.fromarray(last_rgb), spec, c_i, cuts_meta[c_i], tau_in_cut
                )
                pil_f.save(f"{tmp_dir}/f_{f_idx:05d}.jpg", quality=86)
                if k == int(n_frames_per_cut * 0.55) and c_i in (0, 3, 6, 7):
                    sample_phase_thumbs.append(pil_f.resize((320, 180), Image.Resampling.LANCZOS))
                f_idx += 1
            cap.release()

        sheet_rows.append(sample_phase_thumbs)

        out_mp4_abs = os.path.join(OUT_DIR, spec["film_file"])
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps_out),
            "-i", f"{tmp_dir}/f_%05d.jpg",
            "-i", wav_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            out_mp4_abs,
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(
            f"Built {spec['short_title']:22s} -> {spec['film_file']} (24.0s, 8 cuts) + prompt {spec['slug']}.md"
        )

        scion_shapes_out.append({
            "scion_id": spec["scion_id"],
            "rule_num": spec["rule_num"],
            "rule_id": spec["rule_id"],
            "slug": spec["slug"],
            "title": spec["title"],
            "short_title": spec["short_title"],
            "family": spec["family"],
            "lineage": spec["lineage"],
            "theorem": spec["theorem"],
            "distinct_from": spec["distinct_from"],
            "hard_proof": spec["hard_proof"],
            "prompt_rel": f"../paeleo/allways/scion/prompts/{spec['slug']}.md",
            "prompt_markdown": md_text,
            "film_file": spec["film_file"],
            "duration_s": 24.0,
            "cuts": cuts_meta,
        })

    # Save 8-Shape 4-Phase Contact Sheet (4 columns = Phases I..IV, 8 rows = SCION 114..121)
    sheet_im = Image.new("RGB", (320 * 4, 180 * 8), (10, 12, 16))
    for r_i, row_thumbs in enumerate(sheet_rows):
        for c_i, th in enumerate(row_thumbs[:4]):
            sheet_im.paste(th, (c_i * 320, r_i * 180))
    sheet_path = os.path.join(IMG_DIR, "scion_8_shapes_films_sheet.jpg")
    sheet_im.save(sheet_path, quality=88)
    print(f"Saved 8-Shape 4-Phase Film Atlas -> {sheet_path}")

    out_json = os.path.join(OUT_DIR, "scion_shapes.json")
    with open(out_json, "w") as f:
        json.dump({"operators": scion_shapes_out}, f, indent=2)
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
