"""Export the multiplane scene graph and the camera / focus / exposure / atmosphere curves (proof/scene.json)."""
import json, os
from common import *
import render as R


def main():
    planes = json.load(open(os.path.join(CACHE, 'planes', 'planes.json')))
    graph = dict(
        units='metres; X along the porch (score x), Y up, Z depth from the camera origin; t seconds of the 32 s scene',
        camera=dict(focal_px=F, principal=[CX, CY], height_m=CAM_Y, aperture_px_per_rel_depth=APERTURE,
                    pan_keys=CAM_X, truck_keys=CAM_Z),
        glass_planes=[dict(name=p['name'], z=p['z'], rect_m=[p['X0'], p['Y0'], p['X1'], p['Y1']], px_per_m=p['ppm']) for p in planes] + [
            dict(name='door_leaf', z='5.05..5.97 (hinged, swings in)', dynamic=True),
            dict(name='floors (interior, yard, porch boards, sill, step, fascia, ground)', z='ray-cast per pixel', dynamic=True),
            dict(name='person (cutout)', z='5.02 -> 4.70', dynamic=True),
            dict(name='dog (cutout, re-cut from maquette)', z='4.55 -> 4.81', dynamic=True)],
        fog_fields=[dict(z=22.0, source='cloud bank edge', profile='prof_far'), dict(z=Z['fog_far'], source='cloud bank edge', profile='prof_far'),
                    dict(z=5.6, source='cloud interior', profile='uniform, warm (room haze)'),
                    dict(z=4.88, source='cloud interior', profile='prof_back: haze between the cutouts and the wall'),
                    dict(z=Z['fog_porch'], source='cloud bank edge (top at 1.55 m)', profile='prof_porch: bank between door and dog; actor states'),
                    dict(z=Z['fog_near'], source='cloud bank edge (top at 0.75 m)', profile='prof_near: ground fog in front of the porch')],
        order_far_to_near=['sky', 'trees_far', 'fog 22', 'trees_near', 'yard', 'fog 10', 'interior_wall', 'interior floor', 'interior_near',
                           'room haze 5.6', 'door leaf + jamb reveals', 'wall', 'porch floor + shadows', 'fog 4.88', 'person / dog (by depth)',
                           'fog 4.25', 'posts + eave', 'fog 2.9', 'leaves', 'grass'],
        light=dict(lamp=R.LAMP.tolist(), model='a ray from the lamp through each lit point must pass the open part of the doorway '
                   '(left jamb to the leaf free edge); falloff with distance; held back by the person while in the doorway'),
    )
    curves = []
    for i in range(0, N, 2):
        t = i / FPS
        c = cam(t)
        curves.append(dict(t=round(t, 3), cam_x=round(c[0], 4), cam_z=round(c[2], 4), focus_z=round(focus_z(t), 3),
                           door_deg=round(door_angle(t), 2), light=round(R.light_level(t), 3), exposure=round(R.ambient(t), 3),
                           atmosphere=R.atmosphere_state(t), fog_drift_m=round(R.drift(t), 3)))
    graph['curves_every_2_frames'] = curves
    json.dump(graph, open(os.path.join(FOLDER, 'proof', 'scene.json'), 'w'), indent=1)
    print('scene.json', len(curves))


if __name__ == '__main__':
    main()
