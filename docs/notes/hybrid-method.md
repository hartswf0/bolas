# CINEOSIS hybrid pilot — method notes (working)

Pipeline per passage
1. Plate: the sign's own example clip from cineosis-lab, cut-free segment, 24 fps, upscaled to 720 high. Static plates shorter than the action are ping-ponged.
2. Camera: a pinhole fitted to the plate (focal, height, pitch, roll) from table/lamp/row/horizon points; moving plates add a tracked 2D transform per frame (raft: template + ECC; row: phase correlation; desert and corridor: LK floor features → homography chain).
3. Dummies: the crash-lab rig authored in a world laid out to the plate, checked by the lab checker (balance, planted feet, reach, clash, floor), rendered per actor as a transparent orthographic layer from the direction the plate camera sees it, mapped by the pinhole's local affine at the actor's anchor (plus the tracked transform).
4. Shadows: the dummy silhouette projected along the plate's light onto receiving planes (wall, desk, cargo, ground), mapped by the plane's homography, blurred and multiplied; contact occlusion under feet and hands.
5. Occlusion: per-shot mattes — key of the rattan chair on a clean plate, hand polygons (table, lamp, cargo heap) carried by the track, ISNet salient matte on the ranger; depth-gated against the dummy's distance.
6. Look: grade (mono or colour, saturation, white balance, contrast), terminator shading from the silhouette toward the light, resampled through the plate's native resolution (320×240) so it shares the plate's softness, per-frame grain.
7. Interaction with the plate: lifted real glass (cut out, carried, its place inpainted); lamp turned down (plate relit in linear light, globe included); raft motion carried; plate camera moves followed.
8. Sound: the plate's own track (looped plates get ambience), foley placed from the rig's foot contacts and authored events.
