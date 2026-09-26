// ============================================================================
//  content.typ — what a page holds, independent of how it is set
// ============================================================================
//
//  The accessors a page family needs to read its own page: the blocks, the
//  opener data, the figure, the heading, and the small shared components (a
//  numbered row, a dash row, a check row, a contour wash) that several
//  families use. Families differ in geometry; the way they *read* a page is
//  shared, and putting that here is what lets a new family be written without
//  re-deciding how to find its own content.
//
//  This module was extracted from page_families.typ so that families.typ can
//  use the same accessors. Both family sets can therefore coexist, and the old
//  sixteen remain the fallback until the new thirteen pass QA.
// ============================================================================

// `grid.typ` first: the shared components -- `panel`, `divider`, `label-text`,
// `dash-row` -- live there, and the block renderer below is built from them.
#import "grid.typ": *
#import "helpers.typ": *
#import "design_system.typ": *

// ── Shared page data ────────────────────────────────────────────────────────
// Flatten a payload that may arrive as a list of strings, a list of lists, or a
// dictionary keyed by group, into a flat list of strings. The renderer's recap
// and objective payloads have used all three shapes across revisions, and a page
// family should not have to know which one it was handed.
#let flatten-strings(value) = {
  let out = ()
  if type(value) == array {
    for v in value {
      if type(v) == array { out = out + flatten-strings(v) }
      else if type(v) == dictionary {
        for (_, item) in v { out = out + flatten-strings(item) }
      } else { out = out + (str(v),) }
    }
  } else if type(value) == dictionary {
    for (_, item) in value { out = out + flatten-strings(item) }
  } else if value != none {
    out = (str(value),)
  }
  out
}

// A clamping take. Typst's `array.slice` raises when the end index runs past
// the array, and a chapter with one objective must not fail the build.
#let first-n(seq, n) = seq.slice(0, calc.min(n, seq.len()))

#let blocks-of(pg) = pg.at("blocks", default: ())
#let opener-of(pg) = pg.at("chapter_opener_data", default: (:))
#let variant-of(pg) = int(pg.at("layout_variant", default: 0))
#let side-of(pg) = str(pg.at("illustration_side", default: "right"))
#let family-label(pg) = str(pg.at("family_label", default: ""))
// The book's topic vocabulary. A noun no page may hardcode.
#let term(pg, key, fallback) = str(pg.at("domain", default: (:)).at(key, default: fallback))
#let is-type(b, kinds) = str(b.at("type", default: "")) in kinds
// The text of a block. Accepts a bare string as well, because a few fields the
// renderer attaches -- `epigraph` among them -- carry text directly rather than
// as a content block, and a family should not have to know which it got.
#let text-of(b) = if type(b) == str { b } else { str(b.at("content", default: "")) }
#let no-content(b) = (type: "paragraph", content: "")

#let or-label(pg, fallback) = if family-label(pg) == "" { fallback } else { family-label(pg) }

// The figure a page owns: a plate the renderer attached, or an image_instruction
// block among the page's own blocks.
#let figure-of(pg) = {
  let direct = pg.at("illustration", default: none)
  if direct != none and str(direct.at("path", default: "")) != "" {
    return direct
  }
  let found = none
  for b in blocks-of(pg) {
    if is-type(b, ("image_instruction")) {
      let img = b.at("image", default: none)
      if img != none and str(img.at("path", default: "")) != "" { found = img }
    }
  }
  found
}

// The heading that opens a page, so a family can set it at display size rather
// than at whatever the global heading rule would choose.
#let lead-heading(blocks) = {
  let out = none
  for b in blocks {
    if out == none and is-type(b, ("heading")) { out = text-of(b).trim() }
  }
  out
}

#let without-head(blocks, head) = blocks.filter(
  b => not (is-type(b, ("heading")) and text-of(b).trim() == head))

// Body flow with the page's own paragraph rhythm. Every family that shows
// running text routes through here, so leading stays identical book-wide.
#let body-flow(blocks, th, size: none, justify: true) = {
  let s = if size == none { th.text-size } else { size }
  set text(size: s)
  set par(justify: justify, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
  render-blocks(blocks, th)
}

#let page-title(t, th, size: scale.display-sm, color: none) = block(
  width: 100%,
  breakable: true,
  below: 0.35em,
)[
  #set par(justify: false, first-line-indent: 0em, leading: size * 1.14)
  #dsp(t, th, size: size, color: color)
]

// A bounded pull from a block: standfirsts, sidebar facts, captions. Never a
// whole paragraph, and never the whole page.
#let first-sentence(b, limit: 200) = {
  let t = text-of(b).trim()
  if t.len() <= limit { return t }
  let cut = t.slice(0, limit)
  let sp = cut.last_indexOf(" ")
  (if sp == none { cut } else { cut.slice(0, sp) }) + "…"
}

#let list-items(blocks) = {
  let out = ()
  for b in blocks {
    if is-type(b, ("list", "list_item", "checklist")) {
      let src = b.at("list", default: (:)).at("items", default: ())
      if src.len() > 0 { out = out + src.map(s => str(s)) }
    }
  }
  out
}

// A numbered body row, used for objectives, calculation steps, lessons and
// references so those four read as one list style.
#let numbered-row(n, t, th, color: none, size: none) = {
  let s = if size == none { scale.body } else { size }
  let c = if color == none { th.brass } else { color }
  grid(
    columns: (9mm, 1fr),
    gutter: 4pt,
    align: (left, left),
    text(font: th.mono-font, size: scale.caption, weight: "bold", fill: c)[#str(n) + "."],
    text(size: s, fill: th.ink)[#t],
  )
}

#let dash-row(t, th, size: none, color: none) = {
  let s = if size == none { scale.body } else { size }
  let c = if color == none { th.brass } else { color }
  grid(
    columns: (5mm, 1fr),
    gutter: 3pt,
    align: (left, left),
    text(size: s, fill: c)[—],
    text(size: s, fill: th.ink)[#t],
  )
}

// A generated contour wash for the visual region of a split page with no plate
// of its own. Vector only, and drawn from the grid rather than borrowed.
#let contour-motif(th, rows: 7, cols: 9) = {
  // The wash reads as ink on paper, or as paper on ink. Which one depends on
  // the page it sits on, so the tone is resolved from the theme rather than
  // fixed here.
  let tone = th.at("cream-deep", default: th.paper-warm)
  grid(
  columns: range(cols).map(_ => 1fr),
  row-gutter: 0pt,
  column-gutter: 0pt,
  // `range(n).map(...)` over a flat index: Typst has no flatMap, and the motif
  // is a plain grid of cells whose on/off state follows a radial falloff.
  ..range(rows * cols).map(k => {
    let r = calc.floor(k / cols)
    let c = calc.rem(k, cols)
    let half = (cols - 1) / 2
    let falloff = 1 - calc.abs(c - half) / half
    let on = calc.rem(r + c * 2, 5) < 3 and falloff > 0.18
    block(
      width: 100%,
      height: 4.2mm,
      fill: if on { tone } else { th.at("paper", default: th.paper-warm) },
    )
  }),
  )
}

// A hairline column rule.
//
// It is a right border on the column itself, not a block of `height: 100%`.
// A percentage height needs a definite containing height, and inside a grid row
// that is still being measured there is none -- Typst resolved it to the whole
// page and pushed the rest of the composition onto a second sheet. A border is
// always exactly as tall as the content it belongs to, which is also the only
// version that can never land on top of a line of text.
#let ruled-column(body, th, inset: 4mm) = block(
  width: 100%,
  stroke: (right: 0.4pt + th.rule),
  inset: (right: inset),
)[#body]

// A checked item: a hairline box and the text beside it. The box is drawn, not
// a glyph, so it is exactly one cap-height at every size and does not depend on
// a font that may not be installed.
#let check-row(t, th, size: none, color: none) = {
  let s = if size == none { th.text-size } else { size }
  let c = if color == none { th.brass } else { color }
  grid(
    columns: (4.6mm, 1fr),
    column-gutter: 2.6mm,
    align: (left, left),
    block(
      width: 3.4mm,
      height: 3.4mm,
      stroke: 0.5pt + c,
      radius: 0pt,
      inset: 0pt,
    ),
    text(size: s, fill: th.ink)[#t],
  )
}


// The pull quote a page owns, taken from a quote block among its own blocks or
// from the data the renderer attached. Returns an empty dictionary rather than
// none so a caller can read fields without a guard at every use.
#let quote-of(pg) = {
  let direct = pg.at("quote_data", default: none)
  if direct != none { return direct }
  let found = (:)
  for b in blocks-of(pg) {
    if is-type(b, ("quote", "pull_quote", "feature_quote")) {
      found = b.at("quote", default: b.at("pull_quote", default: (:)))
    }
  }
  found
}

// ── Flowing blocks on the grid ──────────────────────────────────────────────
// The grid's own block renderer. `helpers.typ` has one too, but it is bound to
// the design_system theme and draws that system's callout cards, tinted sidebars
// and framed panels; running it with the grid theme raised a missing-key error
// on the first callout, and would have produced a book of two design languages if
// it had not. Every block type is rendered here with grid primitives, so a page
// composed on the grid is typeset entirely from the grid.
//
// The specialised blocks -- an exercise, a worked example, a case, a process
// diagram, a table -- are not rendered here. They are the whole subject of their
// own family, and a family that is going to set one must place it; rendering a
// summary of it into the running text as well would set it twice.
#let heading-block(raw, T) = block(
  width: 100%,
  breakable: false,
  above: T.space-before-head,
  below: T.space-after-head,
)[#section-heading-element(raw, T, size: T.h3-size)]

#let list-block(b, T) = {
  let items = b.at("list", default: (:)).at("items", default: ())
  if items.len() == 0 and text-of(b).trim() != "" { items = (text-of(b),) }
  for (i, item) in items.enumerate() [
    #numbered-row(i + 1, str(item), T, size: T.text-size)
    #v(T.space-tight)
  ]
}

#let checklist-block(b, T) = {
  for item in b.at("checklist", default: (:)).at("items", default: ()) [
    #check-row(str(item), T)
    #v(T.space-tight)
  ]
}

#let definition-block(b, T) = block(width: 100%, breakable: false)[
  #set par(justify: true, first-line-indent: 0em, leading: T.lead)
  #text(font: T.heading-font, size: T.text-size, weight: "semibold", fill: T.ink)[
    #text-of(b.at("definition", default: b))
  ]
  #v(0.15em)
  #text(size: T.small-size, fill: T.slate)[#text-of(b.at("body", default: (:)))]
]

#let quotation-block(b, T) = block(width: 100%, breakable: false)[
  #set par(justify: true, first-line-indent: 0em, leading: T.lead * 1.15)
  #text(font: T.body-font, size: T.lead, style: "italic", fill: T.ink)[#text-of(b)]
]

#let callout-block(b, T) = {
  let c = b.at("callout", default: (:))
  // Not named `text`: a local binding of that name shadows Typst's `text()`
  // function for the rest of the block, and `text(...)` below would then be a
  // call on a string.
  let body = str(c.at("text", default: text-of(b)))
  let label = str(c.at("label", default: "Note"))
  if body.trim() != "" [
    #panel([
      #label-text(label, fill: T.terracotta, size: T.micro-size)
      #v(0.2em)
      #text(size: T.small-size, fill: T.ink)[#body]
    ], T)
    #v(T.space-block)
  ]
}

#let code-block(b, T) = block(
  width: 100%,
  breakable: true,
  fill: T.slate-tint,
  stroke: (left: 1.1pt + T.slate),
  inset: (left: 8pt, right: 6pt, top: 5pt, bottom: 5pt),
  radius: 0pt,
)[
  #set par(justify: false, first-line-indent: 0em, leading: T.lead)
  #raw(block: true, lang: none, text-of(b))
]

#let footnote-block(b, T) = block(width: 100%, breakable: false)[
  #set par(justify: true, first-line-indent: 0em, leading: 1.32em)
  #text(font: T.heading-font, size: T.caption-size, fill: T.slate)[#text-of(b)]
]

#let reference-block(b, T) = block(width: 100%, breakable: false)[
  #set par(justify: true, first-line-indent: 0em, leading: 1.32em)
  #text(size: T.small-size, fill: T.ink)[#text-of(b)]
]

// Flow a block list into the page with the book's paragraph rhythm. This is the
// single entry point for running text: a family that wants running prose calls
// this, so leading, justification and paragraph spacing are book-wide by
// construction rather than by convention.
#let render-blocks-grid(blocks, T) = {
  for b in blocks {
    let kind = str(b.at("type", default: "paragraph"))
    let raw = text-of(b)
    if kind == "heading" {
      heading-block(raw, T)
    } else if kind in ("paragraph", "unknown") {
      if raw.trim() != "" { block(width: 100%)[#raw] }
    } else if kind in ("list", "list_item") {
      list-block(b, T)
    } else if kind == "checklist" {
      checklist-block(b, T)
    } else if kind == "definition" {
      definition-block(b, T)
    } else if kind == "quotation" {
      quotation-block(b, T)
    } else if kind == "callout" {
      callout-block(b, T)
    } else if kind == "code" {
      code-block(b, T)
    } else if kind == "footnote" {
      footnote-block(b, T)
    } else if kind == "reference" {
      reference-block(b, T)
    } else if kind in ("table", "exercise", "worked_example", "case_study", "process_diagram", "image_instruction") {
      none
    } else if kind in ("page_break", "section_break") {
      none
    } else if raw.trim() != "" {
      block(width: 100%)[#raw]
    }
  }
}

#let flow-blocks(blocks, T, size: none, justify: true, lead-drop-cap: false) = {
  let s = if size == none { T.text-size } else { size }
  set text(size: s)
  set par(justify: justify, first-line-indent: 0em, spacing: T.par-space, leading: T.lead)
  render-blocks-grid(blocks, T)
}
