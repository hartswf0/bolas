"""Editor repair-round-2 helpers (r3). Reuses r2 helpers (print LUTs, kit pass-through, shot writer)
but writes only under films/sources/un-homme-qui-dort/editor-r3/."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/editor-r2-build")
from ed import *  # noqa
import ed as _ed

E3 = SRC / "editor-r3"
for sub in ("raw", "rgba", "masks", "failure_masks", "fills", "shots", "json", "diag"):
    (E3 / sub).mkdir(parents=True, exist_ok=True)
_ed.E2 = E3          # write_shot() writes into editor-r3/shots/<shot>


def write_shot3(shot, frames_iter, n=None):
    _ed.E2 = E3
    return write_shot(shot, frames_iter, n)
