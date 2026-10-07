"""
Automated checks for CO-Home-Bound.

Runs the game headlessly with no network (so it also proves the bundled three.js
fallback works), then:
  1. loads the page and makes sure nothing throws,
  2. lets a simple bot play full runs to confirm the obstacle patterns leave escape routes,
  3. confirms the scenic stretches around Bigfoot, Red Rocks and the Capitol carry no trains or barriers,
  4. confirms no roadside scenery appears or vanishes while it is on screen.

Setup (once):   pip install playwright && python -m playwright install chromium
Run:            python tests/check_game.py            (add --games 5 for more bot runs)
"""
import argparse, asyncio, json, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME = (ROOT / "index.html").as_uri()

BOT = r"""
window.__bot = (games) => {
  const R = window.HomewardTrail, I = R._internals; I.debug.hold = true;
  const out = [];
  const blocks = (o, P) => o.type === 'train' && (o.moving || (P.y <= 3.0 && !o.hasRamp));
  const rampH = (o) => Math.max(0, Math.min(1, o.z / o.len)) * 3.4;
  function firstBlock(l, P) {            // distance until lane l is blocked (0 = blocked right now)
    let best = Infinity; const s = I.G.speed;
    for (const o of I.obstacles) {
      if (o.lane !== l) continue;
      if (o.type === 'ramp' && l !== P.lane && o.z > -0.5 && o.z - o.len < 0.8 && rampH(o) > 1.0) { best = 0; continue; }
      if (!blocks(o, P) || o.z - o.len > 0.8) continue;
      let d = Math.max(0, -o.z);
      if (o.moving) d = d * s / (s + (o.active ? Math.max(o.vel, o.vmax * 0.6) : o.vmax) + 0.01);
      best = Math.min(best, d);
    }
    return best;
  }
  for (let g = 0; g < games; g++) {
    document.getElementById(R.state === 'menu' ? 'btnPlay' : 'btnRestart').click();
    let t = 0, lastAct = 0;
    while (R.state === 'playing' || (R.state === 'won' && I.G.speed > 0)) {
      const P = I.P, s = I.G.speed; t += 1 / 60;
      if (t - lastAct > 0.1) {
        const fb = [0, 1, 2].map(l => firstBlock(l, P)), cur = P.lane, stepD = s * 0.16 + 1.5;
        let target = cur, bestD = fb[cur];
        for (const l of [0, 1, 2]) {
          if (l === cur) continue;
          let ok = true;
          for (let k = 1; k <= Math.abs(l - cur); k++) { const m = cur + Math.sign(l - cur) * k; if (fb[m] <= stepD * k + (m === l ? 0 : 1)) ok = false; }
          if (ok && fb[l] > bestD + 4) { bestD = fb[l]; target = l; }
        }
        if (target !== cur && fb[cur] < s * 2.2 + 20) { I.act(target < cur ? 'left' : 'right'); lastAct = t; }
        for (const o of I.obstacles) {
          if (o.lane !== P.lane) continue; const d = -o.z;
          if (o.type === 'barrier' && d > 0 && d < s * 0.2 + 0.8 && P.onGround) { I.act('up'); lastAct = t; break; }
          if (o.type === 'overhead' && d > 0 && d < s * 0.12 + 1.2 && P.slideT <= 0.1) { I.act('down'); lastAct = t; break; }
        }
      }
      I.step(1 / 60);
    }
    out.push({ distance: Math.round(I.G.distance), home: I.G.finished, reason: I.G.reason || '' });
    for (let k = 0; k < 400 && R.state === 'won'; k++) I.step(1 / 60);
  }
  return out;
};
window.__inspect = () => {
  // fly above the track (nothing can hit the runner) and watch every spawn and every prop
  const R = window.HomewardTrail, I = R._internals; I.debug.hold = true;
  document.getElementById(R.state === 'menu' ? 'btnPlay' : 'btnRestart').click();
  const sights = [[590, 'capitol'], [2330, 'bigfoot'], [3320, 'redrocks']];
  const seen = new Set(), prev = new Map(), inScenic = [], pops = [];
  let n = 0;
  while (R.state === 'playing' && n++ < 40000) {
    I.P.y = 60; I.P.vy = 0; I.step(1 / 30);
    for (const o of I.obstacles) {
      if (seen.has(o)) continue; seen.add(o);
      if (o.type === 'deco' || o.type === 'finish') continue;
      const d = I.G.distance - o.z;
      for (const [at, name] of sights) if (d > at - 120 && d - (o.len || 0) < at + 30) inScenic.push([name, o.type, Math.round(d)]);
    }
    for (const s of I.scenery) {
      const v = s.obj.visible, z = s.obj.position.z, p = prev.get(s);
      if (p && p.v !== v && z > -160 && z < 30 && p.z > -160 && p.z < 30) pops.push([Math.round(I.G.distance), Math.round(z)]);
      prev.set(s, { v, z });
    }
  }
  return { reached: Math.round(I.G.distance), inScenic, pops };
};
"""

async def main(games):
    failures = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        page = await browser.new_page(viewport={"width": 800, "height": 600})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        # offline: block the CDN and web fonts so the bundled vendor/three.min.js fallback is used
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        await page.goto(GAME)
        await page.wait_for_timeout(1500)
        if not await page.evaluate("typeof window.HomewardTrail === 'object' && typeof THREE === 'object'"):
            failures.append("game did not start (three.js fallback or script error)")
        await page.evaluate(BOT)

        print("1) Load ................ ok" if not errors else f"1) Load ................ errors: {errors}")
        runs = await page.evaluate(f"window.__bot({games})")
        home = sum(r["home"] for r in runs)
        print(f"2) Bot runs ............ {home}/{len(runs)} made it home")
        for r in runs: print("     ", json.dumps(r))
        if home == 0: failures.append("the bot never reached home - check the obstacle patterns")

        info = await page.evaluate("window.__inspect()")
        print(f"3) Scenic stretches .... {'clear' if not info['inScenic'] else info['inScenic'][:5]}")
        print(f"4) Scenery pop-in ...... {'none' if not info['pops'] else info['pops'][:5]}")
        if info["inScenic"]: failures.append("obstacles spawned in a scenic stretch")
        if info["pops"]: failures.append("scenery changed visibility while on screen")
        if errors: failures.append("page errors")
        await browser.close()
    if failures:
        print("\nFAILED:", "; ".join(failures)); sys.exit(1)
    print("\nAll checks passed.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--games", type=int, default=3)
    asyncio.run(main(ap.parse_args().games))
