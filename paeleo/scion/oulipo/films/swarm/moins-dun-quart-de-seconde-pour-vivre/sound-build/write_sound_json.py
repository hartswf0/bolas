"""Write films/swarm/<slug>/sound.json from bank.json + cues.json (run after prep.py and cues.py)."""
import json, hashlib, os
SW = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/moins-dun-quart-de-seconde-pour-vivre'
SND = '/home/user/bolas/paeleo/scion/oulipo/films/sources/moins-dun-quart-de-seconde-pour-vivre/sound'
bank = json.load(open(f'{SND}/bank.json')); cj = json.load(open(f'{SND}/cues.json'))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
foraged = [
 dict(id='snd-pen-inkpen', title='Writing with inkpen.ogg (PDSounds no. 179, "writing with inkpen", 2007)', author='stephan (via pdsounds.org; transferred to Commons by Fæ)',
      license='Public domain', license_url='', source_url='https://commons.wikimedia.org/wiki/File:Writing_with_inkpen.ogg',
      file_url='https://upload.wikimedia.org/wikipedia/commons/transcoded/7/7c/Writing_with_inkpen.ogg/Writing_with_inkpen.ogg.mp3',
      file_note='Commons MP3 transcode of the original .ogg (the original was rate-limited when the test shot fetched it); first fetched for the test shot, re-used',
      local_path=f'{SND}/raw/Writing_with_inkpen.ogg.mp3', sha256=sha(f'{SND}/raw/Writing_with_inkpen.ogg.mp3'),
      what_it_shows='20 s stereo recording of an ink pen writing fast on paper on a desk: broadband dry scratch bursts with pen-down transients and some low handling rumble (looked at as spectrogram and waveform: real scratch, no voice, no music)',
      verified_date_or_place='2007-04-22 (DateTimeOriginal); place not stated',
      licence_read_from='Commons extmetadata LicenseShortName = "Public domain", categories PD-author | PDsounds.org; re-read 2026-11-17',
      used_as='pen-on-paper scratch, cut into a 36-grain bank (one grain per written stroke: balloon outlines, tail stubs, every glyph stroke, S1 header/labels, S0 brush strokes low-passed) and 6 pen-down taps (full stops, "?", S1 panel stamps)'),
 dict(id='snd-night-moedling', title='Audio Hörbild Grillenzirpen - nachts um 3 im Föhrenwald Mödling.ogg (2020)', author='DrTrumpet (Wikimedia Commons user), own work',
      license='CC BY-SA 4.0', license_url='https://creativecommons.org/licenses/by-sa/4.0',
      source_url='https://commons.wikimedia.org/wiki/File:Audio_H%C3%B6rbild_Grillenzirpen_-_nachts_um_3_im_F%C3%B6hrenwald_M%C3%B6dling.ogg',
      file_url='https://upload.wikimedia.org/wikipedia/commons/transcoded/7/71/Audio_H%C3%B6rbild_Grillenzirpen_-_nachts_um_3_im_F%C3%B6hrenwald_M%C3%B6dling.ogg/Audio_H%C3%B6rbild_Grillenzirpen_-_nachts_um_3_im_F%C3%B6hrenwald_M%C3%B6dling.ogg.mp3',
      file_note='Commons MP3 transcode (the original .ogg returned HTTP 429 repeatedly from upload.wikimedia.org)',
      local_path=f'{SND}/raw/grillenzirpen_moedling.ogg.mp3', sha256=sha(f'{SND}/raw/grillenzirpen_moedling.ogg.mp3'),
      what_it_shows='40 s field recording of crickets/bush-crickets at 3 a.m. in a pine forest near Mödling: an insect chorus pulsing around 6-9 kHz with three natural 3-5 s near-silent pauses, faint low air; no voices, no music, no footsteps (looked at as spectrogram)',
      verified_date_or_place='2020-08-01 (DateTimeOriginal), Föhrenwald, Mödling (Austria) per title/category',
      licence_read_from='Commons extmetadata LicenseShortName = "CC BY-SA 4.0"; re-read 2026-11-17',
      used_as='distant night ambience bed for the whole film: deep pauses cut, kept spans joined with 1 s crossfades, looped with 1.5 s crossfades, low RMS, fade in over S0, fade out over the last 2 s; A3 is this bed alone'),
]
not_used = [
 dict(id='snd-alt-pencil', title='Pencil scratchings.ogg (PDSounds no. 513)', author='gypsygirl (via pdsounds.org)', license='Public domain', license_url='',
      source_url='https://commons.wikimedia.org/wiki/File:Pencil_scratchings.ogg', file_url='https://upload.wikimedia.org/wikipedia/commons/9/9f/Pencil_scratchings.ogg',
      local_path=f'{SND}/raw/pencil_scratchings.ogg', what_it_shows='82 s mechanical pencil writing on a single page against a wooden desk', verified_date_or_place='2008-05-02',
      used_as='NOT USED (downloaded as an alternate; the ink pen is the truer match for the pen hand and was approved in the test shot). Not to be credited unless used.'),
 dict(id='snd-test-cricket', title='Field cricket unedited.ogg', license='CC BY-SA 3.0', source_url='https://commons.wikimedia.org/wiki/File:Field_cricket_unedited.ogg',
      local_path='/home/user/bolas/paeleo/scion/oulipo/films/sources/moins-dun-quart-de-seconde-pour-vivre/test-shot/Field_cricket_unedited.ogg',
      used_as='NOT USED in the full build (test-shot ambience: one close indoor cricket, 10 s; looped over 66 s its fixed chirp period reads as mechanical). Replaced by the Mödling night chorus. Not to be credited unless used.'),
 dict(id='snd-rejected-soundsnap', title='292934-152 Writing-pen-paper-various marks and lines.wav', license='CC0 (as claimed on Commons)', source_url='https://commons.wikimedia.org/wiki/File:292934-152_Writing-pen-paper-various_marks_and_lines.wav',
      used_as='REJECTED, not downloaded: author given as "soundsnap", a commercial library; the CC0 claim is not credible enough to rely on.'),
]
absences = [
 'Moving Image Archive cache (forage.py index, 253 clips with audio): scanned all speech/sound/music clips by decoded audio (2.5-7 kHz share, speech-band share, 3-7 Hz speech modulation) and looked at spectrograms of the 5 best candidates (Unique Contribution II, Miss Clark Introduces Panorama x2, Legacy for Wings, Back-Room Boy): narration, music, optical hiss; no usable night/cricket/park ambience and no pen-on-paper sound. Nothing taken from the archive.',
 'Commons "dip pen" search: only pronunciation files; no dip-pen recording. Commons "night ambience park": only game music (Minetest) and a pond; none used.',
 'upload.wikimedia.org original-file downloads were rate-limited (HTTP 429) throughout; MP3 transcodes of the same files were used.',
]
handmade = [
 dict(item='grain bank', made_how='prep.py: the pen recording high-passed at 350 Hz (rumble only), 5 ms energy envelope, runs over 2.8x the floor cut at their first hop = pen-down; 36 grains (45-324 ms) + 6 sharpest pen-down transients shortened to 90 ms taps', where=f'{SND}/grains/, {SND}/taps/, {SND}/bank.json'),
 dict(item='cue engine (cues.py)', made_how='one grain per written stroke from balloons.json (every outline, tail stub and glyph stroke), plate prologue-schedule.json (41 S0 brush strokes) and page_lettering (S1 header/labels); grain = the real recording from a pen-down onset for the stroke duration (min 35 ms, clipped so nothing enters A3 or the B4 pen hold); gain = 0.45+0.55*sqrt(speed/median speed); taps at the pen lift of every full stop and "?" dot; S1 panel stamps = the same real tap low-passed', where='/home/user/bolas/paeleo/scion/oulipo/films/swarm/moins-dun-quart-de-seconde-pour-vivre/sound-build/cues.py'),
 dict(item='ambience bed', made_how='the Mödling recording, deep pauses cut (kept spans %s s), loop start chosen (%.2f s) so the chorus is steady through A3, S0 settle and the last 4 s; RMS 0.014 (~-37 dBFS) against the pen at ~-25 dBFS while writing' % (bank['ambience_kept_spans_s'], cj['amb_offset_s']), where=f'{SND}/ambience-bed.wav'),
]
synth = 'None. No synthesized sound: every grain, tap and the bed are cut from the two foraged recordings (filtering only: high/low-pass, fades, crossfades).'
draft_credits = [dict(title=f['title'], author=f['author'], license=f['license'], license_url=f['license_url'], source_url=f['source_url'], file_url=f['file_url'], used_as=f['used_as']) for f in foraged]
cues_compact = [[c['src'], c['idx'], c['kind'], c['ch'], c['t'], c['dur'], c['gain'], c['ref_frame']] for c in cj['cues']]
out = dict(
 slug='moins-dun-quart-de-seconde-pour-vivre', unit='sound (U3, FORAGE + handmade grain engine)', date='2026-11-17', bar='plan.json (frozen) read only; nothing changed',
 inputs=dict(balloons=f'{SW}/balloons.json (letterer write-on schedule, real, not a sample)', plate_prologue='films/sources/moins-dun-quart-de-seconde-pour-vivre/plate-artist/prologue-schedule.json + plate/strokes.json', timeline='plan.json shots'),
 editor_media=dict(
   dir=SND, module='/home/user/bolas/paeleo/scion/oulipo/films/swarm/moins-dun-quart-de-seconde-pour-vivre/sound-build/cues.py',
   usage="sys.path.insert(0, '<swarm>/sound-build'); import cues; S = cues.build(s1=dict(stamp_t0=<s>, header_t0=<s>)); mix.add(S['ambience'], 0.0, pan=-0.1); mix.add(S['pen'], 0.0, pan=0.08)  # mono float64 at 44100 Hz, 66.0 s",
   prerendered=dict(pen=f'{SND}/pen-track.wav', ambience=f'{SND}/ambience-bed.wav', preview=f'{SND}/mix-preview.wav (pen*0.6 + bed, peak-normalised; listening preview only)'),
   rebuild='python3 sound-build/prep.py && python3 sound-build/cues.py && python3 sound-build/write_sound_json.py',
   s1_note='S1 timings are provisional (stamps from 6.5 s every 4 f, header/labels written in parallel over 19 f after the 7th stamp). Pass the editor\'s actual S1 times to cues.build(s1=...) and the checks re-run.',
   pan_note='sonic perspective: pen close and near centre, ambience far (low, 150 Hz-12 kHz band, slight left)'),
 files=dict(raw=[f['local_path'] for f in foraged], decoded=[f'{SND}/pen-44k.wav', f'{SND}/ambience-44k.wav'], grains=f'{SND}/grains/g00..g35.wav', taps=f'{SND}/taps/t00..t05.wav', bank=f'{SND}/bank.json', cues=f'{SND}/cues.json'),
 foraged=foraged, not_used=not_used, absences=absences, handmade=handmade, synthesized=synth,
 checks=cj['checks'],
 cue_columns=['src', 'idx', 'kind', 'ch', 't_s', 'dur_s', 'gain', 'first_visible_frame'],
 cues=cues_compact,
 draft_credits=draft_credits,
 downloads_this_unit_mb=round((os.path.getsize(f'{SND}/raw/grillenzirpen_moedling.ogg.mp3') + os.path.getsize(f'{SND}/raw/pencil_scratchings.ogg')) / 1e6, 2),
 honest_evidence=dict(measured=['cue onsets vs stroke onsets', 'zero pen samples in A3 and in the B4 pen hold', 'zero cues in post-balloon holds', 'levels'],
                      perceptually_judged='spectrogram/waveform inspection only; no human listening has occurred. The acting listener (#47) still has to hear A3 as deciding, not as a dropout, and the pen hold as the impact before ELSE\'S?'),
)
json.dump(out, open(f'{SW}/sound.json', 'w'), indent=1, ensure_ascii=False)
print('wrote', f'{SW}/sound.json', len(cues_compact), 'cues', out['checks']['all_pass'])
