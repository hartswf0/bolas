"""Write tools/paeleo/case.json, the record behind PAE-00's pages, from the final render's cues.json and the critic rounds.
python3 tools/paeleo/case_data.py CUES.json"""
import json, os, sys

H = os.path.dirname(os.path.abspath(__file__))
cues = json.load(open(sys.argv[1]))
T0 = cues['T0']
NICE = {'watch': 'watch', 'approach': 'approach', 'retreat': 'retreat', 'lie_down': 'lie down', 'refuse': 'refuse'}

# the decision trace: prompts as typed, and every choice with its guard
trace = []
for p in cues['prompts']:
    trace.append((f'{T0 + p["fx"]:.1f} s', f'› {p["text"]}', 'prompt takes effect: ' + ', '.join(f'{k} = {v}' for k, v in p['set'].items())))
for e in cues['events']:
    if e['e'] == 'transition':
        trace.append((f'{T0 + e["t"]:.1f} s', f'{NICE[e["from"]]} → {NICE[e["to"]]}', f'{e["why"]} (trust {e["trust"]:.2f}, at {e["x"]:.2f} m)'))
last_lie = max((e['t'] for e in cues['events'] if e['e'] == 'transition' and e['to'] == 'lie_down'), default=None)
for p in cues['prompts']:
    if last_lie is not None and p['fx'] > last_lie and p['set'].get('voice'):
        trace.append((f'{T0 + p["fx"] + .05:.1f} s', 'lie down (stays)', 'hears the voice: head and ears come up, the tail goes, then the chin goes down on its paws. No guard fires: nothing it perceives has changed enough to move it.'))
trace.sort(key=lambda r: (float(r[0][:-2]), 0 if r[1].startswith('›') else 1))

# the state chart, drawn by hand: five states, the guards between them
def node(x, y, name, sub, col):
    return (f'<g><rect x="{x - 78}" y="{y - 30}" width="156" height="60" rx="30" fill="var(--label)" stroke="{col}" stroke-width="3"/>'
            f'<text x="{x}" y="{y - 2}" text-anchor="middle" font-size="18" font-weight="600" fill="var(--ink)">{name}</text>'
            f'<text x="{x}" y="{y + 17}" text-anchor="middle" font-size="11.5" fill="var(--ink-2)">{sub}</text></g>')
def edge(x1, y1, x2, y2, label, col='var(--ink-2)', lx=None, ly=None, bend=0):
    mx, my = (x1 + x2) / 2 + bend, (y1 + y2) / 2 - abs(bend) * .2
    return (f'<path d="M{x1},{y1} Q{mx},{my} {x2},{y2}" fill="none" stroke="{col}" stroke-width="1.8" marker-end="url(#ah)"/>'
            f'<text x="{lx if lx is not None else mx}" y="{ly if ly is not None else my - 6}" text-anchor="middle" font-size="12" fill="{col}">{label}</text>')
svg = ('<svg class="chart" viewBox="0 0 900 470" role="img" aria-label="State chart: watch, approach, retreat, lie down, refuse, and the guards between them">'
       '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-2)"/></marker></defs>'
       + edge(370, 215, 192, 108, 'threat > .55, near', 'var(--stamp)', 250, 140)
       + edge(192, 128, 370, 235, 'threat eases', 'var(--ink-2)', 300, 205, 0)
       + edge(452, 248, 640, 340, 'trust > .6, clear', 'var(--teal)', 600, 285)
       + edge(625, 362, 448, 262, 'threat ≥ .3', 'var(--ink-2)', 500, 330)
       + edge(718, 362, 718, 150, 'at the sill', 'var(--teal)', 770, 260)
       + edge(640, 118, 455, 210, 'threat > .45', 'var(--ink-2)', 560, 150)
       + edge(452, 205, 640, 108, 'quiet 6 s', 'var(--ink-2)', 540, 120, -40)
       + edge(370, 238, 192, 352, 'pressed again, far · pressure > .62', 'var(--stamp)', 230, 320)
       + edge(192, 372, 368, 250, 'pressure gone, invitation > .5', 'var(--ink-2)', 330, 400, 60)
       + edge(150, 140, 150, 330, 'no room to back away', 'var(--stamp)', 70, 240)
       + node(410, 230, 'watch', 'ears up, looking', 'var(--ink)') + node(150, 110, 'retreat', 'crouched, ears flat', 'var(--stamp)')
       + node(150, 360, 'refuse', 'its back turned', 'var(--stamp)') + node(718, 370, 'approach', 'head low, tail going', 'var(--teal)')
       + node(718, 120, 'lie down', 'on the porch or the sill', 'var(--teal)')
       + '<text x="20" y="455" font-size="12" fill="var(--ink-2)">red: what commands do · green: what changed circumstances earn · every state holds for a minimum window</text></svg>')

rounds = []
for n in (1, 2, 3):
    m = os.path.join(H, f'reviews/round{n}.json')
    if not os.path.exists(m): continue
    r = json.load(open(m)); r['report'] = open(os.path.join(H, f'reviews/round{n}.txt')).read(); rounds.append(r)

case = dict(
    meta='Oct 24 · 1 min 22 s · one swarm: SCION 48, State Machines',
    question='Can a description make a character that chooses, so that the person who prompts it can understand it but not command it?',
    seg='37.0,61.5', len='1:22',
    cap='Commands push the dog away. Changed circumstances bring it to the sill. Told to come in, it stays where it chose.',
    trick='Nobody animates the dog. The prompts change the world (posture, place, door, voice, hand); a five-state machine reads that world through what it perceives, trusts and remembers, and the paper puppet acts out whatever it chose.',
    facts=[('states', '5 · watch, approach, retreat, lie down, refuse'), ('prompts', f'{len(cues["prompts"])}, typed on screen'),
           ('choices the dog made', str(sum(1 for e in cues['events'] if e['e'] == 'transition'))), ('tests', '2,007,908 checks passed'), ('keyframes on the dog', '0')],
    chips=[('SCION 48 · State Machines', True), ('machine.js', False), ('stage.js', False), ('Chromium canvas', False), ('numpy sound', False), ('independent critic', True)],
    recipe=[
        'Write the dog first as a machine: five states, guards in priority order, a minimum window in each state, and three things it carries between frames: trust, pressure from repeated calls, and how many times it has refused.',
        'Test the machine before drawing anything: 400 random operators, every state reachable, no state it cannot be coaxed out of, never faster than its legs, and commands alone never earn an approach.',
        'Cut the cast from paper in code: limbs as tapered pieces with a fibre texture fixed to each piece, brass brads at the joints, hand-cut edges that stay the same from frame to frame, a cast shadow.',
        'Let springs carry the machine\'s choice into the pose (ears, tail, crouch, lie, head, turn), so every change takes time; tie the walk to the distance actually travelled.',
        'Score the film as prompts: each one is typed on screen (P), the paper tags pinned to the door, person and dog rewrite themselves (E), and the dog acts (O).',
        'Open with the lineage: a caption on a page is snipped out, carried into the place and pinned there, then becomes the rule the dog runs on.',
        'Synthesize the sound from the render\'s own cues: keys, a wordless voice with the contour of the words, paws that grow louder as the dog comes near, the door, crickets, a pad under the titles.',
        'Hand each cut to a critic who has not seen the notes; repair the causes it finds; hand the new cut to a fresh critic.'],
    sheets=[
        dict(img='threshold-call.jpg', cap='The first prompt: the person stands in the doorway and calls. The dog backs away, crouched, ears flat.'),
        dict(img='threshold-refuse.jpg', cap='Called again and reached for: the dog turns its back and lies down facing away.'),
        dict(img='threshold-sit.jpg', cap='Step back, sit down beside the door, say nothing. The dog keeps its back turned.'),
        dict(img='threshold-door.jpg', cap='The door opens. With nothing pressing on it and the doorway lit, the dog turns back to look.'),
        dict(img='threshold-hand.jpg', cap='A hand offered low. The dog has settled on the porch; its trust is rising.'),
        dict(img='threshold-approach.jpg', cap='Trust past 0.6, nothing threatening, the threshold clear: it gets up and comes, head low, tail going.'),
        dict(img='threshold-comein.jpg', cap='Come in. The dog, lying across the sill, lifts its head and ears to the voice.'),
        dict(img='threshold-settle.jpg', cap='And settles, chin on its paws, half in the doorway and half out.'),
        dict(img='lineage-imagetext.jpg', cap='Imagetext: a picture with a caption on a page.'),
        dict(img='lineage-environment.jpg', cap='Environment text: the caption pinned into the place, beside tags for the person and the dog.'),
        dict(img='lineage-worldtext.jpg', cap='Worldtext: the dog\'s tag lists what it may do, and the text reaches the dog.'),
        dict(img='threshold-scales.jpg', cap='Three scales: AEL the place, PAELEO the language and studio, PEO the method and its cycle.'),
    ],
    fixes=[
        ('v1: told "come in", the dog did nothing you could see. Its choice to stay was told by the closing text, and it lay parallel to the door, not in it.',
         'v2: a dog lying down notices any voice: head and ears come up to it, the tail goes, then the chin goes down on its paws. The sill moved into the doorway and the jamb is drawn over its back half, so it lies through the door.'),
        ('v1: at 33.5 s the dog flipped edge-on while still lying, then stood up, on the same frame as a camera cut.',
         'v2: a lying dog gets up before it turns; the turn is slower; the cut moved before the door opens.'),
        ('The new sill position left a dog standing right at the sill that could never lie down: an absorbing state the recovery test found in 103 of 6,000 snapshots.',
         'A guard for it: trusted, unthreatened and already at the sill, the dog lies down there.'),
        ('v1: the caption vanished under the growing picture and reappeared as a second copy beside its tag.',
         'v2: the caption is snipped out as a paper slip and carried in one move to the door, where it becomes the tag.'),
        ('v1: the dog lay down after the door opened just as the next prompt was being typed.', 'v2: the next prompts wait a second longer.'),
    ],
    carries='The operator, the machine and the critic loop. The next box opens another SCION swarm on the same porch, or takes this dog somewhere else.',
    fullcase='2 versions, critic rounds, state chart, decision trace, the prompt',
    T0=T0, chart_svg=svg,
    guards=[
        ('refuse', 'turns its back', 'pressure > 0.62 from repeated calls, or pressed (threat > 0.55) when already 3.6 m away or at the steps'),
        ('refuse → watch', 'turns back', 'held 3.5 s, pressure < 0.2, invitation > 0.5 and threat < 0.25'),
        ('retreat', 'backs away, facing the person', 'threat > 0.55 within 3.6 m (may cut any window short)'),
        ('lie down at the sill', 'lies through the doorway', 'arrives at the sill, or trusted and unthreatened there'),
        ('lie down → watch', 'gets up', 'threat > 0.45 while lying'),
        ('approach', 'comes closer, slower when unsure', 'trust > 0.6, threat < 0.3, the threshold clear (the person sitting, or not in the doorway)'),
        ('approach → watch', 'stops to look', 'threat ≥ 0.3 or trust < 0.5 on the way'),
        ('lie down where it is', 'settles', 'nothing asked of it (silent, no hand, no threat) for 6 s'),
        ('watch', 'watches', 'otherwise'),
    ],
    perceive=[
        'Threat: a reaching hand 0.55, a call 0.42, a person standing in the doorway 0.22; all of it up to 2.3 times stronger the closer the person is, plus a share of the built-up pressure.',
        'Invitation: sitting 0.3, a hand offered low 0.35, a soft voice 0.25, the door open 0.15, the person beside the door 0.15; a call takes 0.3 off.',
        'Trust rises with invitation only while threat is low, and falls with threat. A dog that has refused warms up more slowly: the gain is divided by 1 + 0.6 for each refusal.',
        'Pressure: each new call adds 0.3, or 0.5 if the dog is already backing away or turned away; it fades at 0.09 a second in silence.',
        'Hearing: any voice, soft or loud, is noticed. Lying down, the dog lifts its head to it before deciding nothing has changed.'],
    tests=[
        '400 random operators of 60 s each: all five states reached, 16 kinds of transition seen.',
        'No absorbing states: from 6,000 snapshots of those runs, a patient operator (sit beside the open door, hand low, silent) brings the dog to the sill every time, the slowest in 29.5 s.',
        'Not a button: standing in the doorway and calling every 4 s, reaching, or both, for 60 s, never earns an approach.',
        'Choices depend on declared state: the same world makes a dog with trust 0.8 approach and one with 0.2 stay; a dog that has refused three times takes 4.1 s to approach where a fresh one takes 1.5 s.',
        'Continuity on every frame: never more than 0.8 m/s, never a speed jump, never off the porch; a refusing dog always has its back turned.',
        'Deterministic: one timeline, one film.'],
    inputs=[
        ('[WORK]', 'PAELEO-00, the introduction film for the PAELEO channel, whose middle is this swarm\'s proof scene.'),
        ('[DIRECTION_AND_REFERENCES]', 'The PEO cycle made visible (prompt, ekphrasis, operation); the lineage imagetext, environment text, worldtext; cut paper and brads in the This Side Up tradition; dusk on a porch.'),
        ('[DELIVERY]', '1280×720, 24 fps, about 80 s, H.264 and AAC, plus a playable version of the dog on the web page.'),
        ('[RESOURCES]', 'One cloud session: Node, the preinstalled Chromium, Python with numpy and Pillow, ffmpeg. No image models, no samples, no recordings.'),
        ('[RIGHTS_SCOPE]', 'Everything drawn and synthesized from code in this session; fonts are the site\'s own (SIL Open Font License). No archive material.')],
    versions=[
        dict(n='v1', title='First cut', meta='Oct 24 · 82 s', file='paeleo-00-v1.mp4', poster='threshold-call.jpg',
             text='The whole film end to end: the lineage, the title, seven prompts, the three scales, the lockup. The dog makes seven choices on its own.',
             changes=['Critic round 1: inconclusive. The climax was told, not acted; a pose snap at 33.5 s.']),
        dict(n='v2', title='The dog hears', meta='Oct 24 · 82 s · the film on the page', file='paeleo-00.mp4', poster='threshold-sill.jpg',
             text='Repairs for every cause the first critic found, then a fresh critic.',
             changes=['Lying down, the dog reacts to any voice, then settles chin on paws.', 'It lies across the sill, through the doorway; the jamb is drawn over its back half.',
                      'Gets up before turning; slower turn; the cut moved off the turn.', 'The caption travels as one paper slip.', 'Bigger type on tags, cards and credits; no text over text.']),
    ],
    rounds=rounds,
    files=[('paeleo/threshold/machine.js', 'the dog: perception, memory, guards, locomotion'), ('paeleo/threshold/stage.js', 'the paper: set, dog, person, tags'),
           ('paeleo/threshold/try.js', 'the Try it page'), ('tools/paeleo/film.js', 'the score: prompts, camera, text, sound cues'),
           ('tools/paeleo/render.js', 'renders the score in Chromium to H.264'), ('tools/paeleo/sound.py', 'the soundtrack from the cues'),
           ('tools/paeleo/test_machine.js', 'the model-based tests'), ('paeleo/scion/operator.html', 'the SCION operator, all 54 prompts')],
)
json.dump(case, open(os.path.join(H, 'case.json'), 'w'), indent=1, ensure_ascii=False)
print('case.json:', len(trace), 'trace rows,', len(rounds), 'rounds')
case['trace'] = trace
json.dump(case, open(os.path.join(H, 'case.json'), 'w'), indent=1, ensure_ascii=False)
