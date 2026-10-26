"""../rulebook.json: the rewrite rules (typed inputs/outputs, preconditions, preserved anchors) and when each fired in this render"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); TOP = os.path.dirname(HERE)
gt = json.load(open(os.path.join(TOP, 'graph_trace.json')))['changes']
RULES = [
    dict(id='R1 REPLACE head', kind='replace', input='dog.head', output='dog.head',
         precondition='intention changes (score act.head / state); the new drawing\'s native neck->nose angle within 45 deg of the wanted angle',
         preserved='neck anchor N (the joint), facing', fragments=['head_alert_f006', 'head_level_f012', 'head_low_f048'],
         motif='head up = attention; head low = the decision to come (f048: the dog lowering its head to its bowl, re-used as trust)'),
    dict(id='R2 REPLACE head by the looking-away head', kind='replace', input='dog.head on a turned-away body', output='dog.head facing the door',
         precondition='state becomes watch (7.458, on its own frame) while the body still faces away; legibility: muzzle left of the neck, level (<= 20 deg), head at normal scale, clear of the back, with its own paper rim; the body stays lying (no hybrid) until the found turn frames at 7.75', preserved='neck anchor', fragments=['head_alert_f006 rotated level about its neck (muzzle to the door, 8 deg)'],
         motif='the head comes round first: turning to look'),
    dict(id='R3 MERGE dog -> whole found frame', kind='merge', input='dog graph (head, torso, legs, tail)', output='dog.whole',
         precondition='a turn: |facing| changes sign; the found frame must show the same dog between profiles', preserved='ground point under the body, height 0.80 m (local)',
         fragments=['whole_f027', 'whole_f030'], motif='the turn is never a mirror flip: the real dog turning, two found frames'),
    dict(id='R4 SPLIT whole -> mirrored graph', kind='split', input='dog.whole', output='dog graph facing the other way',
         precondition='the turn is complete', preserved='ground point, anchors S/H/N/T'),
    dict(id='R5 REPLACE legs (stance/swing)', kind='replace', input='dog.leg', output='dog.leg',
         precondition='gait phase: stance -> straight found leg, swing -> bent found leg', preserved='hip/shoulder anchor; a stance foot keeps its world x (visual anchor)',
         fragments=['fore_a/b_f012', 'hind_a/b_f012', 'fore_a/b_f045', 'hind_a/b_f045']),
    dict(id='R6 EXIT legs / lie', kind='exit', input='standing graph', output='lying graph (discrete drawings; hind legs EXIT from 2/3 down; lying at the sill starts half down on its own frame)',
         precondition='score act.lie quantised (thirds; quarters from 1/2 for lie_down)', preserved='body centre x, tail outside', motif='lying is composed: no frame of this dog lies down'),
    dict(id='R7 REPLACE node.material shade -> sun', kind='replace', input='dog node cut from the shaded frames (f006/f012)', output='same node cut from the sunlit frames (f045/f048), blended in by weight',
         precondition='state in {approach, lie_down} AND (node is the head [the decision, weight 1] OR chest/forelegs entering the door light: weight ramps over world x 0.80 -> 0.50 m, about 0.6 s; haunch, hind legs, tail stay 0)',
         preserved='node anchors; the source dog (identity: every piece is the same home-movie dog)', motif='what the dog is made of changes as it comes into the light; the tail never does'),
    dict(id='R8 SPLIT torso at the threshold', kind='split', input='dog.torso', output='shaded torso + sunlit chest laid over it (rear edge feathered, alpha = R7 weight)',
         precondition='chest weight > 0 (R7)', preserved='S and H anchors of the torso', motif='half in, half out, materially'),
    dict(id='R9 ENTER head -> the door light (look in)', kind='enter', input='dog.head', output='head_low_f048 rotated about its neck to a level muzzle (10 deg), the neck reaching in past the jamb at sill height, muzzle into the room',
         precondition='score act.look > 0.2 (on hearing "come in"); legibility: muzzle inside the door frame at sill height, no more than 20 deg above horizontal (measured on the rendered frame), pointing into the room, not at the bulb', preserved='neck anchor (the neck runs from inside the chest)', motif='the head that came low to trust now reaches level into the house; nothing drawn'),
    dict(id='P1 ENTER voice', kind='enter', input='person.head (mouth anchor)', output='voice.arcs (found telephone sound arcs, re-timed)',
         precondition='score voice = call (wide arcs travelling to the dog) or soft (small arcs that stay at the mouth)'),
    dict(id='P2 SPLIT coat (sit)', kind='split', input='person.body (the coat)', output='person.torso + person.thigh + person.shin',
         precondition='score person.sit > 0.2 (quantised to thirds)'),
    dict(id='D1 REPLACE door.leaf by the found swing', kind='replace', input='door.leaf', output='door.leaf at a found angle (Straight Talk closing, played backward)',
         precondition='score door = open (6.2 s)', preserved='hinge on the left jamb'),
    dict(id='D2 ENTER room light', kind='enter', input='doorway', output='room = a lit bulb (Light Of Your Life B); light field on the porch',
         precondition='door open; light rises 6.2-6.9 s'),
]
fired = []
for c in gt:
    if c['rules'] or c['split_at_threshold']:
        fired.append(dict(t=c['t'], i=c['i'], state=c['state'], rules=c['rules'] + (['R8 SPLIT torso at the threshold'] if c['split_at_threshold'] else []),
                          materials=c['materials']))
json.dump(dict(about='SCION 43 rewrite rulebook. Time base: score frames, 24 fps; the dog graph is solved on twos. Coordinates: metres along the porch (x), height (v); screen X = 278 + 195 x.',
               rules=RULES, fired_in_this_render=fired), open(os.path.join(TOP, 'rulebook.json'), 'w'), indent=1)
print(len(RULES), 'rules;', len(fired), 'graph changes with rules')
