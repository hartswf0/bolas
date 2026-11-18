"""Writes ../process_graph.json (evidence read from Commons extmetadata 2026-11-16)."""
import json
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / "process_graph.json"
DL = "films/sources/le-chant-du-styrene/process-verse-process-researcher-verse-writer-voice-sound-performer-/dl/"
C = "https://commons.wikimedia.org/wiki/File:"
E = {
 "E-spritzguss": dict(title="Spritzguss teile.jpg", author="Gmhofmann", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
     source_url=C+"Spritzguss_teile.jpg", file_url="https://upload.wikimedia.org/wikipedia/commons/e/e6/Spritzguss_teile.jpg", local_path="films/sources/le-chant-du-styrene/r2/spritzguss.jpg",
     what_it_shows="Two injection-moulded shots of the same tool, teal plastic on white: left, a degated four-arm runner beside its four loose rings; right, a runner with four rings still attached at the gates. Commons category: Sprue.",
     verified_date_or_place="licence read from Commons extmetadata 2026-11-16; photograph date/place unverified; polymer not stated (polystyrene unverified)"),
 "E-moldcavity": dict(title="Mold cavity.jpg", author="Blue tooth7", license="CC BY-SA 3.0", license_url="https://creativecommons.org/licenses/by-sa/3.0",
     source_url=C+"Mold_cavity.jpg", file_url="https://upload.wikimedia.org/wikipedia/commons/4/43/Mold_cavity.jpg", local_path=DL+"mold_cavity.jpg",
     what_it_shows="An actual 4-cavity shot (brackets for an LCD TV power button) with sprue, runner, gates and each part labelled 'Produk (cavity)': the part is the filled cavity, still joined to the runner. Categories: Injection moulding, Moulds, Sprue.",
     verified_date_or_place="licence read 2026-11-16; viewed; date/place unverified"),
 "E-diagram": dict(title="Injection molding diagram.svg", author="ariel cornejo", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
     source_url=C+"Injection_molding_diagram.svg", file_url="https://upload.wikimedia.org/wikipedia/commons/3/32/Injection_molding_diagram.svg", local_path=DL+"im_diagram_1280.png (1280 px PNG render)",
     what_it_shows="Simplified section: a melt charge pushed (P) from the nozzle through sprue, runner and gates into empty cavities between two mould plates; second panel shows the cavities filled as parts, ejector pins below.",
     verified_date_or_place="licence read 2026-11-16; viewed"),
 "E-hotrunner": dict(title="Hot runner x-section injection.png", author="Keyarts at English Wikipedia (image created by Orycon Control Technology)", license="CC BY-SA 3.0", license_url="https://creativecommons.org/licenses/by-sa/3.0",
     source_url=C+"Hot_runner_x-section_injection.png", file_url="", local_path="",
     what_it_shows="Cross-section of a plastic injection mould shown in the injection cycle (per file description).",
     verified_date_or_place="licence read 2026-11-16; not downloaded, not viewed"),
 "E-mold11": dict(title="Injection mold - (11).jpg", author="Bricetofly", license="CC0", license_url="http://creativecommons.org/publicdomain/zero/1.0/deed.en",
     source_url=C+"Injection_mold_-_(11).jpg", file_url="https://upload.wikimedia.org/wikipedia/commons/1/10/Injection_mold_-_%2811%29.jpg", local_path="films/sources/le-chant-du-styrene/kf/mold11.jpg",
     what_it_shows="Machined steel plate of a plastic injection mould with a slide ('système de tiroir pour un moule à injection plastique').",
     verified_date_or_place="licence read 2026-11-16 (also by the test-shot unit); viewed"),
 "E-screw": dict(title="Injection moulding machine screw.jpg", author="Nalbarian", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
     source_url=C+"Injection_moulding_machine_screw.jpg", file_url="", local_path="",
     what_it_shows="Injection-moulding machine screws, before and after purging with commercial purging resin (per description): the screw that melts and conveys the resin.",
     verified_date_or_place="licence read 2026-11-16; not downloaded, not viewed"),
 "E-process-pd": dict(title="Injection moulding process (1).png", author="derivative of Injection_moulding_process.png by Laurens (per Commons Artist field)", license="Public domain", license_url="",
     source_url=C+"Injection_moulding_process_(1).png", file_url="https://upload.wikimedia.org/wikipedia/commons/8/82/Injection_moulding_process_%281%29.png", local_path=DL+"im_process_pd.png",
     what_it_shows="Schematic (viewed): granules (yellow) fall from a hopper onto a rotating screw in a barrel and turn to red melt along it; the melt is pushed through the nozzle into the sprue, runner and cavities of a two-plate mould; the solid runner with its parts is then ejected. All three edges in one drawing.",
     verified_date_or_place="licence read 2026-11-16 (Public domain); viewed"),
 "E-gigaset": dict(title="Gigaset Cordless Telephone Production II - Engel Injection Moulding Machine.webm", author="Sound recordist: Kathinka Engels; photographer and video recordist: Inke Pickhardt (Work With Sounds)", license="CC BY 3.0", license_url="https://creativecommons.org/licenses/by/3.0",
     source_url=C+"Gigaset_Cordless_Telephone_Production_II_-_Engel_Injection_Moulding_Machine.webm", file_url="https://upload.wikimedia.org/wikipedia/commons/transcoded/9/9f/Gigaset_Cordless_Telephone_Production_II_-_Engel_Injection_Moulding_Machine.webm/Gigaset_Cordless_Telephone_Production_II_-_Engel_Injection_Moulding_Machine.webm.480p.vp9.webm", local_path=DL+"gigaset_engel.webm",
     what_it_shows="33.6 s of an Engel injection moulding machine running in the Gigaset telephone factory, Bocholt, Germany, 2009 (Commons category: Injection moulding; Videos of 2009). Continuous machine sound, no speech detected in level/centroid profile.",
     verified_date_or_place="Bocholt, Germany, 2009 (per Commons description/categories); licence read 2026-11-16; frames viewed"),
 "E-pellets": dict(title="Plastic pellets for injection molding.jpg", author="Teemeah", license="CC BY-SA 3.0", license_url="https://creativecommons.org/licenses/by-sa/3.0",
     source_url=C+"Plastic_pellets_for_injection_molding.jpg", file_url="", local_path="",
     what_it_shows="Coloured plastic granules for injection moulding (per description). Category: Plastic pellets.",
     verified_date_or_place="licence read 2026-11-16; not downloaded"),
 "E-granules": dict(title="Uncolored plastic granules.jpg", author="Rohini", license="CC BY-SA 3.0", license_url="https://creativecommons.org/licenses/by-sa/3.0",
     source_url=C+"Uncolored_plastic_granules.jpg", file_url="", local_path="",
     what_it_shows="'Plastic granules used in the process of manufacturing plastic articles' (description).",
     verified_date_or_place="licence read 2026-11-16; not downloaded"),
 "E-styron": dict(title="Styron (Dow Polystyrene) - DPLA - 648a2cd69107879d8c651555a0a31798.jpg", author="Dow Chemical Company (via Science History Institute / DPLA)", license="Public domain", license_url="",
     source_url=C+"Styron_(Dow_Polystyrene)_-_DPLA_-_648a2cd69107879d8c651555a0a31798.jpg", file_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Styron_%28Dow_Polystyrene%29_-_DPLA_-_648a2cd69107879d8c651555a0a31798.jpg/1280px-Styron_%28Dow_Polystyrene%29_-_DPLA_-_648a2cd69107879d8c651555a0a31798.jpg", local_path=DL+"styron_ad_1280.jpg",
     what_it_shows="Colour print advertisement (wartime, 'Chemicals indispensable to industry and victory') for Styron, Dow's polystyrene, showing a hand releasing a stream of granules, a crystal-clear block and a beaded chain: printed matter tying the polymer to granular raw stock and moulding.",
     verified_date_or_place="Commons category PD US; Dow Chemical Company, Midland, Michigan; date not stated on file page (1940s by its slogan, unverified); viewed"),
 "E-bos411": dict(title="Circular of the Bureau of Standards no. 411- organic plastics (IA circularofbureau411klin).pdf", author="Kline, Gordon M. (US National Bureau of Standards)", license="Public domain (PD US Government)", license_url="",
     source_url=C+"Circular_of_the_Bureau_of_Standards_no._411-_organic_plastics_(IA_circularofbureau411klin).pdf", file_url="", local_path="",
     what_it_shows="US government survey of organic plastics (subject: Plastics). Printed-matter anchor for thermoplastics such as polystyrene being moulded; pages not inspected here.",
     verified_date_or_place="licence read 2026-11-16; not downloaded; contents unverified"),
 "E-nub": dict(title="Gunpla sprue nub.jpg", author="Gravis", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
     source_url=C+"Gunpla_sprue_nub.jpg", file_url="", local_path="",
     what_it_shows="A part clipped free of its sprue, showing the gate nub left by the cut (description).",
     verified_date_or_place="licence read 2026-11-16; not downloaded"),
 "E-cutter": dict(title="Gunpla sprue cutter.jpg", author="Gravis", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
     source_url=C+"Gunpla_sprue_cutter.jpg", file_url="", local_path="",
     what_it_shows="Side-cutters sold for clipping plastic model parts from sprues (description).",
     verified_date_or_place="licence read 2026-11-16; not downloaded"),
 "E-cat-im": dict(title="Category:Injection moulding (description)", author="Wikimedia Commons contributors", license="CC BY-SA 4.0 (Commons text)", license_url="https://creativecommons.org/licenses/by-sa/4.0",
     source_url="https://commons.wikimedia.org/wiki/Category:Injection_moulding", file_url="", local_path="",
     what_it_shows="'Injection molding (moulding) is a manufacturing process for producing parts from both thermoplastic and thermosetting plastic ...' Parent categories: Moulding, Plastic processing.",
     verified_date_or_place="wikitext read 2026-11-16"),
}
for k, v in E.items():
    v["id"] = k
    v.setdefault("used_as", "process evidence only (not on screen)")
E["E-spritzguss"]["used_as"] = "process evidence for degate; on screen as GrabCut cutouts (cutout unit)"
E["E-mold11"]["used_as"] = "evidence for M (mould steel); on screen as the Sh3 steel (melt unit)"
E["E-gigaset"]["used_as"] = "evidence for the machine; its audio is the foraged press bed stem (press_foraged.wav) under Sh3a/Sh3b"

ALLOWED = ["PD", "Public domain", "CC0", "CC BY", "CC BY-SA"]
graph = {
 "revision": "process-verse r1 against plan.md r3",
 "fabrication": "injection-moulded thermoplastic parts (polystyrene asserted by the film; the foraged runner's polymer is unverified)",
 "allowed_licences": ALLOWED,
 "nodes": {
  "P1": dict(process_id="P1", name="raw_stock", kind="material", inputs=[], outputs=["polystyrene granules/pellets"],
             material_evidence=["E-pellets", "E-granules", "E-styron"], source_anchor="https://commons.wikimedia.org/wiki/Category:Plastic_pellets", on_screen="Sh4 handmade pellets; Sh5 foraged heap (cutout unit)"),
  "P2": dict(process_id="P2", name="melt", kind="material", inputs=["P1"], outputs=["plasticized melt shot (charge)"],
             material_evidence=["E-process-pd", "E-diagram"], source_anchor=C+"Injection_moulding_process_(1).png", on_screen="Sh3 handmade melt simulation"),
  "M": dict(process_id="M", name="mould", kind="tool", inputs=[], outputs=["cavities + runner + gates + sprue (persistent tool, not consumed)"],
             material_evidence=["E-mold11", "E-diagram", "E-hotrunner"], source_anchor=C+"Injection_mold_-_(11).jpg", on_screen="Sh3 foraged CC0 steel + handmade cavity field from geometry.json"),
  "P3": dict(process_id="P3", name="shot", kind="material", inputs=["P2", "M"], outputs=["runner tree with parts attached at gates"],
             material_evidence=["E-spritzguss", "E-moldcavity"], source_anchor=C+"Mold_cavity.jpg", on_screen="Sh2a/Sh2b cutouts (runner with rings)"),
  "P4": dict(process_id="P4", name="finish", kind="material", inputs=["P3"], outputs=["finished parts (rings)", "runner scrap"],
             material_evidence=["E-spritzguss", "E-nub"], source_anchor=C+"Spritzguss_teile.jpg", on_screen="Sh1 loose-ring cutouts"),
 },
 "edges": [
  dict(id="plasticize", inputs=["P1"], outputs=["P2"], aspect="is plasticized into", reverse_aspect="was melted from", status="verified",
       evidence=["E-process-pd", "E-screw", "E-cat-im", "E-gigaset", "E-styron", "E-bos411"], licence=["Public domain", "CC BY-SA 4.0", "CC BY 3.0"], confidence=0.88,
       note="Granules fed from a hopper are melted by the rotating screw in the heated barrel: shown in the PD schematic Injection moulding process (1).png (viewed). The screw photo was not viewed; the Styron advertisement shows the polystyrene as granules, not the melting. No photograph of the melt itself was found (melt is enclosed in the barrel); the film's melt is a declared handmade simulation."),
  dict(id="inject+cool", inputs=["P2", "M"], outputs=["P3"], aspect="is injected into / solidifies as", reverse_aspect="is the filled hollow of", status="verified",
       evidence=["E-diagram", "E-moldcavity", "E-process-pd", "E-hotrunner", "E-mold11", "E-gigaset"], licence=["CC BY-SA 4.0", "CC BY-SA 3.0", "Public domain", "CC0", "CC BY 3.0"], confidence=0.92,
       note="Diagram (viewed) shows melt charge -> sprue -> runner -> gates -> cavities -> parts; Mold cavity.jpg (viewed) labels each part as the cavity still joined to the runner. This is the edge 'cavity = part'."),
  dict(id="degate", inputs=["P3"], outputs=["P4"], aspect="is degated into", reverse_aspect="was cut from", status="verified",
       evidence=["E-spritzguss", "E-nub", "E-cutter", "E-moldcavity"], licence=["CC BY-SA 4.0", "CC BY-SA 3.0"], confidence=0.95,
       note="Spritzguss teile.jpg (viewed) shows both states of one tool side by side: rings on the runner, and runner + loose rings after degating."),
 ],
 "hypotheses_unverified": [
  dict(id="H-regrind", inputs=["P4:runner scrap"], outputs=["P1"], status="unverified", usable_in_tour=False,
       note="Runner scrap is ground and returned to the hopper as regrind. Real practice, but no open evidence foraged in this run; not an edge of the tour and must not be shown as one."),
  dict(id="H-reference-construction", subject="assets/references/styreneA.webp (1958 still)", status="unverified", usable_in_tour=False,
       note="Whether the reference's red/amber trees are injection-moulded polystyrene sprues, compression-moulded pieces or a staged arrangement is unknown. Not used as process evidence."),
  dict(id="H-polymer-of-foraged-runner", subject="Spritzguss teile.jpg", status="unverified", usable_in_tour=True,
       note="The file does not name the polymer. The tour asserts polystyrene only through the film's subject; the edges hold for injection-moulded thermoplastics generally."),
 ],
 "evidence": list(E.values()),
}
OUT.write_text(json.dumps(graph, indent=1, ensure_ascii=False))
print("wrote", OUT)
