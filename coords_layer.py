#!/usr/bin/env python3
"""Coordinates: read a point written in any common system, and write it in all of them.

The map page has one box where anything can be pasted (decimal degrees, DMS, a
Plus Code, a geohash, UTM or MGRS, a Maidenhead locator, a geo: URI, a link from
OpenStreetMap, Organic Maps, OsmAnd, Google, Apple, Bing, Waze, HERE, Mapillary,
uMap or this site's own map), and a panel that shows the point in every system
with copy buttons and "open in" links.

docs/coords.js sets window.MDCOORDS (and globalThis.MDCOORDS):

    parse(text, {ref:{lat,lng}}?)  -> {lat, lng, zoom?, kind, label?} or null
    format(lat, lng)               -> [{kind, th, en, text}, ...]
    links(lat, lng, name?)         -> [{id, th, en, href}, ...]  open-source tools first

what3words is recognised (kind 'w3w', words, no lat/lng): turning the words into
a point needs their paid API, so the caller shows a message. Mot Dang place
codes (MD-XXXXX, placecode.py) and place URLs come back as kind 'mdcode' and
'mdplace' for the caller to look up.

Plus Codes, geohash, UTM/MGRS, Maidenhead, the Organic Maps ge0 short link and
the OSM short link are implemented here from their public specifications; the
worked examples they are tested against are cited in tests/test_coords.mjs.

Entry point: emit(docs) writes docs/coords.js and returns a status line.
Plain ES5 in an IIFE, no dependencies.
"""
from pathlib import Path

JS = r"""/* coords.js: read and write many coordinate systems. Built by coords_layer.py. */
(function (root) {
  'use strict';

  var CM = { lat: 18.7876, lng: 98.9931, en: 'Chiang Mai', th: 'เชียงใหม่' };
  var CR = { lat: 19.9094, lng: 99.8325, en: 'Chiang Rai', th: 'เชียงราย' };

  // Towns a short Plus Code may be written against ("QXQV+26 Chiang Mai").
  var TOWNS = [CM, CR,
    { lat: 13.7563, lng: 100.5018, en: 'Bangkok', th: 'กรุงเทพ' },
    { lat: 18.5745, lng: 99.0087, en: 'Lamphun', th: 'ลำพูน' },
    { lat: 18.2888, lng: 99.4909, en: 'Lampang', th: 'ลำปาง' },
    { lat: 19.3020, lng: 97.9654, en: 'Mae Hong Son', th: 'แม่ฮ่องสอน' },
    { lat: 19.3583, lng: 98.4400, en: 'Pai', th: 'ปาย' },
    { lat: 19.3667, lng: 98.9667, en: 'Chiang Dao', th: 'เชียงดาว' },
    { lat: 20.2744, lng: 100.0847, en: 'Chiang Saen', th: 'เชียงแสน' },
    { lat: 20.4335, lng: 99.8761, en: 'Mae Sai', th: 'แม่สาย' },
    { lat: 19.1666, lng: 99.9019, en: 'Phayao', th: 'พะเยา' },
    { lat: 18.1445, lng: 100.1403, en: 'Phrae', th: 'แพร่' },
    { lat: 18.7756, lng: 100.7730, en: 'Nan', th: 'น่าน' }];

  var D2R = Math.PI / 180, R2D = 180 / Math.PI;

  // ---- small helpers ------------------------------------------------------
  function sinh(x) { return (Math.exp(x) - Math.exp(-x)) / 2; }
  function cosh(x) { return (Math.exp(x) + Math.exp(-x)) / 2; }
  function atanh(x) { return 0.5 * Math.log((1 + x) / (1 - x)); }
  function normLng(x) { return ((x + 180) % 360 + 360) % 360 - 180; }
  function inThai(lat, lng) { return lat >= 5 && lat <= 21 && lng >= 97 && lng <= 106; }
  function pad(n, w) { var s = String(n); while (s.length < w) s = '0' + s; return s; }
  function fix(x, d) { if (Math.abs(x) < 0.5 * Math.pow(10, -d)) x = 0; return x.toFixed(d); }
  function short6(x) { return String(+fix(x, 6)); }
  function dec(s) {
    try { return decodeURIComponent(String(s).replace(/\+/g, ' ')); } catch (e) { return String(s); }
  }

  function point(lat, lng, kind, zoom, label) {
    lat = +lat; lng = +lng;
    if (!isFinite(lat) || !isFinite(lng) || lat < -90 || lat > 90 || lng < -540 || lng > 540) return null;
    var r = { lat: lat, lng: (lng >= -180 && lng <= 180) ? lng : normLng(lng), kind: kind };
    if (zoom !== undefined && zoom !== null && zoom !== '' && isFinite(+zoom)) r.zoom = +zoom;
    if (label) r.label = String(label);
    return r;
  }

  // ---- Open Location Code (Plus Codes) ------------------------------------
  // Spec: github.com/google/open-location-code/blob/main/Documentation/Specification/specification.md
  var OLC = '23456789CFGHJMPQRVWX', SEP_POS = 8, PAIR_LEN = 10, MAX_DIGITS = 15;
  var PAIR_PREC = 8000, LAT_PREC = 8000 * 3125, LNG_PREC = 8000 * 1024; // 20^3*5^5, 20^3*4^5
  var PAIR_RES = [20.0, 1.0, 0.05, 0.0025, 0.000125];

  function olcValid(code) {
    if (typeof code !== 'string' || code.length < 2) return false;
    code = code.toUpperCase();
    var sep = code.indexOf('+');
    if (sep === -1 || sep !== code.lastIndexOf('+') || sep > SEP_POS || sep % 2 === 1) return false;
    var p = code.indexOf('0');
    if (p > -1) {
      if (sep < SEP_POS || p === 0) return false;
      var runs = code.match(/0+/g);
      if (runs.length > 1 || runs[0].length % 2 === 1 || runs[0].length > SEP_POS - 2) return false;
      if (code.charAt(code.length - 1) !== '+') return false;
    }
    if (code.length - sep - 1 === 1) return false;
    var body = code.replace('+', '').replace(/0+/, '');
    for (var i = 0; i < body.length; i++) if (OLC.indexOf(body.charAt(i)) === -1) return false;
    return true;
  }
  function olcShort(code) { return olcValid(code) && code.indexOf('+') < SEP_POS; }
  function olcFull(code) {
    if (!olcValid(code) || olcShort(code)) return false;
    code = code.toUpperCase();
    return OLC.indexOf(code.charAt(0)) * 20 < 180 && OLC.indexOf(code.charAt(1)) * 20 < 360;
  }

  function olcEncode(lat, lng, len) {
    len = len || PAIR_LEN;
    if (len < 2 || (len < PAIR_LEN && len % 2 === 1)) return null;
    len = Math.min(len, MAX_DIGITS);
    // Integer grid first, so float noise cannot move a point across a cell edge.
    var latV = Math.floor(Math.round(lat * LAT_PREC * 1e6) / 1e6) + 90 * LAT_PREC;
    if (latV < 0) latV = 0; else if (latV >= 180 * LAT_PREC) latV = 180 * LAT_PREC - 1;
    var lngV = Math.floor(Math.round(lng * LNG_PREC * 1e6) / 1e6) + 180 * LNG_PREC;
    var span = 360 * LNG_PREC;
    lngV = ((lngV % span) + span) % span;
    var code = '', i;
    if (len > PAIR_LEN) {
      for (i = 0; i < MAX_DIGITS - PAIR_LEN; i++) {
        code = OLC.charAt((latV % 5) * 4 + (lngV % 4)) + code;
        latV = Math.floor(latV / 5); lngV = Math.floor(lngV / 4);
      }
    } else {
      latV = Math.floor(latV / 3125); lngV = Math.floor(lngV / 1024);
    }
    for (i = 0; i < PAIR_LEN / 2; i++) {
      code = OLC.charAt(latV % 20) + OLC.charAt(lngV % 20) + code;
      latV = Math.floor(latV / 20); lngV = Math.floor(lngV / 20);
    }
    code = code.substring(0, SEP_POS) + '+' + code.substring(SEP_POS);
    if (len >= SEP_POS) return code.substring(0, len + 1);
    return code.substring(0, len) + new Array(SEP_POS - len + 1).join('0') + '+';
  }

  function olcDecode(code) {
    if (!olcFull(code)) return null;
    var c = code.toUpperCase().replace('+', '').replace(/0+/, '').substring(0, MAX_DIGITS);
    var nLat = -90 * PAIR_PREC, nLng = -180 * PAIR_PREC, gLat = 0, gLng = 0, i;
    var digits = Math.min(c.length, PAIR_LEN), pv = 160000; // 20^4
    for (i = 0; i < digits; i += 2) {
      nLat += OLC.indexOf(c.charAt(i)) * pv;
      nLng += OLC.indexOf(c.charAt(i + 1)) * pv;
      if (i < digits - 2) pv /= 20;
    }
    var latP = pv / PAIR_PREC, lngP = pv / PAIR_PREC;
    if (c.length > PAIR_LEN) {
      var rpv = 625, cpv = 256; // 5^4, 4^4
      digits = Math.min(c.length, MAX_DIGITS);
      for (i = PAIR_LEN; i < digits; i++) {
        var d = OLC.indexOf(c.charAt(i));
        gLat += Math.floor(d / 4) * rpv; gLng += (d % 4) * cpv;
        if (i < digits - 1) { rpv /= 5; cpv /= 4; }
      }
      latP = rpv / LAT_PREC; lngP = cpv / LNG_PREC;
    }
    var lo = nLat / PAIR_PREC + gLat / LAT_PREC, lw = nLng / PAIR_PREC + gLng / LNG_PREC;
    var r14 = function (x) { return Math.round(x * 1e14) / 1e14; };
    var a = { latLo: r14(lo), lngLo: r14(lw), latHi: r14(lo + latP), lngHi: r14(lw + lngP), length: Math.min(c.length, MAX_DIGITS) };
    a.lat = Math.min(a.latLo + (a.latHi - a.latLo) / 2, 90);
    a.lng = Math.min(a.lngLo + (a.lngHi - a.lngLo) / 2, 180);
    return a;
  }

  function olcShorten(code, lat, lng) {
    if (!olcFull(code) || code.indexOf('0') !== -1) return null;
    code = code.toUpperCase();
    var a = olcDecode(code);
    if (a.length < 6) return null;
    var range = Math.max(Math.abs(a.lat - Math.max(-90, Math.min(90, lat))), Math.abs(a.lng - normLng(lng)));
    for (var i = PAIR_RES.length - 2; i >= 1; i--) {
      if (range < PAIR_RES[i] * 0.3) return code.substring((i + 1) * 2);
    }
    return code;
  }

  function olcRecover(code, lat, lng) {
    if (!olcShort(code)) return olcFull(code) ? code.toUpperCase() : null;
    code = code.toUpperCase();
    lat = Math.max(-90, Math.min(90, lat)); lng = normLng(lng);
    var padLen = SEP_POS - code.indexOf('+');
    var res = Math.pow(20, 2 - padLen / 2), half = res / 2;
    var a = olcDecode(olcEncode(lat, lng).substr(0, padLen) + code);
    if (!a) return null;
    // The nearest matching cell may be one step away across a grid edge.
    if (lat + half < a.lat && a.lat - res >= -90) a.lat -= res;
    else if (lat - half > a.lat && a.lat + res <= 90) a.lat += res;
    if (lng + half < a.lng) a.lng -= res;
    else if (lng - half > a.lng) a.lng += res;
    return olcEncode(a.lat, a.lng, a.length);
  }

  // ---- geohash --------------------------------------------------------------
  var GH = '0123456789bcdefghjkmnpqrstuvwxyz';
  function ghEncode(lat, lng, len) {
    var la = [-90, 90], lo = [-180, 180], out = '', bits = 0, ch = 0, even = true;
    len = len || 9;
    while (out.length < len) {
      var r = even ? lo : la, v = even ? lng : lat, mid = (r[0] + r[1]) / 2;
      if (v >= mid) { ch = ch * 2 + 1; r[0] = mid; } else { ch = ch * 2; r[1] = mid; }
      even = !even;
      if (++bits === 5) { out += GH.charAt(ch); bits = 0; ch = 0; }
    }
    return out;
  }
  function ghDecode(h) {
    h = String(h).toLowerCase();
    if (!/^[0-9b-hjkmnp-z]{1,12}$/.test(h)) return null;
    var la = [-90, 90], lo = [-180, 180], even = true;
    for (var i = 0; i < h.length; i++) {
      var c = GH.indexOf(h.charAt(i));
      for (var b = 4; b >= 0; b--) {
        var r = even ? lo : la, mid = (r[0] + r[1]) / 2;
        if ((c >> b) & 1) r[0] = mid; else r[1] = mid;
        even = !even;
      }
    }
    return { lat: (la[0] + la[1]) / 2, lng: (lo[0] + lo[1]) / 2, latErr: (la[1] - la[0]) / 2, lngErr: (lo[1] - lo[0]) / 2 };
  }

  // ---- UTM and MGRS (WGS84) -------------------------------------------------
  // Transverse Mercator by Krueger's series in n, to third order (sub-millimetre in a zone).
  var A_ = 6378137, F_ = 1 / 298.257223563, K0 = 0.9996;
  var N1 = F_ / (2 - F_), N2 = N1 * N1, N3 = N2 * N1;
  var AA = A_ / (1 + N1) * (1 + N2 / 4 + N2 * N2 / 64);
  var ALPHA = [N1 / 2 - 2 * N2 / 3 + 5 * N3 / 16, 13 * N2 / 48 - 3 * N3 / 5, 61 * N3 / 240];
  var BETA = [N1 / 2 - 2 * N2 / 3 + 37 * N3 / 96, N2 / 48 + N3 / 15, 17 * N3 / 480];
  var DELTA = [2 * N1 - 2 * N2 / 3 - 2 * N3, 7 * N2 / 3 - 8 * N3 / 5, 56 * N3 / 15];
  var ECC = 2 * Math.sqrt(N1) / (1 + N1);
  var BANDS = 'CDEFGHJKLMNPQRSTUVWX';

  function utmZone(lat, lng) {
    var z = Math.floor((lng + 180) / 6) + 1;
    if (z > 60) z = 60;
    if (lat >= 56 && lat < 64 && lng >= 3 && lng < 12) z = 32;          // Norway
    if (lat >= 72 && lat < 84) {                                        // Svalbard
      if (lng >= 0 && lng < 9) z = 31; else if (lng >= 9 && lng < 21) z = 33;
      else if (lng >= 21 && lng < 33) z = 35; else if (lng >= 33 && lng < 42) z = 37;
    }
    return z;
  }
  function band(lat) { return BANDS.charAt(Math.max(0, Math.min(19, Math.floor((lat + 80) / 8)))); }

  function toUtm(lat, lng, zone) {
    if (!(lat >= -80 && lat <= 84)) return null;
    lng = normLng(lng);
    zone = zone || utmZone(lat, lng);
    var dl = normLng(lng - (zone * 6 - 183)) * D2R, sp = Math.sin(lat * D2R);
    var t = sinh(atanh(sp) - ECC * atanh(ECC * sp));
    var xi = Math.atan2(t, Math.cos(dl)), eta = atanh(Math.sin(dl) / Math.sqrt(1 + t * t));
    var e = eta, n = xi;
    for (var j = 1; j <= 3; j++) {
      e += ALPHA[j - 1] * Math.cos(2 * j * xi) * sinh(2 * j * eta);
      n += ALPHA[j - 1] * Math.sin(2 * j * xi) * cosh(2 * j * eta);
    }
    return { zone: zone, band: band(lat), south: lat < 0,
      easting: 500000 + K0 * AA * e, northing: K0 * AA * n + (lat < 0 ? 10000000 : 0) };
  }

  function fromUtm(zone, south, easting, northing) {
    var xi = (northing - (south ? 10000000 : 0)) / (K0 * AA), eta = (easting - 500000) / (K0 * AA);
    var xp = xi, ep = eta, j;
    for (j = 1; j <= 3; j++) {
      xp -= BETA[j - 1] * Math.sin(2 * j * xi) * cosh(2 * j * eta);
      ep -= BETA[j - 1] * Math.cos(2 * j * xi) * sinh(2 * j * eta);
    }
    var chi = Math.asin(Math.sin(xp) / cosh(ep)), phi = chi;
    for (j = 1; j <= 3; j++) phi += DELTA[j - 1] * Math.sin(2 * j * chi);
    return { lat: phi * R2D, lng: normLng(zone * 6 - 183 + Math.atan2(sinh(ep), Math.cos(xp)) * R2D) };
  }

  var MG_COLS = ['ABCDEFGH', 'JKLMNPQR', 'STUVWXYZ'], MG_ROWS = 'ABCDEFGHJKLMNPQRSTUV';

  function toMgrs(lat, lng, digits) {
    var u = toUtm(lat, lng);
    if (!u) return null;
    digits = digits === undefined ? 5 : digits;
    // MGRS names the square the point is in, so easting and northing are truncated.
    var e = Math.floor(u.easting), n = Math.floor(u.northing);
    var sq = MG_COLS[(u.zone - 1) % 3].charAt(Math.floor(e / 100000) - 1) +
      MG_ROWS.charAt((Math.floor(n / 100000) + (u.zone % 2 ? 0 : 5)) % 20);
    var es = pad(e % 100000, 5).substring(0, digits), ns = pad(n % 100000, 5).substring(0, digits);
    return u.zone + u.band + sq + (digits ? ' ' + es + ' ' + ns : '');
  }

  function fromMgrs(text) {
    var m = /^(\d{1,2})([C-HJ-NP-X])([A-HJ-NP-Z])([A-HJ-NP-V])(\d*)$/.exec(String(text).replace(/\s+/g, '').toUpperCase());
    if (!m || m[5].length % 2 || m[5].length > 10) return null;
    var zone = +m[1];
    if (zone < 1 || zone > 60) return null;
    var col = MG_COLS[(zone - 1) % 3].indexOf(m[3]);
    if (col < 0) return null;
    var row = (MG_ROWS.indexOf(m[4]) - (zone % 2 ? 0 : 5) + 20) % 20;
    var p = m[5].length / 2, cell = Math.pow(10, 5 - p);
    var e = (col + 1) * 100000 + (p ? +m[5].substring(0, p) * cell : 0);
    var n = row * 100000 + (p ? +m[5].substring(p) * cell : 0);
    var south = m[2] < 'N';
    // Row letters repeat every 2000 km; add cycles until the northing reaches the band's floor.
    var floorLat = BANDS.indexOf(m[2]) * 8 - 80;
    var nb = toUtm(floorLat, zone * 6 - 183, zone);
    var nBand = Math.floor(nb.northing / 100000) * 100000;
    while (n < nBand) n += 2000000;
    var ll = fromUtm(zone, south, e + cell / 2, n + cell / 2);
    ll.zone = zone; ll.easting = e + cell / 2; ll.northing = n + cell / 2; ll.precision = p;
    return ll;
  }

  // ---- Maidenhead locator -----------------------------------------------------
  var AZ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  function mhEncode(lat, lng, len) {
    len = len || 6;
    var x = normLng(lng) + 180, y = Math.min(Math.max(lat, -90), 89.9999999) + 90;
    var s = AZ.charAt(Math.floor(x / 20)) + AZ.charAt(Math.floor(y / 10));
    x %= 20; y %= 10;
    s += Math.floor(x / 2) + '' + Math.floor(y);
    x %= 2; y %= 1;
    if (len >= 6) {
      var sx = Math.floor(x * 12), sy = Math.floor(y * 24);
      s += AZ.charAt(sx).toLowerCase() + AZ.charAt(sy).toLowerCase();
      if (len >= 8) s += Math.floor((x - sx / 12) * 120) + '' + Math.floor((y - sy / 24) * 240);
    }
    return s;
  }
  function mhDecode(s) {
    var m = /^([A-R]{2})(\d{2})(?:([A-X]{2})(?:(\d{2}))?)?$/i.exec(String(s));
    if (!m) return null;
    var f = m[1].toUpperCase(), lng = AZ.indexOf(f.charAt(0)) * 20 - 180, lat = AZ.indexOf(f.charAt(1)) * 10 - 90;
    lng += +m[2].charAt(0) * 2; lat += +m[2].charAt(1);
    var w = 2, h = 1;
    if (m[3]) {
      var sub = m[3].toUpperCase();
      w = 2 / 24; h = 1 / 24;
      lng += AZ.indexOf(sub.charAt(0)) * w; lat += AZ.indexOf(sub.charAt(1)) * h;
      if (m[4]) { w /= 10; h /= 10; lng += +m[4].charAt(0) * w; lat += +m[4].charAt(1) * h; }
    }
    return { lat: lat + h / 2, lng: lng + w / 2 };
  }

  // ---- Organic Maps / Maps.me ge0 short links -----------------------------------
  // Port of organicmaps libs/ge0/url_generator.cpp and parser.cpp: a zoom character,
  // then lat/lng as 30-bit integers interleaved 3 bits at a time into base64.
  var B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
  var GE0_MAX = 1073741823; // 2^30 - 1

  function ge0Encode(lat, lng, zoom, nbytes) {
    nbytes = Math.min(nbytes || 9, 10);
    var z = zoom <= 4 ? 0 : (zoom >= 19.75 ? 63 : Math.floor((zoom - 4) * 4));
    var y = (lat + 90) / 180 * GE0_MAX;
    var latI = y < 0 ? 0 : (y > GE0_MAX ? GE0_MAX : Math.round(y));
    var x = (normLng(lng) + 180) / 360 * (GE0_MAX + 1) + 0.5;
    var lngI = (x <= 0 || x >= GE0_MAX + 1) ? 0 : Math.floor(x);
    var s = B64.charAt(z);
    for (var i = 0, sh = 27; i < nbytes; i++, sh -= 3) {
      var a = (latI >> sh) & 7, b = (lngI >> sh) & 7;
      s += B64.charAt((a >> 2 & 1) << 5 | (b >> 2 & 1) << 4 | (a >> 1 & 1) << 3 | (b >> 1 & 1) << 2 | (a & 1) << 1 | (b & 1));
    }
    return s;
  }
  function ge0Decode(s) {
    if (!/^[A-Za-z0-9_-]{2,11}$/.test(s)) return null;
    var zoom = B64.indexOf(s.charAt(0)) / 4 + 4, latI = 0, lngI = 0, c = s.substring(1);
    for (var i = 0, sh = 27; i < c.length; i++, sh -= 3) {
      var a = B64.indexOf(c.charAt(i));
      latI |= ((a >> 5 & 1) << 2 | (a >> 3 & 1) << 1 | (a >> 1 & 1)) << sh;
      lngI |= ((a >> 4 & 1) << 2 | (a >> 2 & 1) << 1 | (a & 1)) << sh;
    }
    var rest = 3 * (10 - c.length) - 1;
    if (rest >= 0) { latI += 1 << rest; lngI += 1 << rest; }
    return { lat: latI / GE0_MAX * 180 - 90, lng: lngI / (GE0_MAX + 1) * 360 - 180, zoom: zoom };
  }
  function ge0Name(n) {
    var swapped = String(n).replace(/[ _]/g, function (c) { return c === ' ' ? '_' : ' '; });
    return encodeURIComponent(swapped).replace(/[!'()*]/g, function (c) {
      return '%' + c.charCodeAt(0).toString(16).toUpperCase();
    });
  }
  function ge0NameDecode(n) {
    var s;
    try { s = decodeURIComponent(n); } catch (e) { s = n; }
    return s.replace(/[ _]/g, function (c) { return c === '_' ? ' ' : '_'; });
  }

  // ---- OpenStreetMap short links (osm.org/go/...) -----------------------------------
  // Port of openstreetmap-website lib/short_link.rb decode.
  var OSMSL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_~';
  function osmShortDecode(str) {
    str = String(str).replace(/@/g, '~');
    var x = 0, y = 0, z = 0, zo = 0;
    for (var i = 0; i < str.length; i++) {
      var t = OSMSL.indexOf(str.charAt(i));
      if (t < 0) { zo -= 1; continue; }
      for (var k = 0; k < 3; k++) {
        x = x * 2 + (t & 32 ? 1 : 0); t <<= 1;
        y = y * 2 + (t & 32 ? 1 : 0); t <<= 1;
      }
      z += 3;
    }
    if (!z) return null;
    x *= Math.pow(2, 32 - z); y *= Math.pow(2, 32 - z);
    return { lng: x * 360 / 4294967296 - 180, lat: y * 180 / 4294967296 - 90, zoom: z - 8 - ((zo % 3) + 3) % 3 };
  }

  // ---- text clean-up ----------------------------------------------------------------
  var PAIRS = { '(': ')', '[': ']', '{': '}', '<': '>', '"': '"', "'": "'", '\u201C': '\u201D', '\u2018': '\u2019', '\u00AB': '\u00BB', '\u300C': '\u300D', '\u300E': '\u300F' };
  var TRAIL = '.,;:!?ฯๆ๏๚๛\u3002\u3001';

  function clean(t) {
    var s = String(t)
      .replace(/[\u200B-\u200D\u2060\uFEFF]/g, '')
      .replace(/[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000\s]+/g, ' ')
      .replace(/[\u0E50-\u0E59]/g, function (d) { return String(d.charCodeAt(0) - 0x0E50); })
      .replace(/[\uFF10-\uFF19]/g, function (d) { return String(d.charCodeAt(0) - 0xFF10); })
      .replace(/[\uFF0C\u3001]/g, ',').replace(/\uFF1B/g, ';').replace(/\uFF1A/g, ':')
      .replace(/\uFF0E/g, '.').replace(/\u2212/g, '-');
    for (;;) {
      s = s.replace(/^ +| +$/g, '');
      var a = s.charAt(0), z = s.charAt(s.length - 1);
      if (!s) return s;
      if (s.length > 1 && PAIRS[a] === z) { s = s.substring(1, s.length - 1); continue; }
      if (TRAIL.indexOf(z) > -1) { s = s.substring(0, s.length - 1); continue; }
      if (TRAIL.indexOf(a) > -1 && a !== '.') { s = s.substring(1); continue; }
      if (PAIRS[a] && a !== '"' && a !== "'" && s.indexOf(PAIRS[a]) < 0) { s = s.substring(1); continue; }
      var closer = null;
      for (var k in PAIRS) if (PAIRS.hasOwnProperty(k) && PAIRS[k] === z && k !== z) closer = k;
      if (closer && s.indexOf(closer) < 0) { s = s.substring(0, s.length - 1); continue; }
      return s;
    }
  }

  // ---- what3words and Mot Dang codes --------------------------------------------------
  var LETTERS = 'a-zA-Z\u00C0-\u024F\u0370-\u03FF\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF' +
    '\u0900-\u097F\u0980-\u09FF\u0E00-\u0E7F\u1E00-\u1EFF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF';
  var W3W = new RegExp('^(\\/\\/\\/)?([' + LETTERS + ']+)\\.([' + LETTERS + ']+)\\.([' + LETTERS + ']+)$');
  var NOT_W3W_END = /^(com|net|org|th|io|co|app|me|info|gov|edu|dev|ly|gl|uk|de|fr|jp|cn|ru|in|html?|php|aspx?|jpe?g|png|gif|pdf|txt|js|css|json|xml)$/i;

  function parseW3w(s) {
    var m = W3W.exec(s);
    if (!m) return null;
    // Without the /// a domain name looks the same, so leave those to the URL reader.
    if (!m[1] && (/^www$/i.test(m[2]) || /^[a-z]{2}$/i.test(m[4]) || NOT_W3W_END.test(m[4]) || /^(co|com|net|org|ac|go|or|gov|edu)$/i.test(m[3]))) return null;
    return { kind: 'w3w', words: (m[2] + '.' + m[3] + '.' + m[4]).toLowerCase() };
  }

  var CROCK = /^[0-9A-HJKMNP-TV-Z]+$/;
  function mdCode(c, lenient) {
    c = c.toUpperCase();
    // Crockford base32 reads I and L as 1 and O as 0 when a person types them.
    if (lenient) c = c.replace(/O/g, '0').replace(/[IL]/g, '1');
    return c.length >= 4 && c.length <= 8 && CROCK.test(c) ? { kind: 'mdcode', code: c } : null;
  }

  // ---- decimal, DMS and DDM -------------------------------------------------------------
  var UNITS = ['\u00B0', "'", '"'];

  function parseLatLng(s0) {
    var s = ' ' + s0 + ' ';
    s = s.replace(/[\u00B0\u00BA\u02DA\u2070]|deg\b/gi, '\u00B0')
      .replace(/''|[\u2033\u201D\u201C\u02DD\u3003]/g, '"')
      .replace(/[\u2032\u2019\u2018\u00B4\u0060]/g, "'")
      .replace(/(latitude|longitude|long|lat|lng|lon|ละติจูด|ลองจิจูด|พิกัด)\s*[:=]?/gi, ' ')
      .replace(/north|เหนือ/gi, ' N ').replace(/south|ใต้/gi, ' S ')
      .replace(/east|ตะวันออก/gi, ' E ').replace(/west|ตะวันตก/gi, ' W ');
    var tok = /^\s*(?:([NSEWnsew])(?![A-Za-z])|([-+]?)(\d+(?:\.\d*)?|\.\d+)\s*([\u00B0'"])?|([,;\/|]))/;
    var comps = [], cur = null, seps = 0, anyMark = false, m;
    s = s.replace(/^\s+|\s+$/g, '');
    while (s.length) {
      m = tok.exec(s);
      if (!m) return null;
      s = s.substring(m[0].length).replace(/^\s+/, '');
      if (m[1]) {
        var h = m[1].toUpperCase();
        anyMark = true;
        if (cur && cur.nums.length && !cur.hemi && !cur.done) { cur.hemi = h; cur.done = true; }
        else { cur = { nums: [], units: [], signs: [], hemi: h, done: false }; comps.push(cur); }
      } else if (m[5]) {
        if (!cur || !cur.nums.length || ++seps > 1) return null;
        cur.done = true;
      } else {
        var unit = m[4] || '';
        if (unit) anyMark = true;
        if (!cur || cur.done || cur.nums.length === 3 || cur.lastDec || (unit === '\u00B0' && cur.nums.length)) {
          cur = { nums: [], units: [], signs: [], hemi: '', done: false }; comps.push(cur);
        }
        cur.nums.push(m[3]); cur.units.push(unit); cur.signs.push(m[2]);
        cur.lastDec = m[3].indexOf('.') > -1;
      }
    }
    // Plain numbers with no marks: split them evenly, "18 47.257 98 59.587" is two DDM values.
    if (!anyMark && !seps) {
      var all = [], signs = [];
      for (var i = 0; i < comps.length; i++) { all = all.concat(comps[i].nums); signs = signs.concat(comps[i].signs); }
      if (all.length !== 2 && all.length !== 4 && all.length !== 6) return null;
      var hl = all.length / 2;
      comps = [{ nums: all.slice(0, hl), units: [], signs: signs.slice(0, hl), hemi: '' },
               { nums: all.slice(hl), units: [], signs: signs.slice(hl), hemi: '' }];
    }
    if (comps.length !== 2) return null;
    var vals = [], parts = 0, anyDec = false;
    for (var c = 0; c < 2; c++) {
      var p = comps[c], n = p.nums.length;
      if (!n) return null;
      parts = Math.max(parts, n);
      var v = 0;
      for (var k = 0; k < n; k++) {
        if (p.units[k] && p.units[k] !== UNITS[k]) return null;
        if (k > 0 && p.signs[k]) return null;
        if (k < n - 1 && p.nums[k].indexOf('.') > -1) return null;
        if (p.nums[k].indexOf('.') > -1) anyDec = true;
        var x = parseFloat(p.nums[k]);
        if (k > 0 && x >= 60) return null;
        v += x / Math.pow(60, k);
      }
      if (p.signs[0] === '-' || p.hemi === 'S' || p.hemi === 'W') v = -v;
      vals.push({ v: v, hemi: p.hemi });
    }
    // Two bare whole numbers ("7 11", "18 98") are too weak to call a place.
    if (parts === 1 && !anyDec && !anyMark) return null;
    var a = vals[0], b = vals[1], lat, lng;
    var aLat = a.hemi === 'N' || a.hemi === 'S', aLng = a.hemi === 'E' || a.hemi === 'W';
    var bLat = b.hemi === 'N' || b.hemi === 'S', bLng = b.hemi === 'E' || b.hemi === 'W';
    if ((aLat && bLat) || (aLng && bLng)) return null;
    if (aLat || bLng) { lat = a.v; lng = b.v; }
    else if (aLng || bLat) { lat = b.v; lng = a.v; }
    else if (Math.abs(a.v) > 90 && Math.abs(b.v) <= 90) { lat = b.v; lng = a.v; }
    else if (inThai(b.v, a.v) && !inThai(a.v, b.v)) { lat = b.v; lng = a.v; }
    else { lat = a.v; lng = b.v; }
    if (Math.abs(lng) > 180) return null;
    return point(lat, lng, parts === 1 ? 'decimal' : (parts === 2 ? 'ddm' : 'dms'));
  }

  // ---- URLs ----------------------------------------------------------------------------
  function parseQuery(q) {
    var out = {};
    if (!q) return out;
    var parts = q.split(/[&;]/);
    for (var i = 0; i < parts.length; i++) {
      var eq = parts[i].indexOf('='), k = eq < 0 ? parts[i] : parts[i].substring(0, eq);
      k = dec(k).toLowerCase();
      if (k && !out.hasOwnProperty(k)) out[k] = eq < 0 ? '' : dec(parts[i].substring(eq + 1));
    }
    return out;
  }

  // "18.78,98.99", "18.78~98.99", "loc:18.78 98.99", optionally followed by ",zoom" or "(Label)".
  // Two whole numbers split only by a space ("q=7 11") read as words, not a place.
  function pairOf(v) {
    if (v === null || v === undefined) return null;
    var m = /^\s*(?:loc:\s*|ll\.)?(-?\d+(?:\.\d+)?)\s*([,~;]\s*|\s+)(-?\d+(?:\.\d+)?)(.*)$/.exec(String(v));
    if (!m) return null;
    if (!/[,~;]/.test(m[2]) && m[1].indexOf('.') < 0 && m[3].indexOf('.') < 0) return null;
    m.splice(2, 1);
    if (m[3] && !/^\s*(?:$|\(|,|\/|\?|&|!)/.test(m[3])) return null;
    var lat = +m[1], lng = +m[2];
    if (Math.abs(lat) > 90 || Math.abs(lng) > 180) return null;
    var lab = /\(([^)]*)\)\s*$/.exec(m[3]);
    return { lat: lat, lng: lng, label: lab ? lab[1] : '', rest: m[3] };
  }

  function hashZLL(h) {
    var m = /^(?:map=)?(\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)/.exec(h || '');
    return m ? { zoom: +m[1], lat: +m[2], lng: +m[3] } : null;
  }

  function splitUrl(s) {
    if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(s)) {
      if (/^\/\//.test(s)) s = 'https:' + s;
      else if (/^(?:[a-z0-9-]+\.)+[a-z]{2,}(?::\d+)?(?=[\/?#]|$)/i.test(s) && !/^[^\/?#]*\.html?(?:[\/?#]|$)/i.test(s)) s = 'https://' + s;
    }
    var m = /^(?:([a-z][a-z0-9+.-]*):\/\/([^\/?#]*))?([^?#]*)(?:\?([^#]*))?(?:#(.*))?$/i.exec(s);
    if (!m) return null;
    return { scheme: (m[1] || '').toLowerCase(), host: (m[2] || '').toLowerCase().replace(/^www\./, '').replace(/:\d+$/, ''),
      path: m[3] || '', query: parseQuery(m[4] || ''), hash: m[5] || '', raw: s };
  }

  function parseGeoUri(s) {
    var m = /^geo:\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)(?:,-?[\d.]+)?(?:;[^?]*)?(?:\?(.*))?$/i.exec(s);
    if (!m) return null;
    var lat = +m[1], lng = +m[2], qs = parseQuery(m[3] || ''), label = '';
    if (qs.q) {
      var p = pairOf(qs.q);
      if (p) { lat = p.lat; lng = p.lng; label = p.label; }
      else if (lat === 0 && lng === 0) return null; // geo:0,0?q=coffee is a search
      else label = qs.q;
    }
    return point(lat, lng, 'geo', qs.z, label);
  }

  function organic(rest) {
    var parts = rest.split(/[?#]/), q = parseQuery(rest.indexOf('?') > -1 ? rest.split('?')[1].split('#')[0] : '');
    var segs = parts[0].split('/'), name = segs[1] ? ge0NameDecode(segs[1]) : '';
    var p = pairOf(segs[0]);
    if (p && !p.rest) return point(p.lat, p.lng, 'organicmaps', q.z, name);
    var g = ge0Decode(segs[0]);
    return g ? point(g.lat, g.lng, 'organicmaps', g.zoom, name) : null;
  }

  function firstPair(q, keys) {
    for (var i = 0; i < keys.length; i++) { var p = pairOf(q[keys[i]]); if (p) return p; }
    return null;
  }

  function google(u) {
    var at = /@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)(?:,(\d+(?:\.\d+)?)z)?/.exec(u.path);
    var zoom = at && at[3] ? at[3] : u.query.z, label = '', m, p;
    var place = /\/maps\/place\/([^\/@]+)/.exec(u.path);
    if (place && !pairOf(dec(place[1]))) label = dec(place[1]);
    if ((m = /!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)/.exec(u.raw))) return point(m[1], m[2], 'google', zoom, label);
    if ((p = firstPair(u.query, ['q', 'query', 'destination', 'daddr', 'll', 'center', 'sll']))) {
      return point(p.lat, p.lng, 'google', zoom, label || p.label);
    }
    var segs = u.path.split('/');
    for (var i = 0; i < segs.length; i++) {
      p = pairOf(dec(segs[i]));
      if (p && segs[i].charAt(0) !== '@') return point(p.lat, p.lng, 'google', zoom, label);
    }
    return at ? point(at[1], at[2], 'google', zoom, label) : null;
  }

  function genericUrl(u, kind) {
    var q = u.query, h = hashZLL(u.hash);
    if (q.mlat && q.mlon) return point(q.mlat, q.mlon, kind, h ? h.zoom : q.zoom || q.z);
    var lng = q.lng || q.lon || q.long;
    if (q.lat && lng) return point(q.lat, lng, kind, q.zoom || q.z);
    var p = firstPair(q, ['ll', 'q', 'center']);
    if (p) return point(p.lat, p.lng, kind, q.z || q.zoom);
    return h ? point(h.lat, h.lng, kind, h.zoom) : null;
  }

  function parseUrl(s) {
    if (/^geo:/i.test(s)) return parseGeoUri(s);
    var m = /^(?:om|ge0):\/\/(.+)$/i.exec(s);
    if (m) return organic(m[1]);
    var u = splitUrl(s);
    if (!u) return null;
    var host = u.host, q = u.query, path = u.path, p, h;
    var mdp = /(?:^|\/)([a-z]{2,4})\/p\/([^\/?#]+?)(?:\.html?)?\/?$/i.exec(path);
    if (!host || /(^|\.)motdang\.net$/.test(host)) {
      if (mdp) return { kind: 'mdplace', prov: mdp[1].toLowerCase(), slug: dec(mdp[2]) };
      h = hashZLL(u.hash);
      return h ? point(h.lat, h.lng, 'mdmap', h.zoom) : null;
    }
    if (/(^|\.)(openstreetmap\.org|osm\.org)$/.test(host)) {
      if ((m = /^\/go\/([A-Za-z0-9_~@-]+)/.exec(path))) {
        var o = osmShortDecode(m[1]);
        return o ? point(o.lat, o.lng, 'osm', o.zoom) : null;
      }
      return genericUrl(u, 'osm');
    }
    if (/(^|\.)(omaps\.app|ge0\.me)$/.test(host)) return organic(u.raw.replace(/^[a-z]+:\/\/[^\/]+\//i, ''));
    if (/(^|\.)osmand\.net$/.test(host)) {
      if ((p = pairOf(q.pin))) return point(p.lat, p.lng, 'osmand', (hashZLL(u.hash) || {}).zoom || q.z);
      return genericUrl(u, 'osmand');
    }
    if (/(^|\.)goo\.gl$/.test(host)) return null; // short links need a network lookup
    if (/(^|\.)google\.[a-z]{2,3}(\.[a-z]{2})?$/.test(host) && (/^\/maps/.test(path) || /^maps\./.test(host))) return google(u);
    if (/^maps\.apple(\.com)?$/.test(host)) {
      p = firstPair(q, ['q', 'll', 'coordinate', 'sll', 'center', 'daddr']);
      if (!p) return null;
      return point(p.lat, p.lng, 'apple', q.z, q.name || (pairOf(q.q) ? '' : q.q));
    }
    if (/(^|\.)bing\.com$/.test(host)) {
      p = firstPair(q, ['cp', 'q']);
      return p ? point(p.lat, p.lng, 'bing', q.lvl) : null;
    }
    if (/(^|\.)waze\.com$/.test(host)) {
      p = firstPair(q, ['ll', 'to', 'q']);
      return p ? point(p.lat, p.lng, 'waze', q.zoom || q.z) : null;
    }
    if (/(^|\.)here\.com$/.test(host)) {
      if ((p = pairOf(q.map))) return point(p.lat, p.lng, 'here', (/^,(\d+(?:\.\d+)?)/.exec(p.rest) || [])[1]);
      if ((m = /^\/l\/([^\/?#]+)/.exec(path)) && (p = pairOf(dec(m[1])))) {
        return point(p.lat, p.lng, 'here', null, p.rest.replace(/^,/, ''));
      }
      return null;
    }
    if (/(^|\.)mapillary\.com$/.test(host)) return q.lat && q.lng ? point(q.lat, q.lng, 'mapillary', q.z) : null;
    if (/(^|\.)(what3words\.com|w3w\.co)$/.test(host)) return parseW3w(dec(path.replace(/^\/+/, '')));
    if (/(^|\.)geohash\.org$/.test(host)) {
      var g = ghDecode(path.replace(/^\//, '').split('/')[0]);
      return g ? point(g.lat, g.lng, 'geohash') : null;
    }
    if (/(^|\.)plus\.codes$/.test(host)) {
      var a = olcDecode(dec(path.replace(/^\//, '').replace(/%2B/i, '+')).replace(/ /g, '+'));
      return a ? point(a.lat, a.lng, 'pluscode') : null;
    }
    return genericUrl(u, /umap/.test(host) ? 'umap' : 'url');
  }

  function isUrlish(s) {
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(s) || /^geo:/i.test(s)) return true;
    if (/\s/.test(s)) return false;
    return /^[#\/]/.test(s) ||
      /^(?:[a-z0-9-]+\.)+[a-z]{2,}(?::\d+)?(?=[\/?#]|$)/i.test(s) || /^[\w.-]+\.html?(?:[?#]|$)/i.test(s) ||
      /^[a-z]{2,4}\/p\//i.test(s);
  }

  // ---- Plus Code with a town name -------------------------------------------------------
  function townIn(text) {
    var best = null, bestAt = Infinity, low = ' ' + text.toLowerCase() + ' ';
    for (var i = 0; i < TOWNS.length; i++) {
      var t = TOWNS[i], at = text.indexOf(t.th);
      var m = new RegExp('[^a-z]' + t.en.toLowerCase() + '[^a-z]').exec(low);
      if (m && (at < 0 || m.index < at)) at = m.index;
      if (at > -1 && at < bestAt) { best = t; bestAt = at; }
    }
    return best;
  }

  function parseOlc(s, ref) {
    var m = /^([0-9A-Za-z]{0,8}\+[0-9A-Za-z]*)(?:[\s,]+([\s\S]*))?$/.exec(s);
    if (!m || !olcValid(m[1])) return null;
    var code = m[1].toUpperCase(), full = code;
    if (olcShort(code)) {
      var r = (m[2] && townIn(m[2])) || ref;
      full = olcRecover(code, r.lat, r.lng);
    }
    var a = full && olcDecode(full);
    return a ? point(a.lat, a.lng, 'pluscode') : null;
  }

  // ---- UTM text ---------------------------------------------------------------------
  function parseUtm(s) {
    var m = /^(?:zone\s*)?(\d{1,2})\s*([C-HJ-NP-Xc-hj-np-x]|north|south)?\s*[\s,]\s*(?:e\s*)?(\d{5,7}(?:\.\d+)?)\s*(?:m?e)?\s*[\s,]\s*(?:n\s*)?(\d{1,8}(?:\.\d+)?)\s*(?:m?n)?$/i.exec(s);
    if (!m) return null;
    var zone = +m[1], L = m[2] || '', e = +m[3], n = +m[4], south;
    if (zone < 1 || zone > 60 || e < 100000 || e > 900000 || n > 10000000) return null;
    if (/^(south|s)$/.test(L)) south = true;              // lower-case n/s: hemisphere
    else if (/^(north|n)$/.test(L) || !L) south = false;
    else if (/^south$/i.test(L)) south = true;
    else if (/^north$/i.test(L)) south = false;
    else {
      L = L.toUpperCase();
      south = L < 'N';
      if (L === 'S') {
        // Band S lies at 32-40 N; a northing that does not land there means "south".
        var tryN = fromUtm(zone, false, e, n);
        if (tryN.lat < 31 || tryN.lat > 41) south = true;
      }
    }
    var ll = fromUtm(zone, south, e, n);
    return point(ll.lat, ll.lng, 'utm');
  }

  // ---- bare tokens: Maidenhead, geohash, Mot Dang code --------------------------------
  function parseToken(s) {
    if (!/^[0-9A-Za-z]{4,12}$/.test(s) || !/[A-Za-z]/.test(s)) return null;
    // Letters alone read as a geohash only when long and nearly vowel-free, so words fall through.
    if (!/\d/.test(s)) {
      var g = /^[0-9b-hjkmnp-z]{8,12}$/.test(s) && ghDecode(s);
      return g && (s.match(/[euy]/g) || []).length / s.length < 0.2 ? point(g.lat, g.lng, 'geohash') : null;
    }
    var mh = mhDecode(s), gh = s.length >= 5 ? ghDecode(s) : null;
    var upper = s === s.toUpperCase();
    // Maidenhead is written with a lower-case subsquare (OK08fs); Mot Dang codes are upper case.
    if (mh && (inThai(mh.lat, mh.lng) || /^[A-Ra-r]{2}\d{2}[a-x]{2}(\d{2})?$/.test(s))) return point(mh.lat, mh.lng, 'maidenhead');
    if (gh && !upper && inThai(gh.lat, gh.lng)) return point(gh.lat, gh.lng, 'geohash');
    var md = mdCode(s, false);
    if (md) return md;
    if (mh) return point(mh.lat, mh.lng, 'maidenhead');
    if (gh && /^[0-9a-z]+$/.test(s)) return point(gh.lat, gh.lng, 'geohash');
    return null;
  }

  function parse(text, opts) {
    if (text === null || text === undefined) return null;
    var s = clean(text);
    if (!s) return null;
    var ref = (opts && opts.ref && isFinite(opts.ref.lat) && isFinite(opts.ref.lng)) ? opts.ref : CM;
    var r = parseW3w(s);
    if (r) return r;
    if (isUrlish(s)) return parseUrl(s);
    var m = /^MD[-\s]?([0-9A-Za-z]{4,8})$/i.exec(s);
    if (m && (r = mdCode(m[1], true))) return r;
    if ((m = /^(?:gh|geohash)\s*:\s*([0-9A-Za-z]{1,12})$/i.exec(s))) {
      var g = ghDecode(m[1]);
      return g ? point(g.lat, g.lng, 'geohash') : null;
    }
    if (s.indexOf('+') > -1 && (r = parseOlc(s, ref))) return r;
    if (/^\d{1,2}\s*[A-Za-z]/.test(s) && (m = fromMgrs(s)) && /\d{2}$/.test(s.replace(/\s+/g, ''))) {
      return point(m.lat, m.lng, 'mgrs');
    }
    return parseUtm(s) || parseToken(s) || parseLatLng(s);
  }

  // ---- writing ------------------------------------------------------------------------
  function dms(v, pos, neg) {
    var t = Math.round(Math.abs(v) * 360000); // hundredths of a second
    var d = Math.floor(t / 360000), r = t - d * 360000, m = Math.floor(r / 6000), sec = (r - m * 6000) / 100;
    return d + '\u00B0' + pad(m, 2) + "'" + pad(sec.toFixed(2), 5) + '"' + (v < 0 ? neg : pos);
  }
  function ddm(v, pos, neg) {
    var t = Math.round(Math.abs(v) * 600000); // ten-thousandths of a minute
    var d = Math.floor(t / 600000), m = (t - d * 600000) / 10000;
    return d + '\u00B0' + pad(m.toFixed(4), 7) + "'" + (v < 0 ? neg : pos);
  }
  function nearestTown(lat, lng) {
    var a = Math.abs(lat - CM.lat) + Math.abs(lng - CM.lng), b = Math.abs(lat - CR.lat) + Math.abs(lng - CR.lng);
    return a <= b ? CM : CR;
  }

  function format(lat, lng) {
    lat = +lat; lng = +lng;
    if (!isFinite(lat) || !isFinite(lng) || lat < -90 || lat > 90) return [];
    lng = normLng(lng);
    var out = [], code = olcEncode(lat, lng, 10);
    function row(kind, th, en, text) { if (text) out.push({ kind: kind, th: th, en: en, text: text }); }
    row('decimal', 'พิกัดทศนิยม', 'Decimal', fix(lat, 6) + ', ' + fix(lng, 6));
    row('dms', 'องศา ลิปดา ฟิลิปดา', 'Degrees, minutes, seconds', dms(lat, 'N', 'S') + ' ' + dms(lng, 'E', 'W'));
    row('ddm', 'องศา ลิปดาทศนิยม', 'Degrees, decimal minutes', ddm(lat, 'N', 'S') + ' ' + ddm(lng, 'E', 'W'));
    row('pluscode', 'พลัสโค้ด', 'Plus Code', code);
    var town = nearestTown(lat, lng), a = olcDecode(code);
    // Google's short form drops four digits; that is safe within about 0.3 degrees of the town.
    if (Math.max(Math.abs(a.lat - town.lat), Math.abs(a.lng - town.lng)) < 0.3) {
      row('pluscode_short', 'พลัสโค้ดแบบสั้น', 'Plus Code, short', code.substring(4) + ' ' + town.en);
    }
    row('geohash', 'จีโอแฮช', 'Geohash', ghEncode(lat, lng, 9));
    var u = toUtm(lat, lng);
    if (u) {
      row('utm', 'พิกัดยูทีเอ็ม', 'UTM', u.zone + u.band + ' ' + Math.round(u.easting) + ' ' + Math.round(u.northing));
      row('mgrs', 'กริดทหาร', 'MGRS', toMgrs(lat, lng, 5));
    }
    row('maidenhead', 'กริดวิทยุสมัครเล่น', 'Maidenhead', mhEncode(lat, lng, 6));
    return out;
  }

  function links(lat, lng, name) {
    lat = +lat; lng = normLng(+lng);
    if (!isFinite(lat) || !isFinite(lng)) return [];
    var la = short6(lat), lo = short6(lng), ll = la + ',' + lo, nm = name ? String(name) : '';
    return [
      { id: 'osm', th: 'โอเพนสตรีทแมป', en: 'OpenStreetMap',
        href: 'https://www.openstreetmap.org/?mlat=' + la + '&mlon=' + lo + '#map=17/' + la + '/' + lo },
      { id: 'organicmaps', th: 'ออร์แกนิกแมปส์', en: 'Organic Maps',
        href: 'https://omaps.app/' + ge0Encode(lat, lng, 17, 9) + (nm ? '/' + ge0Name(nm) : '') },
      { id: 'osmand', th: 'ออสมแอนด์', en: 'OsmAnd',
        href: 'https://osmand.net/map?pin=' + ll + '#17/' + la + '/' + lo },
      { id: 'geo', th: 'แอปแผนที่ในเครื่อง', en: 'Map app (geo:)',
        href: 'geo:' + ll + '?q=' + ll + (nm ? '(' + encodeURIComponent(nm) + ')' : '') },
      { id: 'umap', th: 'ยูแมป', en: 'uMap',
        href: 'https://umap.openstreetmap.fr/en/map/new/#17/' + la + '/' + lo },
      { id: 'google', th: 'กูเกิลแมปส์', en: 'Google Maps',
        href: 'https://www.google.com/maps/search/?api=1&query=' + ll },
      { id: 'apple', th: 'แผนที่แอปเปิล', en: 'Apple Maps',
        href: 'https://maps.apple.com/?ll=' + ll + '&q=' + encodeURIComponent(nm || ll) },
      { id: 'waze', th: 'เวซ', en: 'Waze', href: 'https://www.waze.com/ul?ll=' + ll + '&zoom=17' }
    ];
  }

  var api = {
    parse: parse, format: format, links: links,
    CHIANG_MAI: CM, CHIANG_RAI: CR,
    olc: { encode: olcEncode, decode: olcDecode, shorten: olcShorten, recoverNearest: olcRecover,
      isValid: olcValid, isShort: olcShort, isFull: olcFull },
    geohash: { encode: ghEncode, decode: ghDecode },
    utm: { fromLatLng: toUtm, toLatLng: fromUtm },
    mgrs: { fromLatLng: toMgrs, toLatLng: fromMgrs },
    maidenhead: { encode: mhEncode, decode: mhDecode },
    ge0: { encode: ge0Encode, decode: ge0Decode },
    osmShortLink: { decode: osmShortDecode }
  };
  if (typeof window !== 'undefined') window.MDCOORDS = api;
  root.MDCOORDS = api;
})(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this));
"""


def emit(docs):
    """Write docs/coords.js; return a status line for the build log."""
    out = Path(docs) / "coords.js"
    out.write_text(JS, encoding="utf-8")
    return f"  coords: coords.js ({len(JS.encode('utf-8')):,} bytes)"
