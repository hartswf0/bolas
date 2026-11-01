# Watching the ALLWAYS references

The operator page renders its watch section from reference-videos.json. It updates when the selected operator changes and removes the previous player. The original 59 prompt objects are unchanged.

The catalog separates complete films, trailers, excerpts, project documentation, original interactive experiences and related context. Each media entry keeps its primary source, viewing URL, embed URL and actual availability-check method. Existing textual research records remain historical records; an available player does not retroactively establish complete-film viewing or listening.

Coverage on 2026-11-01:50 operators have matching video/example/experience embeds.069,070 and104 have clearly labelled related context only.061 and066 retain unresolved titles.067,071,072 and073 have external viewing links with their access limitations. There are 60 available media choices across 53 operators; interactive runtimes and provider/territory restrictions can change.

Words 055 uses the creator-selected 181-second Vimeo film 83934755, not Re:Words.079 includes three separately labelled Qatsi trailers.100 includes all four Short History of the Highrise films.071’s university player reports IP-restricted access.104’s creator-hosted MP4 returned 403 and is marked playable:false. A related talk does not replace that work. No unavailable film is replaced silently with another title.

To update: verify the exact title and uploader against a creator, commissioner, distributor or institution; inspect public embed availability; preserve any Vimeo hash; set playable:false on failed sources. Do not store expiring session tokens. Use related only for supporting context and keep its distinction visible. Full-film access links may require subscription or a supported territory.

reference-watch.js and reference-watch.css are buildless. The static operator HTML calls AllwaysReferences.show on selection; the script also initializes the current hash after its catalog loads. External sources are embedded or linked, not copied into this repository.
