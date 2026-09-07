/* เวียนขวา — the dash view, driving off a baked ride plan.
 *
 * The plan comes from ride_plan.py: a line the route follows and the cues where
 * the road changes name. Nothing here routes, and nothing here re-routes. That
 * is a decision, not a gap: data/road_graph.json carries no turn restrictions,
 * so a route recomputed at a junction would be a guess dressed as an
 * instruction. Miss a turn and this says rejoin, which it can be sure of.
 *
 * WHERE THE HEADING COMES FROM, AND WHY NOT THE COMPASS
 * A motorcycle is a large magnetised object with an alternator in it, so the
 * magnetometer is the wrong instrument on this vehicle. Heading comes from GPS
 * course over ground. Below WALK_MS that course is noise — standing at a light,
 * a course-derived arrow spins — so the arrow FREEZES and greys instead. A
 * still arrow is wrong for a second; a spinning one is wrong about the road.
 *
 * ?sim=1 replays the plan's own line so the view can be checked without going
 * outside. It is a test harness and says so on screen.
 */
(function () {
  "use strict";

  var RIDE = window.RIDE || null;

  // Below this the GPS course is noise rather than a direction. 2.2 m/s is
  // about 8 km/h — walking pace, slower than anyone rides between junctions.
  var WALK_MS = 2.2;
  // Off the line by more than this and the instruction is no longer about the
  // road under the wheels.
  var OFF_ROUTE_M = 45;
  // Within this of a cue, it is done and the next one is the live one.
  var CUE_DONE_M = 18;

  var el = {};
  ["dash", "arrow", "arrowbox", "turnword", "distnum", "distunit",
   "street-th", "street-en", "fix", "speed", "left", "kind",
   "alert", "alert-th", "alert-en"].forEach(function (id) {
    el[id] = document.getElementById(id);
  });

  function label() {
    // A lap says which way it goes round. เวียนขวา is the direction and is
    // not rideable on the moat's one-way ring, so a lap here is normally the
    // other way by a decision that was made deliberately — and a decision is
    // worth being able to see on the screen it produced.
    if (!RIDE || RIDE.kind !== "lap") return "";
    var th = RIDE.direction === "clockwise" ? "เวียนขวา" : "เวียนซ้าย";
    var waived = RIDE.waived && RIDE.waived.indexOf("turning") >= 0;
    return th + (waived ? " (โดยเจตนา)" : "");
  }

  var heading = null;      // last trustworthy course, degrees
  var frozen = true;
  var cueIndex = 0;

  function rad(d) { return d * Math.PI / 180; }

  function hav(a, b) {
    var R = 6371000;
    var dla = rad(b[0] - a[0]), dlo = rad(b[1] - a[1]);
    var h = Math.sin(dla / 2) * Math.sin(dla / 2)
          + Math.cos(rad(a[0])) * Math.cos(rad(b[0]))
          * Math.sin(dlo / 2) * Math.sin(dlo / 2);
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  function bearing(a, b) {
    var dl = rad(b[1] - a[1]), la1 = rad(a[0]), la2 = rad(b[0]);
    var y = Math.sin(dl) * Math.cos(la2);
    var x = Math.cos(la1) * Math.sin(la2)
          - Math.sin(la1) * Math.cos(la2) * Math.cos(dl);
    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  }

  function nearestOnLine(p) {
    // Which part of the route is under the rider, and how far off it they are.
    if (!RIDE || !RIDE.line || !RIDE.line.length) return null;
    var best = null;
    for (var i = 0; i < RIDE.line.length; i++) {
      var d = hav(p, RIDE.line[i]);
      if (!best || d < best.d) best = { d: d, i: i };
    }
    return best;
  }

  function metres(m) {
    if (m >= 1000) return [(m / 1000).toFixed(m < 10000 ? 1 : 0), "km"];
    return [String(Math.round(m / 5) * 5), "m"];
  }

  function say(thText, enText) {
    if (!thText && !enText) { el.alert.hidden = true; return; }
    el["alert-th"].textContent = thText || "";
    el["alert-en"].textContent = enText || "";
    el.alert.hidden = false;
  }

  function setArrow(deg, settle) {
    if (settle) {
      el.arrowbox.classList.add("settling");
      setTimeout(function () { el.arrowbox.classList.remove("settling"); }, 320);
    }
    el.arrow.style.transform = "rotate(" + deg.toFixed(1) + "deg)";
  }

  function noPlan() {
    el.dash.classList.remove("waiting");
    el["street-th"].textContent = "ยังไม่มีเส้นทาง";
    el["street-en"].textContent = "no ride planned";
    el.fix.textContent = "—";
    say("ยังไม่มีเส้นทางในเครื่อง",
        "Plan a ride with ride_plan.py, then build this app again.");
  }

  function render(pos) {
    var p = [pos.lat, pos.lng];
    var cues = (RIDE && RIDE.cues) || [];

    // Advance past cues already behind the rider.
    while (cueIndex < cues.length
           && hav(p, cues[cueIndex].point) < CUE_DONE_M) {
      cueIndex++;
      setArrow(0, true);
    }

    if (cueIndex >= cues.length) {
      el.dash.classList.remove("waiting", "frozen");
      el.distnum.textContent = "0";
      el.distunit.textContent = "m";
      el.turnword.textContent = "ถึงแล้ว";
      el["street-th"].textContent = "ถึงที่หมาย";
      el["street-en"].textContent = "arrived";
      setArrow(0, true);
      return;
    }

    var cue = cues[cueIndex];
    var to = hav(p, cue.point);
    var mu = metres(to);
    el.distnum.textContent = mu[0];
    el.distunit.textContent = mu[1];
    el.turnword.textContent = cue.say_th || "";
    el["street-th"].textContent = cue.street_th || "";
    el["street-en"].textContent = cue.street_en || "";

    // The arrow points at the next cue RELATIVE to where the rider is facing,
    // which is the only frame that means anything on a moving vehicle.
    if (heading === null) {
      el.dash.classList.add("frozen");
      el.dash.classList.remove("waiting");
    } else {
      el.dash.classList.remove("frozen", "waiting");
      setArrow((bearing(p, cue.point) - heading + 360) % 360, false);
    }

    var near = nearestOnLine(p);
    if (near && near.d > OFF_ROUTE_M) {
      say("ออกนอกเส้นทาง " + Math.round(near.d) + " ม. — กลับเข้าเส้นทาง",
          "off the route by " + Math.round(near.d) + " m — rejoin it; "
          + "this view does not re-route");
    } else {
      say(null, null);
    }

    var doneM = 0;
    if (near && RIDE.line) {
      for (var i = 1; i <= near.i; i++) doneM += hav(RIDE.line[i - 1], RIDE.line[i]);
    }
    var total = RIDE.metres || 0;
    var leftM = Math.max(0, total - doneM);
    var lu = metres(leftM);
    el.left.textContent = "เหลือ " + lu[0] + " " + lu[1];
  }

  function onFix(lat, lng, course, speed) {
    if (speed !== null && speed !== undefined && speed >= WALK_MS
        && course !== null && course !== undefined && !isNaN(course)) {
      heading = course;
      frozen = false;
    } else {
      frozen = true;   // keep the last heading; do not spin on noise
    }
    el.fix.textContent = frozen ? "หยุด · arrow held" : "กำลังไป · live";
    el.speed.textContent = (speed === null || speed === undefined)
      ? "" : Math.round(speed * 3.6) + " กม./ชม.";
    render({ lat: lat, lng: lng });
  }

  // ---- simulation, for checking the view without going outside -----------
  function simulate() {
    var i = 0;
    el.fix.textContent = "SIM";
    var timer = setInterval(function () {
      if (!RIDE || !RIDE.line || i >= RIDE.line.length - 1) {
        clearInterval(timer);
        return;
      }
      var a = RIDE.line[i], b = RIDE.line[i + 1];
      onFix(a[0], a[1], bearing(a, b), 8.0);
      el.fix.textContent = "SIM " + (i + 1) + "/" + RIDE.line.length;
      i++;
    }, 220);
  }

  function start() {
    if (!RIDE || !RIDE.line || !RIDE.line.length) { noPlan(); return; }
    el.kind.textContent = label();
    if (/[?&]sim=1/.test(location.search)) { simulate(); return; }
    if (!navigator.geolocation) {
      say("เครื่องนี้ไม่มีตำแหน่ง", "this device has no location");
      return;
    }
    navigator.geolocation.watchPosition(function (pos) {
      onFix(pos.coords.latitude, pos.coords.longitude,
            pos.coords.heading, pos.coords.speed);
    }, function (err) {
      say("ไม่ได้รับตำแหน่ง", "no location: " + err.message);
    }, { enableHighAccuracy: true, maximumAge: 1000, timeout: 20000 });
  }

  start();
})();
