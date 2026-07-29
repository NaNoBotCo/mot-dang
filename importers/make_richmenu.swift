// Draw the LINE rich menu image. Run via importers/make_richmenu.py.
//
// Swift rather than Pillow because Pillow here is built without raqm, so it
// cannot shape Thai — vowels and tone marks land in the wrong place, which on
// a brand asset is worse than no asset. CoreText shapes Thai correctly, and
// /usr/bin/swift ships with the command line tools.
//
// LINE accepts 2500x1686 for a six-button menu; tap areas are declared
// separately in the JSON the Python side writes, in this same pixel space.

import Foundation
import AppKit

let W = 2500.0, H = 1686.0
let COLS = 3.0, ROWS = 2.0
let cw = W / COLS, ch = H / ROWS

struct Cell {
    let glyph: String
    let th: String
    let en: String
    let tint: NSColor
}

// Row one is why anybody opens it; row two is what we want them to do. Put the
// pleasure first — a person who came for today's fortune is already here when
// they notice their own shop needs a phone number.
let cells: [Cell] = [
    Cell(glyph: "🔮", th: "ดวงวันนี้", en: "Today's fortune",
         tint: NSColor(srgbRed: 0.76, green: 0.25, blue: 0.11, alpha: 1)),
    Cell(glyph: "🎋", th: "เซียมซี", en: "Fortune sticks",
         tint: NSColor(srgbRed: 0.62, green: 0.42, blue: 0.09, alpha: 1)),
    Cell(glyph: "🎪", th: "งานในเมือง", en: "What's on",
         tint: NSColor(srgbRed: 0.16, green: 0.47, blue: 0.84, alpha: 1)),
    Cell(glyph: "🏪", th: "ร้านนี้ของฉัน", en: "This is my shop",
         tint: NSColor(srgbRed: 0.56, green: 0.18, blue: 0.07, alpha: 1)),
    Cell(glyph: "📷", th: "ส่งรูป", en: "Send a photo",
         tint: NSColor(srgbRed: 0.18, green: 0.49, blue: 0.31, alpha: 1)),
    Cell(glyph: "✏️", th: "ตรงนี้ผิด", en: "Something's wrong",
         tint: NSColor(srgbRed: 0.35, green: 0.31, blue: 0.28, alpha: 1)),
]

// Draw into a bitmap of exactly these pixel dimensions. NSImage.lockFocus()
// picks up the screen's backing scale, which on a Retina Mac silently doubles
// the output to 5000x3372 — a size LINE rejects.
guard let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil, pixelsWide: Int(W), pixelsHigh: Int(H),
        bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
        colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0) else { exit(1) }
rep.size = NSSize(width: W, height: H)
guard let gctx = NSGraphicsContext(bitmapImageRep: rep) else { exit(1) }
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = gctx

// paper
NSColor(srgbRed: 0.984, green: 0.965, blue: 0.933, alpha: 1).setFill()
NSBezierPath(rect: NSRect(x: 0, y: 0, width: W, height: H)).fill()

func draw(_ s: String, font: NSFont, colour: NSColor, centreX: Double, baselineY: Double) {
    let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: colour]
    let a = NSAttributedString(string: s, attributes: attrs)
    let sz = a.size()
    a.draw(at: NSPoint(x: centreX - sz.width / 2, y: baselineY))
}

let thaiFont = NSFont(name: "Thonburi-Bold", size: 96)
    ?? NSFont.boldSystemFont(ofSize: 96)
let enFont = NSFont.systemFont(ofSize: 52, weight: .medium)
let glyphFont = NSFont(name: "AppleColorEmoji", size: 190)
    ?? NSFont.systemFont(ofSize: 190)

for (i, cell) in cells.enumerated() {
    let col = Double(i % Int(COLS)), row = Double(i / Int(COLS))
    // AppKit's origin is bottom-left; LINE counts rows from the top.
    let x = col * cw
    let y = H - (row + 1) * ch
    let inset = 18.0
    let r = NSRect(x: x + inset, y: y + inset, width: cw - inset * 2, height: ch - inset * 2)

    let card = NSBezierPath(roundedRect: r, xRadius: 46, yRadius: 46)
    NSColor.white.setFill(); card.fill()
    cell.tint.withAlphaComponent(0.9).setStroke(); card.lineWidth = 7; card.stroke()

    // a soft band of the tint at the top of each card, so the six read as a set
    let band = NSBezierPath(roundedRect: NSRect(x: r.minX, y: r.maxY - 130,
                                                width: r.width, height: 130),
                            xRadius: 46, yRadius: 46)
    cell.tint.withAlphaComponent(0.13).setFill(); band.fill()

    let cx = x + cw / 2
    draw(cell.glyph, font: glyphFont, colour: .black, centreX: cx, baselineY: y + ch * 0.52)
    draw(cell.th, font: thaiFont, colour: cell.tint, centreX: cx, baselineY: y + ch * 0.30)
    draw(cell.en, font: enFont, colour: NSColor(white: 0.45, alpha: 1),
         centreX: cx, baselineY: y + ch * 0.18)
}

NSGraphicsContext.restoreGraphicsState()

guard let png = rep.representation(using: .png, properties: [:]) else { exit(1) }
let out = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "richmenu.png"
try png.write(to: URL(fileURLWithPath: out))
print("wrote \(out)")
