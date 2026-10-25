"""Fig. 1, the dog: contours traced by hand over archive scan frames (scan pixel coordinates, 384x288).
Each part: poly (traced contour, documented outline of the scan), pivot (joint, inferred), parent.
The tone inside each part is sampled from the scan itself (documented); re-posing parts is invented motion."""
RIGS = {
 'L': {  # Amateur Film New Jersey C, frame f006: dog in profile, facing left
  'frame': 6, 'view': (80, 60, 280, 220),
  'parts': {
   'tail':  {'pivot': (214, 126), 'parent': 'torso', 'poly': [(212,122),(230,128),(248,136),(262,142),(266,150),(258,152),(244,148),(228,142),(214,136)]},
   'hind_far': {'pivot': (196, 150), 'knee': (197, 175), 'foot': (195, 197), 'parent': 'torso', 'poly': [(188,146),(204,146),(204,170),(200,196),(193,198),(190,194),(194,170)]},
   'fore_far': {'pivot': (137, 150), 'knee': (137, 172), 'foot': (136, 190), 'parent': 'torso', 'poly': [(130,146),(144,146),(142,172),(140,190),(134,192),(132,186),(134,170)]},
   'torso': {'pivot': (170, 130), 'parent': None, 'poly': [(126,106),(146,108),(165,116),(190,121),(212,120),(222,128),(222,146),(216,156),(200,152),(175,150),(150,150),(130,148),(118,140),(116,120)]},
   'hind_near': {'pivot': (210, 146), 'knee': (211, 176), 'foot': (209, 200), 'parent': 'torso', 'poly': [(200,140),(220,138),(222,156),(216,176),(214,198),(208,202),(202,200),(206,178),(204,160)]},
   'fore_near': {'pivot': (129, 146), 'knee': (130, 172), 'foot': (128, 199), 'parent': 'torso', 'poly': [(120,140),(138,142),(138,160),(134,180),(132,196),(136,200),(126,201),(122,196),(124,176),(122,160)]},
   'head':  {'pivot': (126, 108), 'parent': 'torso', 'poly': [(87,91),(89,87),(99,84),(104,80),(108,79),(112,67),(116,74),(119,81),(124,88),(132,98),(138,108),(134,118),(122,122),(114,114),(108,103),(102,98),(95,97),(88,95)]},
  }},
}

ORDER = ['fore_far', 'hind_far', 'tail', 'torso', 'head', 'hind_near', 'fore_near']
LEGS = ['fore_far', 'hind_far', 'hind_near', 'fore_near']
GROUND = 200.0   # scan y of the ground under the feet in f006
ANCHOR = (155.0, 200.0)  # body centre over the ground (nose 89 .. rump 222)

FEATURES = {'eye': (101.5, 87.0), 'nostril': (88.6, 90.6), 'mouth': [(89.5, 95.2), (95, 96.0), (100, 95.4)], 'ear': [(110.5, 72), (113, 79), (116, 84)]}
