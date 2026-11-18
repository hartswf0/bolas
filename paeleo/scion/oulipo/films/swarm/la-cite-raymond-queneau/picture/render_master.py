"""Render all 720 frames, hash each rgb24 frame, encode out/master.mp4 ONCE, write framemd5."""
import hashlib, json, os, subprocess, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maquette as M
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

def work(k):
    return k, M.frame(k).tobytes()

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    mp4 = os.path.join(OUT, "master.mp4")
    assert not os.path.exists(mp4), "master already encoded"
    ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "960x464", "-r", "24",
                           "-i", "-", "-an", "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-tune", "animation", "-pix_fmt", "yuv420p",
                           "-r", "24", "-fps_mode", "cfr", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    hashes = []
    with Pool(4) as pool:
        for k, b in pool.imap(work, range(M.NFR), chunksize=4):
            assert len(b) == 960 * 464 * 3
            hashes.append(hashlib.sha1(b).hexdigest())
            ff.stdin.write(b)
            if k % 48 == 0:
                print("frame", k, flush=True)
    ff.stdin.close(); assert ff.wait() == 0
    rev = hashlib.sha1("".join(hashes).encode()).hexdigest()
    json.dump({"revision": rev, "frames": len(hashes), "format": "rgb24 960x464, sha1 per frame before encoding", "sha1": hashes},
              open(os.path.join(OUT, "master.sha1.json"), "w"), indent=0)
    subprocess.check_call(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", mp4, "-y", "-f", "framemd5", os.path.join(OUT, "master.framemd5")])
    print("revision", rev)
