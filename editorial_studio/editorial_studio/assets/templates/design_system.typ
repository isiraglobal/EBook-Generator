// ============================================================================
//  Land Investor's Field Manual — editorial design system
// ----------------------------------------------------------------------------
//  Primitives and named styles that the page families in layout_library.typ
//  compose. Three rules hold everywhere:
//
//  1. Decoration never sits on top of text. Corner brackets, rules, sidebars
//     and markers reserve their own space or are part of a component's frame.
//  2. Every size here is a named style, so a page family states a role
//     ("display", "lead", "caption") rather than a point size, and the whole
//     scale can be retuned in one place.
//  3. Colour defaults are resolved with a hoisted `let` before they reach a
//     function argument. A `if` written directly as an argument value inside a
//     content block is parsed as markup, which silently yields `none`.
//
//  All decoration is vector. No glyphs, no box-drawing characters, no imagery
//  that is not generated from the manuscript's own structure.
// ============================================================================

#import "helpers.typ": *

// ── Type scale ──────────────────────────────────────────────────────────────
// A4 reading measure. Display sizes step up hard from the body, so a chapter
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

// ── Content proportions ─────────────────────────────────────────────────────
// Named intents rather than three arbitrary fractions per family.
#let proportions = (
  narrow: 0.60,
  standard: 0.72,
  wide: 0.86,
  full: 1.0,
  sidebar: 0.28,
  split-main: 0.62,
  split-alt: 0.38,
)

// ── Colour resolution ───────────────────────────────────────────────────────
// One helper, so no caller has to write a conditional expression inline.
#let ink-of(th, c) = if c == none { th.ink } else { c }
#let brass-of(th, c) = if c == none { th.brass } else { c }
#let slate-of(th, c) = if c == none { th.slate } else { c }
#let rule-of(th, c) = if c == none { th.rule } else { c }
#let panel-of(th, c) = if c == none { th.panel-bg } else { c }

// ── Named text styles ───────────────────────────────────────────────────────
#let dsp(t, th, size: scale.display, color: none, weight: "bold", tracking: -0.3pt) = text(
  t,
  font: th.heading-font,
  size: size,
  weight: weight,
  fill: ink-of(th, color),
  tracking: tracking,
)

#let label(t, th, color: none, size: scale.meta) = {
  let c = brass-of(th, color)
  text(upper(str(t)), font: th.heading-font, size: size, weight: "bold", fill: c, tracking: 1.7pt)
}

#let lead(t, th, color: none) = text(
  t,
  font: th.body-font,
  size: scale.lead,
  style: "italic",
  fill: ink-of(th, color),
)

#let caption(t, th, color: none) = text(
  t,
  font: th.body-font,
  size: scale.caption,
  fill: slate-of(th, color),
)

#let mono(t, th, color: none) = text(
  t,
  font: th.mono-font,
  size: scale.body-sm,
  fill: slate-of(th, color),
)

// ── Rules ───────────────────────────────────────────────────────────────────
#let rule(th, weight: 0.6pt, color: none, width: 100%) = line(
  length: width,
  stroke: weight + rule-of(th, color),
)

// A rule with a short heavier accent that marks the start of a run of text. The
// accent is a second segment, not an overlay.
#let accent-rule(th, weight: 0.6pt, color: none, accent: 22mm) = {
  let c = rule-of(th, color)
  grid(
    columns: (accent, 1fr),
    gutter: 5pt,
    rule(th, weight: weight, color: c),
    rule(th, weight: weight * 2.4, color: brass-of(th, color)),
  )
}

// Two hairlines with a hair of space between: the title-page and feature-page
// border, where a single rule reads as an accident.
#let double-rule(th, color: none) = block(width: 100%)[
  #rule(th, weight: 0.5pt, color: color)
  #v(1.1pt)
  #rule(th, weight: 0.5pt, color: color)
]

#let side-rule(th, weight: 1.6pt, color: none, length: 100%) = {
  let c = brass-of(th, color)
  block(width: weight, height: length, fill: c)
}

// ── Corner brackets ─────────────────────────────────────────────────────────
// Four L-shaped strokes marking a frame's corners. The caller reserves the
// padding, so these never touch type.
#let corner-brackets(th, size: 12pt, weight: 0.9pt, color: none) = {
  let c = brass-of(th, color)
  let h-arm = line(length: size, stroke: weight + c)
  let v-arm = line(length: size, stroke: weight + c)
  block(width: 100%)[
    #set align(left + top)
    #grid(
      columns: (size, 1fr, size),
      column-gutter: 0pt,
      h-arm,
      box(width: 1fr),
      grid(columns: (1fr,), align(right)[#h-arm]),
    )
    #v(-0.5pt)
    #grid(
      columns: (size, 1fr, size),
      column-gutter: 0pt,
      v-arm,
      box(width: 1fr),
      v-arm,
    )
    #v(-size)
    #grid(
      columns: (size, 1fr, size),
      column-gutter: 0pt,
      grid(columns: (1fr,), h-arm),
      box(width: 1fr),
      h-arm,
    )
  ]
}

// ── Section number badge ────────────────────────────────────────────────────
// A numeral in a hairline square, for pages that name their position in the
// book.
#let number-badge(n, th, color: none, side: 18pt) = {
  let c = brass-of(th, color)
  block(
    width: side,
    height: side,
    stroke: 0.6pt + rule-of(th, color),
    radius: 1pt,
    align(center + horizon)[
      #text(font: th.mono-font, size: scale.body-sm, weight: "bold", fill: c)[#str(n)]
    ],
  )
}

// A bare numeral in the mono face, for pages that want an index without a box.
#let section-index(n, th, color: none) = {
  let c = if color == none { th.terracotta } else { color }
  text(str(n), font: th.mono-font, size: scale.meta, weight: "bold", fill: c, tracking: 0.6pt)
}

// ── Panels ──────────────────────────────────────────────────────────────────
// Panels own their padding. Nothing is placed inside one by absolute position.

#let tinted-panel(body, th, fill: none, edge: none, pad: 13pt, weight: 0.5pt, radius: 1.5pt) = {
  let f = panel-of(th, fill)
  let e = rule-of(th, edge)
  block(
    width: 100%,
    breakable: true,
    fill: f,
    stroke: weight + e,
    radius: radius,
    inset: pad,
  )[#body]
}

// A full-width dark panel, used only by page families that compose a dark
// background themselves -- never a drop-in for a light page.
#let dark-panel(body, th, fill: none, pad: 18pt) = {
  let f = ink-of(th, fill)
  block(width: 100%, breakable: true, fill: f, inset: pad)[
    #set text(fill: th.paper)
    #body
  ]
}

// A narrow coloured band marking the top edge of a feature frame.
#let title-band(title, th, fill: none, fg: none, pad: 7pt) = {
  let f = ink-of(th, fill)
  let c = if fg == none { th.paper } else { fg }
  block(
    width: 100%,
    fill: f,
    inset: (left: pad * 1.4, right: pad, top: pad * 0.8, bottom: pad * 0.8),
  )[
    #set align(left + horizon)
    #label(title, th, color: c)
  ]
}

// ── Result panel ────────────────────────────────────────────────────────────
// Where a worked example's answer lands. The one place a value is allowed to
// be large, because it is the point of the page.
#let result-panel(value, caption, th, fill: none, edge: none) = {
  let e = if edge == none { th.green } else { edge }
  tinted-panel(
    [
      #set par(justify: false, first-line-indent: 0em)
      #label(caption, th, color: e, size: scale.caption)
      #v(0.5em)
      #text(font: th.mono-font, size: scale.lead, weight: "bold", fill: th.ink)[#value]
    ],
    th,
    fill: fill,
    edge: e,
    pad: 14pt,
  )
}

// ── Input cells ─────────────────────────────────────────────────────────────
// A structured field for assumptions and figures. Numbers use the mono face so
// columns of them align.
#let input-cell(lbl, value, th, note: none) = block(
  width: 100%,
  fill: th.panel-bg,
  stroke: (top: 1.1pt + th.ink, rest: 0.4pt + th.rule),
  inset: (left: 8pt, right: 8pt, top: 6pt, bottom: 7pt),
)[
  #set par(justify: false, first-line-indent: 0em, spacing: 0.2em)
  #label(lbl, th, color: th.slate, size: scale.caption)
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
#let answer-area(rules, th, gap: 15pt, weight: 0.55pt) = block(
  width: 100%,
  breakable: false,
)[
  #for _ in range(rules) [
    #v(gap, weak: true)
    #rule(th, weight: weight)
  ]
]

// ── Checkbox row ────────────────────────────────────────────────────────────
// A drawn square, not a glyph, so it scales and takes the rule colour.
#let checkbox(th, side: 8.5pt, color: none) = block(
  width: side,
  height: side,
  stroke: 0.7pt + slate-of(th, color),
  radius: 0.6pt,
)

#let checkbox-item(t, th, number: none, warn: false, gap: 9pt) = {
  let marker = if number == none {
    checkbox(th, color: if warn { th.terracotta } else { none })
  } else {
    let c = if warn { th.terracotta } else { th.brass }
    text(font: th.mono-font, size: scale.body-sm, weight: "bold", fill: c)[#str(number) + "."]
  }
  let col = if number == none { 8.5pt } else { 13pt }
  block(width: 100%, breakable: true, below: 0.42em)[
    #set par(justify: false, first-line-indent: 0em, leading: th.lead)
    #grid(
      columns: (col, 1fr),
      gutter: gap,
      align: (top, top),
      marker,
      text(size: scale.body, fill: th.ink)[#t],
    )
  ]
}

// ── Pull quote ──────────────────────────────────────────────────────────────
// An oversized opening mark in the heading face. Only called for sentences the
// manuscript itself supports.
#let pull-quote(quote, th, attribution: none, size: 25pt) = block(width: 100%, breakable: true)[
  // `par.leading` takes a length, not a ratio: it is added to the font's em box.
  #let q-lead = size * 1.16
  #set par(justify: false, first-line-indent: 0em, leading: q-lead)
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
#let figure-caption(number, text, th, color: none) = block(
  width: 100%,
  breakable: true,
  above: 0.45em,
)[
  #set par(justify: true, first-line-indent: 0em, leading: scale.caption * 1.35)
  #grid(
    columns: (16mm, 1fr),
    gutter: 5pt,
    align: (left, left),
    label("Fig. " + str(number), th, color: color, size: scale.caption),
    caption(text, th),
  )
]

// ── Measurement helpers ─────────────────────────────────────────────────────
// Used by families that have to decide what fits before they compose.
#let line-count(body, th) = measure(block(width: 100%, body)).height / th.lead
#let page-break-point = 7mm
