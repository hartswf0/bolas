// Shared celestial layer. Room destinations are real objects in the same scene.
// No renderer, clock, input listeners or audio context belong to this module.
export function createStarfield(THREE, scene, narrow = false) {
  const count = narrow ? 900 : 1800, positions = [], colors = [];
  let seed = 73019;
  const random = () => ((seed = (1664525 * seed + 1013904223) >>> 0) / 4294967296);
  for (let i = 0; i < count; i++) {
    const y = random() * 2 - 1, a = random() * Math.PI * 2;
    const r = 130 + random() * 80, h = Math.sqrt(1 - y * y);
    positions.push(Math.cos(a) * h * r, y * r, Math.sin(a) * h * r);
    const warm = random(); colors.push(0.72 + warm * 0.28, 0.8 + warm * 0.16, 1 - warm * 0.24);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({size: .27, vertexColors: true, transparent: true,
    opacity: .75, fog: false, depthWrite: false, sizeAttenuation: true});
  const points = new THREE.Points(geometry, material); points.frustumCulled = false;
  scene.add(points);
  return {
    configure({stars = true, density = .55} = {}) {
      points.visible = stars; geometry.setDrawRange(0, Math.round(count * density));
    },
    update(camera) { points.position.copy(camera.position); },
    dispose() { scene.remove(points); geometry.dispose(); material.dispose(); }
  };
}

export function buildConstellationRoom(THREE, group, filmTexture, destinations) {
  const bronze = new THREE.MeshStandardMaterial({color: 0x827052, metalness: .65, roughness: .42});
  const floor = new THREE.Mesh(new THREE.CircleGeometry(31, 96),
    new THREE.MeshStandardMaterial({color: 0x111c2a, metalness: .4, roughness: .55}));
  floor.rotation.x = -Math.PI / 2; floor.position.y = -6.82; group.add(floor);
  const ringGeometry = new THREE.TorusGeometry(25, .065, 5, 128);
  for (const scale of [.48, .75, 1]) {
    const ring = new THREE.Mesh(ringGeometry, bronze); ring.rotation.x = -Math.PI / 2;
    ring.scale.setScalar(scale); ring.position.y = -6.77; group.add(ring);
  }
  // The archive's moving image becomes the observatory's orbital ribbon.
  const ribbonMaterial = new THREE.MeshBasicMaterial({map: filmTexture, side: THREE.DoubleSide,
    transparent: true, opacity: .5, fog: false});
  for (let i = 0; i < 18; i++) {
    const a = i / 18 * Math.PI * 2;
    const frame = new THREE.Mesh(new THREE.PlaneGeometry(6.6, 3.7), ribbonMaterial);
    frame.position.set(Math.cos(a) * 29, 10 + Math.sin(a * 2) * 2, Math.sin(a) * 29 - 6);
    frame.lookAt(0, 3, -6); group.add(frame);
    const border = new THREE.LineSegments(new THREE.EdgesGeometry(frame.geometry),
      new THREE.LineBasicMaterial({color: 0xc6a76b, transparent: true, opacity: .65}));
    frame.add(border);
  }
  const moon = new THREE.Mesh(new THREE.SphereGeometry(7.5, 32, 24),
    new THREE.MeshBasicMaterial({color: 0xd4d9e0, fog: false}));
  moon.position.set(-26, 18, -68); group.add(moon);
  const eclipse = new THREE.Mesh(new THREE.SphereGeometry(7.2, 32, 24),
    new THREE.MeshBasicMaterial({color: 0x080e1d, fog: false}));
  eclipse.position.set(-23.8, 18.8, -65); group.add(eclipse);
  group.add(new THREE.AmbientLight(0x92b3da, .65));
  const lamp = new THREE.PointLight(0xf4bc77, 160, 70, 1.5);
  lamp.position.set(0, 6, 0); group.add(lamp);
  group.userData.constellationDestinations = destinations;
}

function label(THREE, text) {
  const canvas = document.createElement('canvas'); canvas.width = 512; canvas.height = 96;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = 'rgba(6,12,21,.88)'; ctx.fillRect(0, 0, 512, 96);
  ctx.strokeStyle = '#bda57b'; ctx.strokeRect(1, 1, 510, 94);
  ctx.font = '500 25px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillStyle = '#f5e8ca'; ctx.fillText(text, 256, 48, 480);
  const texture = new THREE.CanvasTexture(canvas); texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map: texture, transparent: true,
    depthWrite: false, fog: false})); sprite.scale.set(5.5, 1.03, 1);
  return sprite;
}

export function createRoomPortals(THREE, scene, destinations) {
  const group = new THREE.Group(), meshes = [], labels = [], geometry = new THREE.IcosahedronGeometry(.48, 1);
  const nodeMaterial = new THREE.MeshBasicMaterial({color: 0xffd592, fog: false});
  const lineMaterial = new THREE.LineBasicMaterial({color: 0xc2b2e6, transparent: true, opacity: .42, fog: false});
  const raycaster = new THREE.Raycaster(), coords = new THREE.Vector2();
  let visible = true;
  function clear() {
    for (const child of [...group.children]) {
      if (child.isSprite) { child.material.map.dispose(); child.material.dispose(); }
      if (child.isLine) child.geometry.dispose();
      group.remove(child);
    }
    meshes.length = 0; labels.length = 0;
  }
  function enter(room, profile) {
    clear();
    const isHub = room === 'constellation', list = isHub ? destinations : [{id: 'constellation', title: 'Constellation map'}];
    const linePoints = [];
    list.forEach((destination, i) => {
      const node = new THREE.Mesh(geometry, nodeMaterial);
      if (isHub) {
        const a = (i / Math.max(1, list.length - 1) - .5) * 2.1;
        node.position.set(Math.sin(a) * 19, -1.8 + Math.sin(i * 1.4) * 1.7, -Math.cos(a) * 19);
      } else {
        node.position.set(profile.spawn[0] + 3.2, profile.spawn[1] + .8, profile.spawn[2] - 5);
      }
      node.userData.destination = destination;
      const caption = label(THREE, destination.title); caption.position.copy(node.position); caption.position.y -= 1.2;
      group.add(node, caption); meshes.push(node); labels.push(caption); linePoints.push(node.position.clone());
    });
    if (linePoints.length > 1) group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(linePoints), lineMaterial));
  }
  scene.add(group);
  return {
    enter,
    configure(on, exploring) { visible = on && exploring; group.visible = visible; },
    hit(camera, x = 0, y = 0, occluders = []) {
      if (!visible) return null;
      coords.set(x, y); raycaster.setFromCamera(coords, camera);
      // A slightly larger hit target keeps these usable on a phone.
      let best = null, bestDistance = Infinity;
      for (const mesh of meshes) {
        const distance = raycaster.ray.distanceToPoint(mesh.position);
        const along = mesh.position.clone().sub(raycaster.ray.origin).dot(raycaster.ray.direction);
        if (along > 0 && along < 65 && distance < .95 && distance < bestDistance) {
          best = mesh.userData.destination; bestDistance = distance;
        }
      }
      if (best && occluders.length) {
        const node = meshes.find(mesh => mesh.userData.destination === best);
        const along = node.position.clone().sub(raycaster.ray.origin).dot(raycaster.ray.direction);
        const obstacle = raycaster.intersectObjects(occluders, false)[0];
        if (obstacle && obstacle.distance < along - .65) return null;
      }
      return best;
    },
    update(time, reducedMotion) {
      if (!visible) return;
      meshes.forEach((mesh, i) => { mesh.rotation.y = reducedMotion ? i * .3 : time * .12 + i * .3; });
    },
    dispose() { clear(); scene.remove(group); geometry.dispose(); nodeMaterial.dispose(); lineMaterial.dispose(); }
  };
}
