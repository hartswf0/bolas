"""Step 6 (editor): merge the three unit ledgers into films/credits/la-cite-raymond-queneau.json.

Only items that appear in the film are credited. Licences must be PD, CC0, CC BY or CC BY-SA; each Commons
licence was re-read from extmetadata on 2026-11-16 (scratch result copied into out/credits-reverify.json).
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.dirname(HERE)
FILMS = os.path.abspath(os.path.join(SW, "..", ".."))
ALLOWED = re.compile(r"^(public domain|pd|cc0|cc by( |-)?\d|cc by-sa( |-)?\d)", re.I)


def norm(e, used):
    return {"title": e["title"], "author": e.get("author", ""), "license": e["license"], "license_url": e.get("license_url", ""),
            "source_url": e["source_url"], "file_url": e.get("file_url", ""), "used_as": used, **({"credit_line": e["credit_line"]} if e.get("credit_line") else {})}


EXTRA = json.load(open(os.path.join(SW, "editor", "speech-credits.json"))) if os.path.exists(os.path.join(SW, "editor", "speech-credits.json")) else []


def main():
    P = json.load(open(os.path.join(FILMS, "sources", "la-cite-raymond-queneau", "picture", "ledger.json")))
    A = json.load(open(os.path.join(SW, "sound-A", "ledger.json")))
    B = json.load(open(os.path.join(SW, "sound-B", "ledger.json")))
    rev = json.load(open(os.path.join(SW, "out", "commons-reverify.json")))
    cues_a = json.load(open(os.path.join(SW, "sound-A", "cues-A.json")))
    used_a = {c["source_ledger_id"] for c in cues_a}
    out = []
    for e in P["foraged"]:
        out.append(norm(e, "picture (paper model sheet): " + e["used_as"]))
    for e in A:
        if e.get("kind") == "FORAGED" and e["id"] in used_a:
            stems = {c.get("stem", "") for c in cues_a if c["source_ledger_id"] == e["id"]}
            eds = "Editions A, X and C (amb)" if "amb" in stems else "Editions A and X"
            out.append(norm(e, eds + ": " + e["used_as"]))
    for e in B["foraged"]:
        out.append(norm(e, e["used_as"].replace("Edition B amb", "Editions B and C amb", 1)))
    seen, merged = {}, []
    for c in out:
        k = c["source_url"]
        if k in seen:
            seen[k]["used_as"] += " | " + c["used_as"]
        else:
            seen[k] = c; merged.append(c)
    for c in merged:
        assert ALLOWED.match(c["license"]), c
        t = "File:" + c["source_url"].split("File:")[-1].replace("_", " ") if "commons.wikimedia.org" in c["source_url"] else None
        if t:
            from urllib.parse import unquote
            t = unquote(t)
            r = rev.get(t)
            assert r, ("not re-verified", t)
            lic = r["LicenseShortName"]
            assert lic.lower().replace("public domain", "pd").split()[0] in c["license"].lower().replace("public domain", "pd"), (lic, c["license"])
            c["license_reverified"] = f"{lic} (Commons extmetadata, 2026-11-16)"
        else:
            c["license_reverified"] = ("LoC item rights statement re-read 2026-11-16" + (": National Jukebox, recordings published before 1923 entered the public domain on 1 Jan 2022"
                                       if "jukebox" in c["source_url"] else ""))
    # review-1 corrections (attribution reviewer): LoC rights wording + credit line; full Victor credit; 'song' -> orchestral 78
    for c in merged:
        if "loc.gov/item/musftpsets" in c["source_url"]:
            # repair 2: mapped to PD under a stated reason (the sheet carries no copyrightable expression)
            c["license"] = ("Public domain (treated as PD: an unmarked blank sheet of paper carries no copyrightable expression; "
                            "LoC rights statement: no known copyright restrictions)")
            c["license_url"] = "https://www.loc.gov/legal/"
            c["author"] = "Nels Astner (designer); Federal Theatre Project collection"
            c["credit_line"] = "Library of Congress, Music Division, Federal Theatre Project Collection"
            c["license_reverified"] = ("LoC item rights statement re-read 2026-11-16: the Library knows of no copyright restrictions; "
                                       "the item is a scan of a blank sheet (no drawing, text or design is used: only clean, unmarked "
                                       "areas of the paper are cropped), so no copyrightable expression is reproduced")
        if "Victor-73522a" in c["source_url"]:
            c["author"] = ("Victor Schrammel-Orchester (performers); Carl Millöcker (composer); Commons Artist field: Carl Flisch; "
                           "via publicdomainproject.org; recorded 11 Sep 1922")
            c["title"] = "Victor-73522a-b26758.ogg: « O, du himmelblauer See », Victor 73522-A (matrix B-26758), orchestral 78-rpm recording"
        c["used_as"] = c["used_as"].replace("a song through a wall", "an orchestral 78 through a wall").replace("radio song", "radio (orchestral 78)")
    for c in merged:
        u = c["used_as"].lower()
        if c["source_url"].startswith("https://www.loc.gov") or "picture (paper model sheet)" in u:
            c["modified"] = "adapted: cropped, cut into shapes, warped, levels-graded per channel"
        else:
            c["modified"] = "adapted: cut, filtered, levelled (and where stated slowed, looped or re-timed)"
        lic = c["license"].upper()
        if lic.startswith("CC BY") and not c.get("license_url"):
            raise SystemExit(("missing licence URL", c["title"]))
        if lic.startswith("CC0") and not c.get("license_url"):
            c["license_url"] = "https://creativecommons.org/publicdomain/zero/1.0/"
        if c["license_url"].startswith("http://"):
            c["license_url"] = "https://" + c["license_url"][7:]
        if c["license"].lower().startswith("public domain") and not c.get("license_url"):
            c["license_url"] = "https://creativecommons.org/publicdomain/mark/1.0/"
    for e in EXTRA:
        if os.path.exists(os.path.join(FILMS, e.pop("_local"))):
            merged.append(e)
    fonts = [{"title": t, "author": a, "license": "SIL Open Font License 1.1", "license_url": "https://openfontlicense.org/",
              "source_url": u, "file_url": "", "used_as": "typeface on the reel's cards and caption band", "modified": "unmodified"}
             for t, a, u in (("Instrument Serif", "The Instrument Serif Project Authors (2022)", "https://github.com/Instrument/instrument-serif"),
                             ("Instrument Sans", "The Instrument Sans Project Authors (2022)", "https://github.com/Instrument/instrument-sans"),
                             ("IBM Plex Mono", "IBM Corp. (2017)", "https://github.com/IBM/plex"))]
    json.dump(merged, open(os.path.join(FILMS, "credits", "la-cite-raymond-queneau.json"), "w"), indent=1, ensure_ascii=False)
    print(len(merged), "credits")
    json.dump(fonts, open(os.path.join(SW, "out", "typeface-credits.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
