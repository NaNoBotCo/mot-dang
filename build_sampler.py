"""Where a build spends its time: a two-second stack sampler, written to JSON.

build.py starts it when MD_PROFILE names a file; importers/server_walk.sh sets
that on motdang-build. Every two seconds it notes where the main thread is, and
every thirty it rewrites the file with the most frequent stacks, the seconds
spent in each phase of build(), and the order the phases ran in. A build killed
at its time limit still leaves the picture from its last thirty seconds.

The first reading (2026-10-10, injected by hand into a running build) found 90%
of the time inside _moat_crossings re-parsing data/canonical/cm.json.

    python3 build_sampler.py /srv/state/build-profile.json     # read one
"""
import collections
import json
import os
import sys
import threading
import time


def _rss_mb():
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    try:
        import resource
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return r // (1024 * 1024) if sys.platform == "darwin" else r // 1024
    except Exception:
        return None


def start(path, every=2.0, flush=30.0):
    main = threading.main_thread().ident
    stacks, phase_n, order = collections.Counter(), collections.Counter(), []
    t0 = time.time()

    def loop():
        last_flush, last_phase = 0.0, None
        while True:
            time.sleep(every)
            f = sys._current_frames().get(main)
            stack = []
            while f is not None:
                stack.append("%s:%s" % (os.path.basename(f.f_code.co_filename), f.f_code.co_name))
                f = f.f_back
            stack.reverse()
            stacks[" > ".join(stack[-6:])] += 1
            phase = " > ".join(stack[:3])
            phase_n[phase] += 1
            now = time.time()
            if phase != last_phase:
                order.append([round(now - t0), phase])
                last_phase = phase
            if now - last_flush >= flush:
                last_flush = now
                tmp = path + ".tmp"
                with open(tmp, "w") as fh:
                    json.dump({"started": t0, "seconds": round(now - t0), "every": every,
                               "samples": sum(stacks.values()), "rss_mb": _rss_mb(),
                               "phase_seconds": [[p, round(n * every)] for p, n in phase_n.most_common()],
                               "top": stacks.most_common(40), "order": order[-500:]}, fh)
                os.replace(tmp, path)

    threading.Thread(target=loop, name="build-sampler", daemon=True).start()


def report(path):
    d = json.load(open(path))
    n = d["samples"] or 1
    print("%d s sampled, %d samples, %s MB resident" % (d["seconds"], d["samples"], d.get("rss_mb")))
    print("\nseconds per phase:")
    for p, s in d["phase_seconds"][:25]:
        print("%7d  %s" % (s, p))
    print("\nmost frequent stacks:")
    for k, c in d["top"][:20]:
        print("%5.1f%%  %s" % (100.0 * c / n, k))


if __name__ == "__main__":
    report(sys.argv[1])
