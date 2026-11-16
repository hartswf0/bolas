"""Repair 1: captions that transcribe ONLY audible speech (real recordings placed in the voice stems).

Reads sound-A/cues-A.json and sound-B/cues-B.json; a cue is speech only if its source is a foraged speech
recording (Lingua Libre 'bonsoir', 'toi', 'bonne nuit', 'quarante-sept'). Writes out/{A,B,X}-speech.vtt and
out/speech-captions.json. Handmade hums and squelches are NOT speech and get no caption.
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); SW = os.path.dirname(HERE); OUT = os.path.join(SW, "out")
TEXT = {"bonsoir": ("— Bonsoir !", "Good evening!"), "toi": ("— Toi ?", "You?"), "bonne_nuit": ("— Bonne nuit.", "Good night."),
        "quarante-sept": ("[radio] Quarante-sept.", "[radio] Forty-seven."),
        "loc_radio": ("[radio : une voix d'homme, mots indistincts]", "[radio: a man's voice, words indistinct]")}


def speech(cues):
    out = []
    for c in cues:
        sid = c.get("source_ledger_id") or ""
        key = "quarante-sept" if sid.startswith("LL:") else ("loc_radio" if sid.startswith("LOC:jukebox") else sid)
        if key in TEXT and "synth" not in sid and "HANDMADE" not in sid:
            out.append((c["t_sound"], key, c.get("picture_event_id"), sid))
    return sorted(out)


def ts(t):
    return f"00:00:{t:06.3f}"


def write(name, items, note):
    blocks = ["WEBVTT\nKind: captions\nLanguage: fr", "NOTE " + note]
    for j, (t, key, pid, sid) in enumerate(items):
        fr, en = TEXT[key]
        blocks.append(f"{name.lower()}s{j + 1}\n{ts(max(0, t - 0.05))} --> {ts(min(30.0, t + 1.5))}\n{fr}\n<i>{en}</i>")
    open(os.path.join(OUT, f"{name}-speech.vtt"), "w", encoding="utf-8").write("\n\n".join(blocks) + "\n")


def main():
    A = speech(json.load(open(os.path.join(SW, "sound-A", "cues-A.json"))))
    B = speech(json.load(open(os.path.join(SW, "sound-B", "cues-B.json"))))
    X = [x for x in A if x[0] < 16.0] + [x for x in B if x[0] >= 16.0]
    n = "Transcribes only real recorded speech heard in this edition (Lingua Libre, CC0/CC BY/CC BY-SA; or Library of Congress National Jukebox, PD). No other captions."
    write("A", A, "Edition A. " + n); write("B", B, "Edition B. " + n); write("X", X, "Edition X. " + n)
    rep = {e: [dict(t=round(t, 3), word=k, picture_event_id=p, source=s) for t, k, p, s in L] for e, L in (("A", A), ("B", B), ("X", X))}
    json.dump(rep, open(os.path.join(OUT, "speech-captions.json"), "w"), indent=1, ensure_ascii=False)
    print({e: len(v) for e, v in rep.items()})


if __name__ == "__main__":
    main()
