"""Write sound-B/ledger.json (evidence records, handmade items, absences) and copy prepared wavs for the editor."""
import json, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REL = "films/sources/la-cite-raymond-queneau/sound-B/raw/"
RAW = os.path.join(FILMS, "sources", "la-cite-raymond-queneau", "sound-B", "raw")
PREP = os.path.join(FILMS, "sources", "la-cite-raymond-queneau",
                    "sound-b-surveillance-uneasy-watching-team-voice-captions-music-drone-fx-ambience-")
CHK = "licence read from Commons extmetadata LicenseShortName on 2026-11-16"
C = "https://commons.wikimedia.org/wiki/File:"
U = "https://upload.wikimedia.org/wikipedia/commons/"
items = [
 dict(id="click_heating", title="Sound of heating system turning on.ogg", author="MKFI", license="Public domain", license_url="",
      source_url=C + "Sound_of_heating_system_turning_on.ogg", file_url=U + "9/9a/Sound_of_heating_system_turning_on.ogg",
      local_path=REL + "click_heating.ogg", what_it_shows="two dry relay/thermostat switch clicks (floor heating switching on); recording, no voice",
      verified_date_or_place=CHK, used_as="Edition B fx: the louder second click is THE relay click, one sample repeated on every window frame and at f696; the softer first click is the door strike re-latching at f374"),
 dict(id="typewriter_wws", title="WWS Typewriter.ogg", author="Work With Sounds / Konrad Gutkowski", license="CC BY 4.0",
      license_url="https://creativecommons.org/licenses/by/4.0", source_url=C + "WWS_Typewriter.ogg", file_url=U + "2/25/WWS_Typewriter.ogg",
      local_path=REL + "typewriter_wws.ogg", what_it_shows="Erika 5 mechanical typewriter: typing, bell, carriage return (identified by onset scan and spectrogram)",
      verified_date_or_place=CHK, used_as="Edition B fx: five single keystrokes on the walker's foot contacts (f200-f345); carriage throw on f518; a re-sequenced run of real keystrokes as teleprinter-like chatter 26.35-28.9 s"),
 dict(id="typewriter_ding", title="406243 stubb typewriter-ding-near-mono.wav", author="_stubb", license="CC0",
      license_url="http://creativecommons.org/publicdomain/zero/1.0/deed.en", source_url=C + "406243_stubb_typewriter-ding-near-mono.wav",
      file_url=U + "9/9f/406243_stubb_typewriter-ding-near-mono.wav", local_path=REL + "typewriter_ding.wav",
      what_it_shows="typewriter end-of-line bell", verified_date_or_place=CHK, used_as="Edition B fx: bell 0.32 s before the carriage throw at f518"),
 dict(id="shutter_holga", title="Holga shuttersound.ogg", author="Doitashimashite at Dutch Wikipedia", license="Public domain", license_url="",
      source_url=C + "Holga_shuttersound.ogg", file_url=U + "e/ec/Holga_shuttersound.ogg", local_path=REL + "shutter_holga.ogg",
      what_it_shows="shutter of a Holga 120S camera (recorded 2006-09-19 by the uploader)", verified_date_or_place=CHK,
      used_as="Edition B fx: the single camera shutter at f566 that ends the held silence"),
 dict(id="wind_pine", title="Wind in Swedish pine forest at 25 mps.ogg", author="W.carter",
      license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
      source_url=C + "Wind_in_Swedish_pine_forest_at_25_mps.ogg", file_url=U + "f/f3/Wind_in_Swedish_pine_forest_at_25_mps.ogg",
      local_path=REL + "Wind_in_Swedish_pine_forest_at_25_mps.ogg", what_it_shows="wind in a pine forest, Tuntorp, Brastad, Lysekil, Sweden (stereo field recording)",
      verified_date_or_place=CHK, used_as="Edition B amb: 8-38 s of the recording, low-passed to 900 Hz and set low under the hum (gated off 16.0-17.5 s and f538-566)"),
 dict(id="hum_mainsbrum", title="MainsBrum50Hz.ogg", author="Julo (assumed by Commons; no machine-readable author)", license="Public domain", license_url="",
      source_url=C + "MainsBrum50Hz.ogg", file_url=U + "c/ce/MainsBrum50Hz.ogg", local_path=REL + "MainsBrum50Hz.ogg",
      what_it_shows="5.5 s of 50 Hz mains hum (finger on a high-sensitivity amplifier input); spectrum 50/150/250 Hz",
      verified_date_or_place=CHK, used_as="Edition B music stem: the 50 Hz hum bed, 4.5 s looped on whole periods, gated off 16.0-17.5 s and f538-566"),
 dict(id="metro_buzzer", title="WWS Metro.ogg", author="Work With Sounds / La Fonderie", license="CC BY 4.0", license_url="https://creativecommons.org/licenses/by/4.0",
      source_url=C + "WWS_Metro.ogg", file_url=U + "e/e8/WWS_Metro.ogg", local_path=REL + "WWS_Metro.ogg",
      what_it_shows="metro train arriving at the Saint-Catherine station: arrival, doors opening, door buzzer (about 38.9-41.9 s, ~2.25 kHz), closing, departure",
      verified_date_or_place=CHK, used_as="Edition B fx: 0.52 s of the door buzzer, band-passed 1.8-7 kHz, on f334 (the door is released electrically)"),
]
if os.path.exists(os.path.join(RAW, "LL-Q150_fra-Estrie-quarante-sept.wav")):
    items.append(dict(id="LL:Estrie", title="LL-Q150 (fra)-Estrie-quarante-sept.wav", author="Estrie (Lingua Libre)", license="CC0",
      license_url="http://creativecommons.org/publicdomain/zero/1.0/deed.en", source_url=C + "LL-Q150_(fra)-Estrie-quarante-sept.wav",
      file_url=U + "1/12/LL-Q150_%28fra%29-Estrie-quarante-sept.wav", local_path=REL + "LL-Q150_fra-Estrie-quarante-sept.wav",
      what_it_shows="Lingua Libre French word recording: 'quarante-sept'", verified_date_or_place=CHK,
      used_as="Edition B voice: 'quarante-sept' through a 300-3000 Hz radio band with tanh saturation, onset on f384 (the key cut)"))
if os.path.exists(os.path.join(RAW, "LL-Q150_fra-Poslovitch-quarante-sept.wav")):
    items.append(dict(id="LL:Poslovitch", title="LL-Q150 (fra)-Poslovitch-quarante-sept.wav", author="Poslovitch (Lingua Libre)", license="CC0",
      license_url="http://creativecommons.org/publicdomain/zero/1.0/deed.en", source_url=C + "LL-Q150_(fra)-Poslovitch-quarante-sept.wav",
      file_url=U + "5/50/LL-Q150_%28fra%29-Poslovitch-quarante-sept.wav", local_path=REL + "LL-Q150_fra-Poslovitch-quarante-sept.wav",
      what_it_shows="Lingua Libre French word recording: 'quarante-sept'", verified_date_or_place=CHK,
      used_as="Edition B voice: 'quarante-sept' through a 300-3000 Hz radio band, onset on f384"))

MIA = "https://www.movingimagearchive.com/sources/"
absences = [
 dict(searched="movingimagearchive.com cache: b6100d97 Singing Wires (1951)", page=MIA + "singing-wires-d80fe718?clip=b6100d97-1545-55d8-bb29-ddf9cb418ca7",
      result="rejected: 0-10 s is music score (moving pitches 441/396/373/262 Hz), 10-24 s narration over music; frames show a telegraph key at a lamp-lit table, not a typewriter"),
 dict(searched="b352abf2 / 575666be The Town and the Telephone (1950)", page=MIA + "town-and-the-telephone-the-41340900",
      result="rejected: continuous narration formants throughout both clips"),
 dict(searched="92d84a1d Telephone and Telegraph (1946)", page=MIA + "telephone-and-telegraph?clip=92d84a1d-83b7-5edf-ac87-62871d347549",
      result="rejected: 3.4 s, narration throughout"),
 dict(searched="regex teletype|teleprint|relay|switchboard|typewriter|telegraph|police radio|radio|telephone|office|hum|machine (clip), plus non-speech audio filter",
      result="candidates aaf17c56 Learning to Set Type (1959), e5e60119 We Learn About the Telephone I (1965), 398f8815 Back of the Mike (1938), 287f3379 Principles of Electricity (1945), 6b7a3bcf Logic By Machine II, 18c68920 Man and Space (1961), 842ae581 (1957) all decoded and checked by spectrogram: narration or music in every usable stretch; nothing taken"),
 dict(searched="Commons: teleprinter / teletype mechanical sound", result="only radio-mode recordings (AMTOR, MT63, PSK31, Radiofax) and a spoken word 'teleprinter'; no mechanical teleprinter. Substituted real typewriter keystrokes re-sequenced at 9 strokes/s (labelled as such)"),
 dict(searched="Commons: door buzzer / electric strike", result="no electric door-strike recording found; used the real door buzzer inside WWS Metro.ogg (CC BY 4.0) instead"),
 dict(searched="Commons: fluorescent buzz, light breeze, Lingua Libre 'soixante'", result="search rate-limited (HTTP 429) and not completed; window 60 (f406, inside the voice-only crossover) is carried by a handmade radio key-off squelch instead"),
 dict(searched="Commons: LL-Q150 (fra) Poslovitch and Estrie quarante-sept (both CC0; licences read from extmetadata)", result="both downloads from upload.wikimedia.org rate-limited (HTTP 429) over ~25 min of spaced retries; voice stem uses a handmade radio squelch on f384 instead. build_B.py decodes and uses the word automatically if either file is placed in sound-B/raw/" if not os.path.exists(os.path.join(RAW, "LL-Q150_fra-Poslovitch-quarante-sept.wav")) else "downloaded"),
]
handmade = json.load(open(os.path.join(HERE, "handmade-B.json")))
json.dump(dict(foraged=items, handmade=handmade, absences=absences), open(os.path.join(HERE, "ledger.json"), "w"), indent=1, ensure_ascii=False)
# credits-format rows for the editor (films/credits/<slug>.json is the editor's to assemble)
json.dump([dict(title=i["title"], author=i["author"], license=i["license"], license_url=i["license_url"], source_url=i["source_url"],
                file_url=i["file_url"], used_as=i["used_as"]) for i in items], open(os.path.join(HERE, "credits-B.json"), "w"), indent=1, ensure_ascii=False)
os.makedirs(PREP, exist_ok=True)
for f in os.listdir(RAW):
    if f.endswith(".dec.wav"): shutil.copy(os.path.join(RAW, f), os.path.join(PREP, f))
print(len(items), "foraged,", len(handmade), "handmade,", len(absences), "absences")
