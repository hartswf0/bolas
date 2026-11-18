# AFTERIMAGE

An Afterlight study: the eye keeps the glow. The screen is treated as a retina that adapts to light and keeps a
complementary afterimage where light has gone (the Retina technique of AFL-20, *Sun in Your Eyes*). The archive's
light is tinted a cold clinical green-white, so what the eye is made to watch comes back as pink, made by the eye
rather than painted on. It pairs with *A Clockwork Pink* (the clamp) and *Paradiso* (the tin of cut frames).

```bash
python3 tools/afterimage/afterimage.py SHOTS_DIR OUT_DIR                      # ~9 min, writes afterimage.mp4 and retina.json
python3 tools/afterimage/check_afterimage.py OUT_DIR/retina.json OUT_DIR/afterimage.mp4
python3 tools/afterimage/build_page.py OUT_DIR/retina.json                    # fills afterlight/afterimage/index.html
```

`SHOTS_DIR` is `shots/` from [hartswf0/secondhand-motion](https://github.com/hartswf0/secondhand-motion); only
`eye-sam`, `camera-sam`, `light-bulb-sam`, `lighthouse-sam`, `lantern-sam` and `star-sam` are read. Needs numpy, scipy,
Pillow and ffmpeg. The web copy in `media/afterlight/afterimage.mp4` is re-encoded at CRF 30.

All footage is public domain (Internet Archive; titles and links in `SOURCES` in `afterimage.py` and on the page).
Frames are retimed, cropped, tinted and composited, never drawn on. The sound is synthesized; in the third movement its
loudness is the retina's afterimage energy.

Critic rounds are recorded in `critic.json` and shown on the page. No critic has heard the sound.
