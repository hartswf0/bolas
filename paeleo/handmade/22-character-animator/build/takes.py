"""SCION 22 · the takes.  Character Animator records a performance as takes: one track per behaviour parameter,
layered so that a later take overrides an earlier one only on the parameters it recorded.  No camera and no live performer
exist here, so the 'capture' take is the PAELEO machine's own continuous performance (the score's act tracks, verbatim),
and the take editor (me) records gated trigger, head-turner and gaze takes on top of it.  Writes ../takes.json."""
import json, os
from common import SCORE, N, FPS, FOLDER

fr = SCORE['frames']
r3 = lambda v: round(float(v), 4)

capture = {
    'name': 'Take 1 · capture (machine performance)',
    'kind': 'continuous',
    'source': 'paeleo/handmade/score/threshold-score.json frames[].dog (x, act.*): the PAELEO machine played as the performer',
    'honesty': 'no webcam, no microphone performer, no landmarks: this is the continuous response a live capture would give',
    'params': {k: [r3(f['dog']['act'][k]) for f in fr] for k in ['lie', 'crouch', 'head', 'ear', 'tail', 'wag', 'rest', 'look', 'moving']},
}
capture['params']['x'] = [r3(f['dog']['x']) for f in fr]
capture['params']['turn'] = [r3(f['dog']['act']['turn']) for f in fr]

# Take 2: triggers (Character Animator keyboard triggers / swap sets), the take editor's gated beats
triggers = {
    'name': 'Take 2 · triggers', 'kind': 'trigger',
    'note': 'each trigger is a gated, held beat; it fires a swap set or a pose and holds until the next trigger',
    'events': [
        {'t': 1.00, 'trigger': 'Flinch', 'what': 'crouch, ears flat, tail tucked, start backing'},
        {'t': 2.33, 'trigger': 'Hold', 'what': 'stops, watches'},
        {'t': 3.42, 'trigger': 'Turn Away', 'what': 'head leads away (head turner 0 -> 180 via the back of the head), body follows 3.50-4.02 through the Quarter and Back views'},
        {'t': 4.30, 'trigger': 'Lie Down (away)', 'what': 'lies with its back to the door; gated until the turn has finished'},
        {'t': 5.50, 'trigger': 'Chin Down', 'what': 'chin on the paws, facing away'},
        {'t': 7.42, 'trigger': 'Look Back', 'what': 'head comes round over the shoulder to the door while the body is still down'},
        {'t': 7.60, 'trigger': 'Get Up', 'what': 'rises, head held on the door'},
        {'t': 8.02, 'trigger': 'Turn Toward', 'what': 'body follows the head, 180 -> 0 through the Back view'},
        {'t': 14.71, 'trigger': 'Come (head low)', 'what': 'walks; head carried below the back line for the whole approach'},
        {'t': 23.79, 'trigger': 'Lie Down (sill)', 'what': 'lies across the sill: front half in the doorway, tail outside'},
        {'t': 26.40, 'trigger': 'Look In', 'what': 'head turns into the lit room: back of the head to the viewer, muzzle past the jamb'},
        {'t': 28.02, 'trigger': 'Settle', 'what': 'chin back on the paws; stays'},
    ],
}

# Take 3: head & body turner (yaw in degrees in my side view: 0 = facing the door, 90 = facing away from the camera,
# 180 = facing the porch steps).  Keys are eased.
turner = {
    'name': 'Take 3 · head & body turner', 'kind': 'keyed',
    'body_yaw': [[0, 0], [3.50, 0], [4.02, 180], [8.02, 180], [8.56, 0]],
    'head_yaw': [[0, 0], [3.42, 0], [3.80, 180], [7.34, 180], [7.46, 290], [7.56, 360], [26.40, 360], [26.80, 408], [28.02, 408], [28.40, 360]],
    'head_tilt': [[0, 0], [9.6, 0], [9.9, 11], [10.7, 11], [11.0, 0], [12.4, 0], [12.7, -8], [13.4, -8], [13.7, 0], [25.0, 0], [25.3, 7], [26.0, 7], [26.3, 0]],
    'note': 'both body turns pass through the Back view (90): the dog shows its back to the camera while it turns; the head turns back through its Quarter-Front view (270), face toward the camera, so the face comes round first',
}

# Take 4: eye gaze (snap gaze; targets are named points in the world, resolved by the runtime)
gaze = {
    'name': 'Take 4 · eye gaze', 'kind': 'targets', 'snap_frames': 2,
    'events': [[0.0, 'person_face'], [1.0, 'person_face'], [2.5, 'person_hand'], [3.0, 'person_face'], [3.42, 'porch_end'],
               [4.6, 'floor_ahead'], [7.42, 'door_light'], [7.95, 'person_hand'], [9.0, 'person_face'], [10.5, 'person_face'],
               [11.7, 'door_light'], [12.8, 'person_hand'], [13.9, 'person_face'], [14.71, 'sill'], [18.2, 'person_hand'],
               [20.6, 'sill'], [22.4, 'person_hand'], [23.9, 'person_face'], [26.40, 'room'], [28.05, 'person_hand'], [29.6, 'person_face']],
}

# Take 5: the person (position, posture, arms), mapped from the score's person into my room
def pmap(x):
    from common import PERSON_DOORWAY, PERSON_BESIDE
    u = (x - (-0.28)) / (-1.25 - (-0.28))
    return PERSON_DOORWAY + (PERSON_BESIDE - PERSON_DOORWAY) * u

person = {
    'name': 'Take 5 · person', 'kind': 'continuous',
    'source': 'score frames[].person (x, sit, reach, low); place mapped into my room (doorway -0.20 m, beside -0.80 m)',
    'params': {'x': [r3(pmap(f['person']['x'])) for f in fr], 'sit': [r3(f['person']['sit']) for f in fr],
               'reach': [r3(f['person']['reach']) for f in fr], 'low': [r3(f['person']['low']) for f in fr]},
    'events': [[1.0, 'pat thigh (call)'], [3.4, 'reach (call again)'], [6.12, 'pull the door open'], [6.8, 'offer hand low'], [26.1, 'draws the hand back to her lap as she says come in: she asks and does not pull']],
}

edits = [
    'turn: the capture\'s turn track crosses zero only at 4.1 s and would show the back late; the Turn Away trigger leads with the head at 3.42 and has the back to the door by 3.9',
    'lie: the capture starts lying at 4.3 while its turn track is still at -0.47 (lying down mid-turn reads as a collapse); gated until the body turner has finished (4.02)',
    'look in: the capture\'s look track is a continuous ramp up and down; replaced by a held beat (26.80-28.02) on the Quarter-Back head view, so the look reads as a decision and a hold',
    'head on the approach: capture head 0.45 kept, and the neck pivot is held below the back line for the whole walk (rig constraint, measured in trace)',
    'gaze: the capture has no gaze; Take 4 adds snap gaze toward named targets with 2-frame saccades and holds',
]

out = {'about': 'SCION 22 takes: timed control tracks layered like Character Animator takes (later takes override earlier ones on the parameters they record). No camera, no webcam landmarks and no live performer exist here.',
       'fps': FPS, 'frames': N, 'layer_order': [capture['name'], triggers['name'], turner['name'], gaze['name'], person['name']],
       'takes': [capture, triggers, turner, gaze, person], 'editor_corrections': edits}
json.dump(out, open(os.path.join(FOLDER, 'takes.json'), 'w'), indent=1)
print('takes.json', len(out['takes']), 'takes')
