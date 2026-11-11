// Camera-space entrances and conservative walking colliders for the existing rooms.
// Flight deliberately passes through objects. This is not a general physics engine.
export function roomProfile(id, city) {
  const profile = {id, spawn: [0, -5.1, 15], target: [0, -1.6, -8], floorY: -6.8, eyeHeight: 1.7,
    bounds: {min: [-20, -5.1, -30], max: [20, 22, 25]}, obstacles: [], walkable: true};
  const obstacle = (x0, z0, x1, z1, height = 10) => ({min: [x0, -6.8, z0], max: [x1, height, z1]});
  if (id === 'orbit') {
    // The deck is only an annular sector (r 9..26, centered at x=0,z=6).
    // A flat walking rectangle would let visitors step over its central hole.
    // Start above the deck and use bounded flight until surface support exists.
    profile.walkable = false;
    profile.spawn = [0, -5.1, 22]; profile.target = [0, 4, -28];
    profile.bounds = {min: [-60, -18, -85], max: [60, 45, 55]};
  } else if (id === 'constellation') {
    profile.spawn = [0, -5.1, 18]; profile.target = [0, -1.5, -12];
    profile.bounds = {min: [-27, -5.1, -27], max: [27, 24, 27]};
  } else if (id === 'depot' || id === 'wet') {
    profile.bounds = {min: [-5.5, -5.1, -22.2], max: [5.5, 4.8, 13]}; profile.spawn[2] = 11;
  } else if (id === 'library' || id === 'datacenter') {
    profile.bounds = {min: [-7.6, -5.1, -20], max: [7.6, 5, 13]}; profile.spawn[2] = 11;
    if (id === 'library') profile.obstacles.push(obstacle(-3.6, -10.4, 3.6, -7.6, -4.6));
  } else if (id === 'store') {
    profile.bounds = {min: [-9.4, -5.1, -15.2], max: [9.4, 5.5, 14]}; profile.spawn[2] = 12;
    profile.obstacles = [obstacle(-8.6, 3.3, -2.4, 4.7), obstacle(2.5, .3, 8.7, 1.7),
      obstacle(-8.3, -6, -2.1, -4), obstacle(2.3, -9.8, 8.5, -8.2), obstacle(-3.2, -14.8, 3.2, -13.2)];
  } else if (city) {
    // Place the camera in the world's coordinates, including the director's last run offset.
    const points = city.FL.map(f => ({f, p: city.wp(f)}));
    const floor = city.run.position.y - 6.8;
    profile.floorY = floor; profile.spawn = [0, floor + 1.7, 16]; profile.target = [0, floor + 4, -5];
    const xs = points.map(({p}) => p.x), zs = points.map(({p}) => p.z), ys = points.map(({p}) => p.y);
    profile.bounds = {min: [Math.min(-38, ...xs) - 5, floor + 1.7, Math.min(-35, ...zs) - 12],
      max: [Math.max(38, ...xs) + 5, Math.max(25, ...ys) + 12, Math.max(24, ...zs) + 6]};
    profile.walkable = !['wheel', 'helix', 'shell', 'amph', 'table'].includes(city.arch) && city.C.setting !== 'orbit';
    if (profile.walkable) {
      const towers = new Map();
      for (const {f, p} of points) {
        let box = towers.get(f.t);
        if (!box) { box = obstacle(p.x - 1.3, p.z - 1.3, p.x + 1.3, p.z + 1.3, p.y + .6); towers.set(f.t, box); }
        else { box.min[0] = Math.min(box.min[0], p.x - 1.3); box.min[2] = Math.min(box.min[2], p.z - 1.3);
          box.max[0] = Math.max(box.max[0], p.x + 1.3); box.max[2] = Math.max(box.max[2], p.z + 1.3); box.max[1] = Math.max(box.max[1], p.y + .6); }
      }
      profile.obstacles = [...towers.values()];
    } else { profile.bounds.min[1] = -30; profile.spawn = [0, 3, 26]; profile.target = [0, 0, 0]; }
  } else if (!['paper', 'bay', 'set', 'silhouette', 'card', 'cave'].includes(id)) {
    profile.walkable = false; profile.spawn = [0, 1, 18]; profile.target = [0, 0, 0];
    profile.bounds = {min: [-35, -12, -45], max: [35, 30, 35]};
  }
  return profile;
}
