/* SCION 18 · Cartoon Saloon — the MODEL SHEET (turnaround + expression sheet), authored by hand for this film.
   Every coordinate below was written for this scene (no tracing of any source image). Units: centimetres, y up,
   origin on the floor under the body centre (bodies) or at the neck pivot (heads). Bodies are authored facing LEFT
   (toward the door); the three-quarter-rear view facing right (Q2) is the mirror of Q1 (the dog is drawn symmetric).
   A drawing is {outline:[[x,y]...], strokes:[[[x,y]...]...]} — outlines are closed Catmull-Rom curves through the points.
   Typed boundary: the rig (rig.js part of saloon.js) may only (a) in-between two drawings of the SAME part by arclength
   resampling, (b) place/rotate a drawing at a pivot, (c) solve leg/arm bones and the tail chain. It may never scale a
   drawing non-uniformly or mirror a profile (no edge-on collapse). */
const SHEET = {
  version: 'sheet-v3',
  dog: {
    // ---- bodies (torso + bib + interior strokes), keyed by view
    L_stand: {
      outline: [[-18, 55], [2, 51], [20, 52], [30, 47], [34, 38], [31, 27], [22, 22], [8, 27], [-6, 25], [-20, 19], [-32, 26], [-36, 38], [-31, 49]],
      bib: [[-31, 47], [-36, 37], [-33, 26], [-25, 20], [-24, 30], [-27, 42]],
      strokes: [[[18, 45], [24, 36], [22, 26]], [[-20, 46], [-24, 36], [-20, 28]]],
      shoulder: [-23, 39], hip: [22, 37], neck: [-28, 47], tail: [31, 46],
    },
    L_crouch: {
      outline: [[-17, 44], [2, 45], [18, 43], [27, 38], [30, 29], [27, 19], [19, 14], [7, 19], [-6, 17], [-19, 12], [-31, 18], [-35, 30], [-30, 40]],
      bib: [[-30, 38], [-35, 29], [-32, 18], [-24, 13], [-23, 22], [-26, 33]],
      strokes: [[[15, 37], [21, 28], [19, 18]], [[-19, 37], [-23, 28], [-19, 20]]],
      shoulder: [-22, 30], hip: [19, 28], neck: [-27, 38], tail: [27, 37],
    },
    L_lie: {
      outline: [[-18, 30], [2, 27], [20, 28], [31, 25], [37, 16], [36, 6], [26, 1], [10, 2], [-6, 2], [-22, 2], [-34, 6], [-38, 17], [-32, 27]],
      bib: [[-32, 26], [-38, 16], [-34, 6], [-26, 3], [-25, 12], [-28, 21]],
      strokes: [[[16, 24], [28, 18], [26, 6], [14, 4]], [[-22, 22], [-26, 13], [-24, 6]]],
      shoulder: [-26, 14], hip: [22, 13], neck: [-30, 24], tail: [34, 21],
    },
    Q1_stand: { // three-quarter rear, facing left-away: rump toward the viewer on the right, head small and far on the left
      outline: [[-6, 56], [6, 54], [15, 50], [21, 42], [22, 33], [18, 25], [11, 22], [4, 24], [-4, 25], [-13, 26], [-20, 31], [-23, 41], [-20, 50], [-13, 55]],
      bib: null,
      strokes: [[[-14, 53], [-2, 55], [10, 51], [17, 44]], [[8, 40], [6, 31], [5, 24]], [[19, 36], [16, 28]]],
      neck: [-18, 49], tail: [13, 51],
    },
    RV_stand: { // straight from behind: a broad round rump, legs short under it, head peeking over the shoulders
      outline: [[0, 54], [10, 52], [17, 46], [20, 36], [18, 25], [11, 18], [4, 20], [0, 19], [-4, 20], [-11, 18], [-18, 25], [-20, 36], [-17, 46], [-10, 52]],
      bib: null,
      strokes: [[[0, 52], [0, 44], [1, 37]], [[-15, 33], [-11, 23]], [[15, 33], [11, 23]]],
      neck: [0, 50], tail: [0, 47],
    },
    Q1_lie: { // lying curled, back to the viewer (authored facing left-away; shown mirrored as Q2: back to the door)
      outline: [[-4, 31], [8, 30], [18, 25], [25, 16], [26, 6], [20, 1], [6, 0], [-10, 0], [-22, 1], [-28, 6], [-27, 15], [-20, 24], [-12, 29]],
      bib: null,
      strokes: [[[-18, 25], [-4, 31], [12, 28], [21, 19]], [[18, 17], [11, 10], [5, 3]]],
      neck: [-20, 22], tail: [20, 14],
    },
    // ---- legs per view: root (shoulder/hip), foot (floor contact), bend +1 elbow-back / -1 knee-forward, near (drawn lighter)
    legs: {
      // order: LF (left fore), RF, LH, RH. In L and Q1 the dog's LEFT side faces the viewer; in Q2 (mirror) its right side.
      L: [{ root: 'shoulder', dx: 0, foot: [-22, 0], near: 1 }, { root: 'shoulder', dx: 3, foot: [-18, 1.5], near: 0 },
          { root: 'hip', dx: 0, foot: [23, 0], near: 1 }, { root: 'hip', dx: -3, foot: [19, 1.5], near: 0 }],
      L_lie_feet: [[-50, 0.5], [-46, 2], [4, 0.5], [8, 2]],
      Q1: [{ root: [-19, 38], foot: [-20, 0], near: 1 }, { root: [-12, 39], foot: [-12, 1.8], near: 0 },
           { root: [6, 34], foot: [6, 0], near: 1 }, { root: [15, 35], foot: [15, 1.8], near: 0 }],
      RV: [{ root: [-6, 30], foot: [-7, 2.5], near: 0 }, { root: [6, 30], foot: [7, 2.5], near: 0 },
           { root: [-11, 26], foot: [-11, 0], near: 1 }, { root: [11, 26], foot: [11, 0], near: 1 }],
      Q1_lie: [{ root: [-18, 12], foot: [-20, 2], near: 1 }, { root: [-12, 12], foot: [-12, 2], near: 0 },
               { root: [6, 12], foot: [4, 2], near: 1 }, { root: [15, 12], foot: [13, 2], near: 0 }],
      len: { fore: [19, 19], hind: [21, 20] },
      width: { fore: [11.5, 7.5, 6.2], hind: [14.5, 8, 6.2] },
    },
    // ---- heads: the expression / turn sheet. Pivot = top of the neck. nose = muzzle tip (used to MEASURE facing).
    heads: {
      prof: { // profile facing left
        skull: [[-3, 13], [-10, 11.5], [-15, 7.5], [-21, 6], [-26, 5], [-29.5, 3], [-29.5, -0.5], [-26, -3], [-20, -4.5], [-12, -5.5], [-4, -5], [3, -1], [5, 5], [2, 11]],
        cream: [[-15, 1.5], [-21, 2.2], [-27, 1], [-28, -1.5], [-25, -3], [-19, -4.2], [-13, -4.2], [-11, -1.5]],
        nose: [-28.2, 2.3, 2.5, 1.9], eyes: [[-13.5, 5.4, 1]], brow: [[-16.5, 8.4], [-11, 8.8]],
        mouth: [[-24, -2.1], [-19, -2.9], [-14.5, -2.2]],
        earNear: { attach: [0, 10], prick: [[-3, 10.5], [-1, 19], [3, 24], [6, 20], [5, 12], [2, 8.5]], flat: [[-1, 10], [7, 13.5], [14, 13], [12, 9.5], [6, 7.5], [1, 7.5]] },
        earFar: { prick: [[-6, 11], [-5, 18], [-2, 21], [0, 16], [-1, 11]], flat: [[-4, 11], [2, 14], [8, 13.5], [4, 10], [-1, 9.5]] },
        center: [-10, 3], tip: [-29.5, 1.5],
      },
      back34: { // back of the head toward the viewer, muzzle receding left into depth
        skull: [[-2, 14], [-9, 12], [-13, 8], [-16.5, 7], [-20, 7.2], [-22, 5.2], [-20.5, 2.6], [-15, 1], [-10, -3], [-3, -5], [4, -3], [7, 3], [6, 10]],
        cream: null, nose: [-21.4, 5.6, 1.3, 1.1], eyes: [], brow: null, mouth: null,
        earNear: { attach: [4, 10], prick: [[1, 11], [3, 19], [7, 23], [9, 17], [8, 10], [4, 8]], flat: [[2, 10], [8, 14], [14, 13], [11, 9], [6, 7.5], [3, 8]] },
        earFar: { prick: [[-7, 11], [-10, 17], [-7, 20], [-3, 14]], flat: [[-6, 11], [-12, 13], [-10, 9.5], [-5, 9]] },
        strokes: [[[0, 12], [3, 5], [2, -2]], [[-12, 7], [-16, 4.5]]],
        center: [-4, 4], tip: [-22, 5.2],
      },
      in34: { // looking in, through the door: the back of the head to the viewer, the muzzle pointing away into the room
        skull: [[0, 14], [-7, 12.5], [-11, 8], [-13.5, 5.5], [-16, 5], [-16.5, 2.8], [-13, 1.2], [-9, -3], [-4, -5], [2, -4.5], [7, -1], [9, 5], [6, 11]],
        cream: null, nose: [-16, 4, 1.1, 1.0], eyes: [], brow: null, mouth: null,
        earNear: { attach: [5, 11], prick: [[3, 11], [7, 19], [11, 22], [11.5, 14], [8, 9]], flat: [[3, 11], [10, 14], [14, 12], [10, 8.5]] },
        earFar: { prick: [[-6, 12], [-10, 19], [-12.5, 15], [-10, 10]], flat: [[-6, 12], [-12, 14], [-13, 10], [-9, 9.5]] },
        strokes: [[[1, 12], [3, 4], [1, -3]], [[-9, 6], [-12, 3.5]]],
        center: [-1, 4], tip: [-16.5, 3.5],
      },
      rear: { // straight from behind
        skull: [[0, 14], [-7, 12], [-10, 6], [-9, 0], [-5, -4], [0, -5], [5, -4], [9, 0], [10, 6], [7, 12]],
        cream: null, nose: null, eyes: [], brow: null, mouth: null,
        earNear: { attach: [6, 11], prick: [[5, 11], [10, 19], [12, 15], [10, 9]], flat: [[5, 11], [12, 13], [13, 9], [9, 8]] },
        earFar: { prick: [[-5, 11], [-10, 19], [-12, 15], [-10, 9]], flat: [[-5, 11], [-12, 13], [-13, 9], [-9, 8]] },
        strokes: [[[0, 12], [0, 4]]],
        center: [0, 4], tip: [0, 4],
      },
      front34: { // three-quarter front, face toward the viewer, looking left
        skull: [[1, 14], [-6, 13], [-12, 9], [-15, 4], [-18, 1], [-21, -1], [-21.5, -4], [-18, -6.5], [-12, -8], [-6, -7], [0, -4], [4, 2], [4, 9]],
        cream: [[-10, -1], [-16, 0], [-20.5, -2.5], [-19, -6], [-13, -7.5], [-8, -5.5]],
        nose: [-20, -1.6, 2.6, 2], eyes: [[-7.5, 4.2, 1.05], [-15, 5.4, 0.8]], brow: [[-10, 7.6], [-5, 8.2]],
        mouth: [[-19, -5], [-15, -6.2], [-11, -5.6]],
        earNear: { attach: [2, 10], prick: [[1, 11], [5, 18], [10, 21], [10, 14], [6, 8]], flat: [[1, 10], [8, 14], [13, 13], [10, 8.5], [5, 7.5]] },
        earFar: { prick: [[-9, 11], [-13, 18], [-15, 13], [-12, 9]], flat: [[-9, 11], [-15, 13], [-15, 9], [-11, 9]] },
        center: [-6, 3], tip: [-21.5, -2.5],
      },
    },
    tail: { segs: 6, len: 5.4, width: [5.5, 7.5, 8, 7, 5, 2.5, 0.8] },
  },
  person: {
    stand: {
      dress: [[-10, 102], [10, 102], [13, 80], [18, 40], [24, 5], [10, 3], [-6, 3], [-22, 5], [-17, 45], [-13, 80]],
      bodice: [[-9, 101], [9, 101], [10, 120], [8, 135], [0, 140], [-8, 136], [-11, 120]],
      shawl: [[-13, 140], [-2, 145], [9, 140], [13, 128], [10, 116], [-3, 121], [-15, 125]],
      neck: [1, 142], shoulderN: [5, 135], shoulderF: [-4, 136], shoe: [16, 2.5], hipDrop: 0,
      hand: [12, 92], handF: [-12, 95],
    },
    sit: {
      dress: [[-8, 64], [8, 64], [14, 58], [34, 52], [43, 46], [45, 24], [47, 4], [30, 3], [10, 3], [-14, 4], [-17, 30], [-14, 50]],
      bodice: [[-7, 63], [9, 63], [12, 82], [12, 96], [5, 101], [-4, 98], [-8, 82]],
      shawl: [[-8, 101], [3, 106], [13, 101], [16, 89], [13, 78], [0, 83], [-10, 87]],
      neck: [6, 103], shoulderN: [10, 96], shoulderF: [1, 97], shoe: [50, 2.5], hipDrop: 38,
      hand: [50, 47], handF: [40, 60],
    },
    head: {
      face: [[-8, 6], [-6, 15], [1, 19], [8, 16], [10.5, 10], [12.5, 6.5], [10.5, 4.8], [11, 2.5], [9.5, 0.5], [10, -1.5], [6, -3.5], [0, -3], [-6, 0]],
      hair: [[-10, 4], [-9, 15], [-3, 21], [6, 20], [10, 15], [5, 16.5], [-1, 13], [-3, 6]],
      bun: [-11.5, 13, 5.2], eye: [6.5, 8.5], mouth: [9.2, 1.6], brow: [[4.5, 11.2], [8.5, 11.4]],
    },
    arm: { len: [29, 27], width: [8, 6, 5] },
  },
};
if (typeof module !== 'undefined') module.exports = SHEET;
