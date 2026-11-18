"""Write anim/rig.json: the typed joint graph per panel (SCION #32), read from the page builder's own pivots/matrices."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import panels
from panels import bp

def L(p): return [round(float(p[0]), 2), round(float(p[1]), 2)]
src = "source coords = Rothstein 8b16710u master at every 3rd px (cutout pieces' frame); panel px = page px"
clerk = {"type": "body", "frame": src, "joints": [
    {"id": "root", "parent": None, "piece": "clerk.torso", "pivot_src": L(bp.ROOT_), "dof": "panel transform (translate/rotate/mirror) = the clerk's place"},
    {"id": "collar", "parent": "root", "piece": "clerk.head", "pivot_src": L(bp.COLLAR), "dof": "rotate (head, deg)", "limits_deg": [-15, 18]},
    {"id": "elbow", "parent": "root", "piece": "clerk.forearm", "pivot_src": L(bp.ELBOW), "dof": "rotate (arm, deg)", "limits_deg": [-40, 10],
     "note": "the shoulder->upper arm is part of the torso piece as photographed; the rig's pencil-arm hinge is the elbow"},
    {"id": "grip", "parent": "elbow", "piece": "clerk.pencil", "pivot_src": L(bp.GRIP), "dof": "rotate (pencil, deg)", "tip_src": L(bp.TIP)},
    {"id": "chin", "parent": "collar", "piece": None, "point_src": L(bp.CHIN), "dof": "target (pencil tip meets it in P8)"}],
    "order": ["clerk.torso", "clerk.head", "clerk.forearm", "clerk.pencil"], "pose_chin": panels.POSE_CHIN,
    "pose_source": panels.POSE_SOURCE, "pose_arrive": panels.POSE_ARRIVE}
door = {"type": "set", "joints": [
    {"id": "cupboard", "parent": None, "piece": "set.plate", "dof": "fixed"},
    {"id": "jamb", "parent": "cupboard", "piece": None, "edge_src": [[bp.DOOR_BOX[0], bp.DOOR_BOX[1]], [bp.DOOR_BOX[0], bp.DOOR_BOX[1] + bp.DOOR.shape[0]]], "dof": "fixed hinge edge"},
    {"id": "door", "parent": "jamb", "piece": "cupboard.door", "dof": "swing theta deg: scaleX=|cos theta| about the jamb, outer face theta<90, inner face (mirrored, shade .78) theta>90; far edge grows 5.3%*sin theta (comes toward us)", "rest_theta_deg": 109.88},
    {"id": "hook", "parent": "door", "piece": "hook (handmade)", "point_door_uv": [0.52, 0.40]},
    {"id": "key", "parent": "hook", "piece": "key", "pivot": "ring_top", "dof": "none: constant offset (0, 8*s) below the hook"},
    {"id": "tag", "parent": "key", "piece": "tag (handmade)", "dof": "none"}]}
clock = {"type": "mechanism", "joints": [
    {"id": "case", "parent": None, "piece": "clock.case"},
    {"id": "arbor", "parent": "case", "pivot": "arbor", "children": ["clock.hour", "clock.minute"], "dof": "rotate each hand; minute steps 6 deg per minute", "rest": "4:10 (hour 125 deg, minute 60 deg)"}]}
lamp = {"type": "pendulum", "joints": [{"id": "cord_top", "parent": None, "piece": "lamp (GrabCut from P6 plate + cord band)", "dof": "rotate deg about the cord top", "rest_deg": 0}]}
visitor = {"type": "layer behind glass", "joints": [{"id": "visitor", "parent": "glass", "piece": "visitor", "dof": "translate x (panel px), diffused 3 px, 70% transmission"}]}
def balloon(i): return {"type": "dropped paper object", "id": i, "dof": "translate y (rigid with its tail); drop -150,-55,+9,0 over 4 frames on ones; lands on the page position"}
rig = {"what": "typed joint graph per panel; transforms compose parent @ about(pivot, R(angle)) in source coords, then the panel placement",
       "builder": "page/build_page.py (page-cartoonist) lays the rest pose; anim/panels.py overrides only these DOFs per frame",
       "panels": {"P1": {"clerk": clerk}, "P2": {"clerk": clerk, "note": "seated pose = inverse of the page's lift"},
                  "P3": {"clerk": clerk, "walk": "Gilliam stepping slide: root translate on twos, bob +-14 src px (= +-5.9 page px), head lags one pose"},
                  "P4": {"clerk": clerk, "visitor": visitor, "balloons": [balloon("b_what_time")]},
                  "P5": {"clerk": clerk, "clock": clock, "balloons": [balloon("b_ten_past")]},
                  "P6": {"lamp": lamp, "balloons": [balloon("b_thanks")]},
                  "P7": {"clerk": clerk, "cupboard": door}, "P8": {"clerk": clerk, "cupboard": door, "balloons": [balloon("b_forgot")]}}}
json.dump(rig, open(HERE / "rig.json", "w"), indent=1)
print("ok")
