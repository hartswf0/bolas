"""Who hangs around which film, and what they say to the viewer. One place for all of it.
A cameo is (who, pose, at). Poses are the sprites in media/cameo (cameos.json). Places:
  tl, tr   sitting or peeking on the top edge of a card or player, near the left or right corner
  l, r     standing beside the player, on its bottom edge (film pages, wide screens)
To add a character: render its sprites (scratchpad cast/cameos.py), then give it a SIZE, LINES and a place below.
The poet is a real person, so he appears but never speaks."""

# display height relative to Bola's standing height; sprites share one scale, so this only corrects the ink renderer and photographs
SIZE = dict(bola=1, shim=1, dot=1, critic=1, odysseus=1.75, poet=.98)

LINES = {
 'bola':     ["Hi. I'm Bola. I'm in most of these.", "Every step I take in here was measured.", "That fall was on purpose. There are numbers to prove it."],
 'shim':     ["I'm Shim. I hold the door.", "I'm six per cent taller than Bola. It's in the spec.", "Bola gets the close-ups. I get the heavy end."],
 'dot':      ["I'm Dot! Press play!", "I'm the little one. I fall down the most.", "You can move us in the interactive pages. Try it."],
 'critic':   ["I review these without being told what they mean.", "I see the pictures, not the intentions.", "Weak. No, wait. Meets the bar."],
 'odysseus': ["My name is Nobody.", "The archive answers for me.", "Seven books so far. Still not home."],
}
ON_PLAY = {'bola': "Shh. It's starting.", 'shim': "Here we go.", 'dot': "This is my favourite part.", 'critic': "I'll judge it at 24 frames a second.", 'odysseus': "Watch the hands."}
ON_PAUSE = {'bola': "Paused. We'll wait.", 'shim': "Take your time.", 'dot': "Hey! Keep going!", 'critic': "Pausing is allowed. Skipping is not.", 'odysseus': "Nobody paused it."}
ON_END = {'bola': "Again?", 'shim': "That's the take.", 'dot': "Again! Again!", 'critic': "My notes are in the record below.", 'odysseus': "Next book."}

# who sits on the cards and stands around the player, by program
CARD = {'family': [('bola', 'sit', 'tl'), ('dot', 'peek', 'tr'), ('shim', 'sit', 'tr')], 'cineosis': [('critic', 'sit', 'tr'), ('bola', 'peek', 'tl'), ('shim', 'peek', 'tr')],
        'odyssey': [('odysseus', 'peek', 'tr'), ('odysseus', 'sit', 'tl')], 'wygwyl': []}
PLAYER = {'family': [('bola', 'wave', 'l'), ('dot', 'sit', 'tr'), ('shim', 'shrug', 'r')], 'cineosis': [('critic', 'point', 'r'), ('bola', 'sit', 'tl'), ('shim', 'peek', 'tr')],
          'odyssey': [('odysseus', 'point', 'r'), ('odysseus', 'peek', 'tl')], 'wygwyl': [('poet', 'stand', 'l')]}

# film-specific lines: the first line a character says on that film
FILM = {
 'bolas-videotext': {},
 'the-physical': {'bola': "This is my physical. Every test goes wrong."},
 'crash-lab-film': {'dot': "I miss a stair somewhere in here. Keep watching.", 'bola': "132 tests. I'm in most of them."},
 'cineosis-crash-lab': {'critic': "I judged these from eight stills each.", 'bola': "45 signs. I did them all in the bay."},
 'cineosis-hybrid-pilot': {'critic': "One of these six met the bar.", 'bola': "This is me in real film for the first time."},
 'cineosis-hybrid-atlas': {'critic': "A machine placed her. 38 per cent worked.", 'bola': "Sometimes I'm standing on a desk. That's a bug."},
 'cineosis-handmade-film': {'critic': "I reviewed these blind. All of them.", 'bola': "Every pose here was keyed by hand."},
 'cineosis-hand-butter': {'critic': "This one is about me.", 'bola': "We made a film about making the film."},
 'ep1-nobody': {'odysseus': "I stamp on the prompt in the first ten seconds."},
 'ep2-the-guest-gift': {'odysseus': "He tells it differently. He's wrong."},
 'ep3-the-raft': {'odysseus': "Seventeen days on a raft. You get eight minutes."},
 'ep4-circe': {'odysseus': "Wait for the line. You'll know it when the music stops."},
 'ep5-the-blood': {'odysseus': "Only the blood is in colour. Watch who drinks."},
 'ep6-the-knot': {'odysseus': "They fixed my hands for this one."},
 'ep7-the-loop': {'odysseus': "The beach only colours in when I hold something."},
}

# the intro: who stands in the bay, where (per cent across), and the order they speak in
BAY = [('shim', 'shrug', 16), ('bola', 'wave', 31), ('dot', 'jump', 45), ('critic', 'sit', 84), ('odysseus', 'point', 64)]
BAY_TALK = [('bola', "Hi. We're the test dummies."), ('shim', "Everything we do in here is measured."), ('dot', "I fall down the most!"),
            ('odysseus', "I'm not a dummy. I'm from a different film."), ('critic', "I watch the results without being told what they mean."), ('bola', "Pick a film. Or come and move us around.")]
