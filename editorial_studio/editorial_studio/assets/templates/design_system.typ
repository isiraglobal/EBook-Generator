// ============================================================================
//  Land Investor's Field Manual — editorial design system
// ----------------------------------------------------------------------------
//  Primitives and named styles that the page families in layout_library.typ
//  compose. Two rules hold everywhere:
//
//  1. Decoration never sits on top of text. Corner brackets, rules, sidebars
//     and markers reserve their own space or are part of a component's frame.
//  2. Every size here is a named style, so a page family states a role
//     ("display", "lead", "caption") rather than a point size, and the scale
//     can be retuned in one place.
//
//  All decoration is vector. No glyphs, no box-drawing characters, no images
//  that are not generated from the manuscript's own structure.
// ============================================================================

#import "helpers.typ": *

// ── Type scale ──────────────────────────────────────────────────────────────
// A4 reading measure. Display sizes step up hard from the body so a chapter
// opener and a running page never read as the same kind of object.
#let scale = (
  cover-title: 46pt,
  display: 34pt,        // chapter titles
  display-sm: 27pt,     // feature page titles
  section: 21pt,       // major section heading
  sub: 16pt,           // subsection heading
  lead: 14pt,          // lead paragraph
  body: 10.5pt,
  body-sm: 9.5pt,
  caption: 8.7pt,
  meta: 8pt,           // uppercase labels and running metadata
  giant: 92pt,         // chapter number, display only
  giant-sm: 66pt,
)

// ── Named text styles ───────────────────────────────────────────────────────
#let dsp(t, th, size: scale.display, fill: none, weight: "bold", align: none) = {
  let s = text(
    t,
    font: th.heading-font,
    size: size,
    weight: weight,
    fill: if fill == none { th.ink },
    tracking: -0.3pt,
  )
  if align == none { s } else { align(s) }
}

#let label(t, th, color: none, size: scale.meta) = text(
  upper(str(t)),
  font: th.heading-font,
  size: size,
  weight: "bold",
  fill: if color == none { th.brass },
  tracking: 1.7pt,
)

#let lead(t, th) = text(
  t,
  font: th.body-font,
  size: scale.lead,
  style: "italic",
  fill: th.ink,
)

#let caption(t, th, color: none) = text(
  t,
  font: th.body-font,
  size: scale.caption,
  fill: if color == none { th.slate },
)

#let mono(t, th, color: none) = text(
  t,
  font: th.mono-font,
  size: scale.body-sm,
  fill: if color == none { th.slate },
)

// ── Rules ───────────────────────────────────────────────────────────────────
#let rule(th, weight: 0.6pt, color: none, width: 100%, length: none) = line(
  length: if length == none { width } else { length },
  stroke: weight + (if color == none { th.rule } else { color }),
)

// A rule with a short accent that marks the start of a run of text. The accent
// is a second segment, not an overlay.
#let accent-rule(th, weight: 0.6pt, color: none, accent: 22mm) = grid(
  columns: (accent, 1fr),
  gutter: 5pt,
  rule(th, weight: weight, color: color),
  rule(th, weight: weight * 2.2, color: if color == none { th.brass } else { color }),
)

// Two hairlines with a hair of space between: the title-page and feature-page
// border, where a single rule reads as an accident.
#let double-rule(th, color: none) = block(width: 100%)[
  #rule(th, weight: 0.5pt, color: color)
  #v(1.1pt)
  #rule(th, weight: 0.5pt, color: color)
]

#let side-rule(th, weight: 1.6pt, color: none, length: 100%) = block(
  width: weight,
  height: length,
  fill: if color == none { th.brass } else { color },
)

// ── Corner brackets ─────────────────────────────────────────────────────────
// Four L-shaped strokes marking a frame's corners. The caller reserves the
// padding, so these never touch type.
#let corner-brackets(th, size: 12pt, weight: 0.9pt, color: none, inset: 0pt) = {
  let c = if color == none { th.brass } else { color }
  let arm(w, h) = grid(
    columns: (w, 1fr),
    row-gutter: 0pt,
    rule(th, weight: weight, color: c, width: w, length: weight),
    block(width: 1fr, height: h),
  )
  block(width: 100%, inset: inset)[
    #set align(left + top)
    #arm(size, size)
    #v(-size)
    #grid(
      columns: (size, 1fr, size),
      row-gutter: 0pt,
      rule(th, weight: weight, color: c, width: weight, length: size),
      box(width: 1fr),
      grid(columns: (1fr,), rule(th, weight: weight, color: c, width: 100%, length: weight)),
    )
    #v(-size)
    #align(right)[#arm(size, size)]
  ]
}

// ── Section number badge ────────────────────────────────────────────────────
// A numeral in a hairline square, for pages that name their own position in
// the book.
#let number-badge(n, th, color: none, side: 17pt) = block(
  width: side,
  height: side,
  stroke: 0.6pt + (if color == none { th.rule } else { color }),
  radius: 1pt,
  align(center + horizon)[
    #text(
      font: th.mono-font,
      size: scale.body-sm,
      weight: "bold",
      fill: if color == none { th.brass } else { color },
    )[#str(n)]
  ],
)

// A plain numeral in the heading face, for pages that need one without a box.
#let section-index(n, th, color: none) = text(
  str(n),
  font: th.mono-font,
  size: scale.meta,
  weight: "bold",
  fill: if color == none { th.terracotta } else { color },
  tracking: 0.6pt,
)

// ── Panels ──────────────────────────────────────────────────────────────────
// Panels own their padding. Nothing is placed inside one by absolute position.

#let tinted-panel(body, th, fill: none, edge: none, pad: 13pt, weight: 0.5pt, radius: 1.5pt) = block(
  width: 100%,
  breakable: true,
  fill: if fill == none { th.panel-bg } else { fill },
  stroke: weight + (if edge == none { th.rule } else { edge }),
  radius: radius,
  inset: pad,
)[#body]

// A full-bleed dark panel. Only for page families that compose the dark
// background themselves; never a drop-in for a light page.
#let dark-panel(body, th, fill: none, pad: 18pt) = block(
  width: 100%,
  breakable: true,
  fill: if fill == none { th.ink } else { fill },
  inset: pad,
)[
  #set text(fill: th.paper)
  #body
]

// A narrow coloured band that marks the top edge of a feature frame.
#let title-band(title, th, fill: none, fg: none, pad: 7pt) = block(
  width: 100%,
  fill: if fill == none { th.ink } else { fill },
  inset: (left: pad * 1.4, right: pad, top: pad * 0.8, bottom: pad * 0.8),
)[
  #set align(left + horizon)
  #label(title, th, color: if fg == none { th.paper } else { fg })
]

// ── Result panel ────────────────────────────────────────────────────────────
// Where a worked example's answer lands. The one place a value is allowed to
// be large, because it is the point of the page.
#let result-panel(value, caption, th, fill: none, edge: none) = tinted-panel(
  [
    #set par(justify: false, first-line-indent: 0em)
    #label(caption, th, color: if edge == none { th.green } else { edge }, size: scale.caption)
    #v(0.5em)
    #text(font: th.mono-font, size: scale.lead, weight: "bold", fill: th.ink)[#value]
  ],
  th,
  fill: fill,
  edge: if edge == none { th.green } else { edge },
  pad: 14pt,
)

// ── Input cells ─────────────────────────────────────────────────────────────
// A small structured field for assumptions and figures. Numbers use the mono
// face so columns of them align.
#let input-cell(label, value, th, note: none) = block(
  width: 100%,
  fill: th.panel-bg,
  stroke: (top: 1.1pt + th.ink, rest: 0.4pt + th.rule),
  inset: (left: 8pt, right: 8pt, top: 6pt, bottom: 7pt),
)[
  #set par(justify: false, first-line-indent: 0em, spacing: 0.2em)
  #label(label, th, color: th.slate, size: scale.caption)
  #v(0.25em)
  #text(font: th.mono-font, size: scale.body, weight: "bold", fill: th.ink)[#value]
  #if note != none [
    #v(0.2em)
    #caption(note, th)
  ]
]

// ── Ruled answer area ───────────────────────────────────────────────────────
// Writing space for a workbook. The caller passes the height it actually has
// left, so the rules never sit stranded in the top third of the page.
#let answer-area(rules, th, gap: 15pt) = block(width: 100%, breakable: false)[
  #for _ in range(rules) [
    #v(gap, weak: true)
    #rule(th, weight: 0.4pt)
  ]
]

// ── Checkbox row ────────────────────────────────────────────────────────────
// A drawn square, not a glyph, so it scales and takes the rule colour.
#let checkbox(th, side: 8.5pt, color: none) = block(
  width: side,
  height: side,
  stroke: 0.7pt + (if color == none { th.slate } else { color }),
  radius: 0.6pt,
)

#let checkbox-item(text, th, number: none, warn: false, gap: 9pt) = {
  let marker = if number == none {
    checkbox(th, color: if warn { th.terracotta } else { none })
  } else {
    text(
      font: th.mono-font,
      size: scale.body-sm,
      weight: "bold",
      fill: if warn { th.terracotta } else { th.brass },
    )[#str(number) + "."]
  }
  block(width: 100%, breakable: true, below: 0.42em)[
    #set par(justify: false, first-line-indent: 0em, leading: th.lead)
    #grid(
      columns: (if number == none { 8.5pt } else { 13pt }, 1fr),
      gutter: gap,
      align: (top, top),
      marker,
      text(size: scale.body, fill: th.ink)[#text],
    )
  ]
}

// ── Pull quote ──────────────────────────────────────────────────────────────
// An oversized opening mark, set as a real glyph in the heading face. Only
// called for sentences the manuscript itself supports.
#let pull-quote(quote, th, attribution: none, size: 25pt) = block(width: 100%, breakable: true)[
  #set par(justify: false, first-line-indent: 0em, leading: 1.16)
  #text(
    font: th.heading-font,
    size: size * 2.1,
    weight: "bold",
    fill: th.cream-deep,
    baseline: -size * 0.62,
  )[“]
  #h(0.1em)
  #text(font: th.body-font, size: size, style: "italic", fill: th.ink)[#quote]
  #if attribution != none [
    #v(0.7em)
    #label(attribution, th, color: th.slate, size: scale.caption)
  ]
]

// ── Caption with a figure number ────────────────────────────────────────────
#let figure-caption(number, text, th, color: none) = block(width: 100%, breakable: true, above: 0.45em)[
  #set par(justify: true, first-line-indent: 0em, leading: 1.3)
  #grid(
    columns: (16mm, 1fr),
    gutter: 5pt,
    align: (left, left),
    label("Fig. " + str(number), th, color: color, size: scale.caption),
    caption(text, th),
  )
]

// ── Two-column rule between columns ─────────────────────────────────────────
#let column-divider(th) = block(width: 0.4pt, height: 100%, fill: th.rule)

#let page-section-break = v(7mm, weak: true)

// ── Measure helpers ─────────────────────────────────────────────────────────
#let measure-lines(body, th) = measure(block(width: 100%, body)).height / th.lead

// A named set of content proportions, so families state an intent rather than
// three arbitrary fractions.
#let proportions = (
  narrow: 0.60,
  standard: 0.72,
  wide: 0.86,
  full: 1.0,
  sidebar: 0.28,
  split-main: 0.62,
  split-alt: 0.38,
)
