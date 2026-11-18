"""Write films/swarm/le-chant-du-styrene/geometry.json from the GrabCut measurement + constraint graph."""
import json
import numpy as np
import cv2
from layout import *

SW = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene")
bm = cv2.imread(str(OUT / "masks/bare_runner_mask.png"), 0) > 0
bb = json.load(open(OUT / "geom_src.json"))["report"]["pieces"]["bare_runner"]["bbox_src"]
full = np.zeros((G["image_size"][1], G["image_size"][0]), np.uint8); full[bb[1]:bb[1] + bb[3], bb[0]:bb[0] + bb[2]] = bm
dt = cv2.distanceTransform(full, cv2.DIST_L2, 5)
def width_at(p):
    x, y = int(p[0]), int(p[1]); return 2 * float(dt[max(0, y - 6):y + 7, max(0, x - 6):x + 7].max())

def W(p):  # world -> source
    return [float(p[0] + HUB[0]), float(p[1] + HUB[1])]
cams = {"sh1_start": camera(0.0), "sh2a_wide": camera(10.0), "sh2b_hold": camera(16.0)}

def film_all(pw):
    return {k: to_film(pw, c) for k, c in cams.items()}

rings = []
for r in RINGS:
    e = r["ellipse_src"]
    R = (e["major"] + e["minor"]) / 4; ri = ((e["hole"]["major"] + e["hole"]["minor"]) / 4) if e["hole"] else 0.2 * R
    arm = ARMS[r["flight"] - 1]
    poly_src = arm["polyline_src"]
    rings.append(dict(
        ring=r["flight"], loose_piece=f'pieces/{r["piece"]}.png', arm_angle_deg_src=r["arm_angle"],
        ring_ellipse_src=e, outer_R_src=R, inner_r_src=ri,
        rest_centre_src_of_loose_ring=[e["cx"], e["cy"]],
        gate_src=arm["tip_src"], home_centre_src=W(r["home_world"]),
        arm_polyline_src=poly_src, arm_width_src=[width_at(p) for p in poly_src[1:-1]],
        film={k: dict(rest_centre=to_film(r["rest_world"], c), home_centre=to_film(r["home_world"], c),
                      gate=to_film(r["gate_world"], c), outer_R=R * c[1], inner_r=ri * c[1],
                      arm_polyline=[to_film(np.array(p) - HUB, c) for p in poly_src],
                      arm_width=float(np.median([width_at(p) for p in poly_src[1:-1]]) * c[1]))
              for k, c in cams.items()},
        flight_s=list(FLIGHT[r["flight"]]), rot_max_deg=ROT[r["flight"]]))
sp = SPRUE
geo = dict(
    revision="U2 r3 (plan.md r3)",
    source=dict(file="films/sources/le-chant-du-styrene/r2/spritzguss.jpg", title="Spritzguss teile.jpg", author="Gmhofmann",
                license="CC BY-SA 4.0", source_url="https://commons.wikimedia.org/wiki/File:Spritzguss_teile.jpg",
                local_copy_px=G["image_size"], commons_original_px=[2052, 1064]),
    method="cv2.grabCut per region (rectangle seed, outside = sure BG) with HSV hue seeds (teal & S>90 = probable FG, eroded = sure FG, S<45 = sure BG), 6 iters; "
           "largest component kept; pinholes <= 40 px filled; ring fits cv2.fitEllipse on outer/bore contours; arm directions = peaks of the angular mask histogram around the hub (densest 41 px box); tip = farthest mask pixel within +-7 deg.",
    canonical_layout="sh2b_hold: the bare (left) runner of the photograph with its four loose rings homed by the contact constraint. "
                     "This is what is on screen at 15.8-17.6 s and the outline Sh3a must match. The right-hand runner-with-rings of the same photograph is the real evidence that rings sit at the arm tips; its geometry stays in test-shot/geometry.json.",
    band=[BW, BH], fps=FPS,
    coordinates="source = pixels of the 1280x664 local copy; world = source minus hub; film = (world - cam.centre) * cam.zoom + (480, 204) in the 960x408 picture band (no letterbox offset)",
    cameras={k: dict(centre=[float(c[0][0]), float(c[0][1])], zoom=float(c[1])) for k, c in cams.items()},
    camera_note="Sh1 drifts from sh1_start (zoom 1.00) to centre (-548,14) zoom 1.025; Sh2a is static wide; Sh2b glides (smoothstep) from centre (120,-5) zoom 1.12 to sh2b_hold by 15.80 s, then holds.",
    hub_src=[float(HUB[0]), float(HUB[1])], hub_film={k: to_film(np.zeros(2), c) for k, c in cams.items()},
    sprue=dict(note="the short thick post with the open mouth; seen in perspective it projects up-left of the hub",
               tip_src=sp["tip_src"], polyline_src=sp["polyline_src"],
               film={k: dict(tip=to_film(np.array(sp["tip_src"]) - HUB, c), polyline=[to_film(np.array(p) - HUB, c) for p in sp["polyline_src"]]) for k, c in cams.items()}),
    rings=rings,
    timing=dict(ring1_home_frame=312, ring1_home_t=13.000, cut_C1_t=13.02, cut_C1_between_frames=[312, 313],
                flights={str(k): v for k, v in FLIGHT.items()}, settle="spring-damper +-4 deg, zeta 0.35, 3.2 Hz, peak 3.84 deg, ends < 0.01 deg by 15.8 s", hold_from=15.80),
)
json.dump(geo, open(SW / "geometry.json", "w"), indent=1)
print(json.dumps({r["ring"]: (r["film"]["sh2b_hold"]["home_centre"], round(r["film"]["sh2b_hold"]["outer_R"], 1)) for r in rings}))
