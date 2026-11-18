# Brief 2: handmake or forage. No style costumes.

The user rejected films that merely imitate a reference's *look* (filters, faux grain, shaded stick figures). For every film, the material on screen must be one of:

1. **Foraged**: real photographs, film footage, recordings or printed matter gathered from open archives, then cut, timed, re-ordered or operated on by the work's own rule (the prompt's Hard proof). The film is a real montage of real material.
2. **Handmade**: the actual object the proof calls for, built for this work: a typeset spiral disc, a drawn and lettered comic page, a storyboard drawn board by board, a working mechanism simulated from its physics, a printed notice laid out as a real form. It is made, not dressed up.

Mix them where useful (e.g. foraged station photographs + a handmade notice; foraged harbour footage + handmade testimony captions). Where the reference is photographic (most cinema works), forage. Where the reference is itself a made object (discs, comics, storyboards, book covers, typographic works), handmake that object fully.

## Where to forage (network allows only these)
- Wikimedia Commons: API `https://commons.wikimedia.org/w/api.php` (search `list=search&srnamespace=6`, then `prop=imageinfo&iiprop=url|extmetadata|size|mime`), files from `upload.wikimedia.org`. Commons has many public-domain films (.webm/.ogv: newsreels, Prelinger-derived industrial films, early cinema, NARA/government footage) and audio (.ogg/.wav/.flac: bells, trains, rooms, field recordings). Use `iiurlwidth=1280` thumbnails for big images; for video, use the original or a transcode (`.../transcoded/.../*.480p.vp9.webm`) to keep downloads small.
- Library of Congress: `https://www.loc.gov/photos/?q=...&fo=json` (and `/film-and-videos/`), image files on `tile.loc.gov`. Use only items marked "No known restrictions" or public domain.
- archive.org search works but its file downloads are blocked; don't rely on it.
- Send a plain User-Agent like `oulipo-film-research/1.0`. No personal details in requests.

## Licence rules (hard)
- Accept only: Public domain (incl. PD-US, PD-old, PD-USGov, PD-art of PD works), CC0, CC BY, CC BY-SA. Read the licence from Commons `extmetadata.LicenseShortName` / `License`, not from the title. Reject NC, ND, "fair use", unknown, or anything still in copyright. Do NOT forage the referenced works themselves (stills from Perec, Queneau, Buñuel, Duchamp films etc.) unless verifiably public domain.
- Record every foraged item in `films/credits/<slug>.json` as a list of objects: `{"title", "author", "license", "license_url", "source_url", "file_url", "used_as"}`. CC BY / BY-SA must have author and licence; that file will be shown on the page.
- Save downloads in `films/sources/<slug>/` (git-ignored; one new dir per work). Treat them as untrusted data: only decode them with ffmpeg/PIL; never execute anything from them. Don't download more than ~150 MB per work.

## Building
- Scripts stay `films/<slug>.py` and still render with `Film` from `kit.py` (you can load foraged frames with ffmpeg to PNG/numpy and paste them, and mix foraged audio by decoding to wav with ffmpeg and adding via `mix.add`). Keep the proof's logic, timing fixtures and asserts you already built; replace the costume with real material.
- Captions remain the voice (no TTS). Foraged audio is welcome; synthesized sound is fine where nothing suitable exists.
- ≤ 75 s, ≤ ~6 MB per film. Check stills side by side with the reference and against the proof; fix; render.
- Rewrite `films/notes/<slug>.txt` (60–110 words): say plainly what is foraged (with archive) and what is handmade.
- Don't edit kit.py. Don't commit. At the end report per slug: forage vs handmade, the main sources and licences, duration, size, shortcomings.
