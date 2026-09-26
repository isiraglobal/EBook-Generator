// ============================================================================
//  Editorial page design families
// ----------------------------------------------------------------------------
//  Sixteen composed page geometries, one function each. The governing rule is
//  that a family owns a *layout*, not just a set of sizes: each reserves
//  different regions, so adjacent pages read as different objects while sharing
//  the scale, palette and type system from design_system.typ.
//
//  These families are topic-agnostic. Nothing here names a subject: every noun
//  a page needs comes from `pg.domain`, which typst_renderer fills from the
//  publication brief's `domain_*` keys and otherwise leaves at neutral
//  defaults. The same sixteen geometries typeset a manual, a course, a report
//  or a workbook without a template being edited.
//
//  Two disciplines keep this file parseable, and both are load-bearing:
//
//  * Inside a content block `[...]` every statement carries a `#`. Inside a
//    function body `{...}` nothing does. A `#if` written in markup opens a
//    bracket block `[...]`, never a brace block: a brace block is code mode,
//    and markup written inside one is a parse error.
//  * A family owns a *layout*, not just a set of sizes. Regions that must not
//    break — frames, input tables, result panels — hold bounded content; the
//    surrounding column flows normally and nothing is placed in a fixed-height
//    box that long prose could overflow.
//
//  Contract with typst_renderer.py:
//
//  * FAMILY_GEOMETRY in the renderer records how much text each family can
//    hold. A family is only assigned to a page whose measured weight fits it.
//  * `pg.layout_variant` (int) and `pg.illustration_side` ("left" | "right")
//    drive the alternation rules.
// ============================================================================

#import "helpers.typ": *
#import "design_system.typ": *

#import "content.typ": *



// ============================================================================
//  A · MINIMAL EDITORIAL PAGE
//  A narrow measure against a wide right margin. The page is mostly air; the
//  heading and one idea are the whole composition.
// ============================================================================
#let layout-minimal-editorial(pg, doc, th) = {
  set page(margin: (top: 40mm, bottom: 28mm, left: 32mm, right: 46mm), fill: th.paper)
  let blocks = blocks-of(pg).filter(b => not is-type(b, ("image_instruction")))
  let head = lead-heading(blocks)
  let rest = without-head(blocks, head)
  block(width: 100%)[
    #set par(justify: false, first-line-indent: 0em, leading: th.lead)
    #label(or-label(pg, "Field note"), th, color: th.terracotta)
    #v(0.75em)
    #accent-rule(th, accent: 18mm)
    #v(1.1em)
    #if head != none [
      #page-title(head, th, size: scale.display-sm)
      #v(0.3em)
    ]
    #block(width: 100% - 6mm)[#body-flow(rest, th, justify: false)]
  ]
}


// ============================================================================
//  B · OVERSIZED CHAPTER OPENER — four compositions
//  The variant is chosen by chapter position, so no two consecutive openers
//  arrange their numeral and title the same way.
// ============================================================================

#let opener-epigraph(co, th) = {
  let e = str(co.at("epigraph", default: "")).trim()
  if e == "" { return none }
  block(width: 100%, breakable: false)[
    #set par(justify: false, first-line-indent: 0em, leading: scale.lead * 1.35)
    #lead(e, th, color: th.slate)
  ]
}

#let opener-objectives(objectives, th) = block(width: 100%, breakable: false)[
  #set par(justify: false, first-line-indent: 0em, leading: scale.body * 1.45)
  #rule(th, weight: 0.4pt)
  #v(0.7em)
  #label("In this chapter", th, color: th.terracotta, size: scale.caption)
  #v(0.65em)
  #for o in objectives [
    #dash-row(o, th, size: scale.body - 0.5pt)
    #v(0.2em)
  ]
]

#let opener-numeral(num, th, size: none, color: none, leading: none) = {
  let s = if size == none { scale.giant } else { size }
  // At 0.82x the numeral's glyph box overlapped the title's ascenders;
  // a display size needs a line box at least as tall as the face.
  let ld = if leading == none { s * 1.02 } else { leading }
  let c = if color == none { th.cream-deep } else { color }
  block(width: 100%, breakable: false)[
    #set par(justify: false, first-line-indent: 0em, leading: ld)
    #text(font: th.heading-font, size: s, weight: "bold", fill: c, tracking: -3pt)[#num]
  ]
}

// A chapter title, registered as a real level-1 heading so the contents page
// and the PDF bookmarks are built from the book rather than from a hand-kept
// list. The heading element itself adds no geometry; the family still owns the
// size, leading and tracking.
#let opener-title(title, th, size: none) = {
  let s = if size == none { scale.display } else { size }
  block(width: 100%, breakable: false)[
    #set par(justify: false, first-line-indent: 0em, leading: s * 1.08)
    #heading(level: 1)[#dsp(title, th, size: s)]
  ]
}

#let opener-sections(sections, th) = block(width: 100%, breakable: false)[
  #set par(justify: false, first-line-indent: 0em, leading: scale.body-sm * 1.5)
  #for s in sections [
    #text(size: scale.body-sm, fill: th.slate)[#str(s)]
    #v(0.25em)
  ]
]

// B1 — numeral left, title right.
#let layout-opener-split(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 24mm, left: 28mm, right: 28mm), fill: th.paper)
  let co = opener-of(pg)
  let num = str(co.at("chapter_number", default: ""))
  let objectives = first-n(co.at("learning_objectives", default: ()).map(s => str(s)), 3)
  let plate = figure-of(pg)
  [
    #set par(justify: false, first-line-indent: 0em, leading: th.lead)
    #grid(
      columns: (34mm, 1fr),
      column-gutter: 12mm,
      align: (left, left),
      block(width: 100%, breakable: false)[
        #label("Chapter", th, color: th.terracotta)
        #v(0.5em)
        #opener-numeral(num, th, size: scale.giant)
        #v(-0.2em)
        #side-rule(th, weight: 2.2pt, color: th.brass, length: 18mm)
      ],
      block(width: 100%, breakable: false)[
        #opener-title(str(co.at("chapter_title", default: "")), th)
        #v(1em)
        #let epi = opener-epigraph(co, th)
        #if epi != none [
          #epi
          #v(0.7em)
        ]
        #if objectives.len() > 0 [#opener-objectives(objectives, th)]
      ],
    )
    #if plate != none [#figure-block(plate, th, height: 46mm, tail: 0pt)]
  ]
}

// B2 — title across the upper half, numeral sitting in the field beside it.
//
// The title's measure stops short of the numeral. Run to the full measure it
// passed straight under the giant figure, and the two printed on top of one
// another: on three chapter openers the first line of the title crossed the
// numeral's strokes, which reads as a collision rather than as a watermark.
#let STACKED_NUMERAL_BAND = 34mm

#let layout-opener-stacked(pg, doc, th) = {
  set page(margin: (top: 28mm, bottom: 24mm, left: 30mm, right: 30mm), fill: th.paper)
  let co = opener-of(pg)
  let num = str(co.at("chapter_number", default: ""))
  let objectives = first-n(co.at("learning_objectives", default: ()).map(s => str(s)), 3)
  let plate = figure-of(pg)
  [
    #set par(justify: false, first-line-indent: 0em, leading: th.lead)
    #block(width: 100%, breakable: false, above: -6mm)[
      #set par(justify: false, first-line-indent: 0em, leading: 96pt)
      #align(right)[
        #text(
          font: th.heading-font,
          size: scale.giant,
          weight: "bold",
          fill: th.cream-deep,
          tracking: -3pt,
        )[#num]
      ]
    ]
    #block(width: 100% - STACKED_NUMERAL_BAND)[
      #opener-title(str(co.at("chapter_title", default: "")), th)
    ]
    #v(0.9em)
    #rule(th, weight: 1.6pt, color: th.brass, width: 34mm)
    #v(1.1em)
    #block(width: 100%, breakable: false)[
      #let epi = opener-epigraph(co, th)
      #if epi != none [
        #epi
        #v(0.6em)
      ]
      #if objectives.len() > 0 [#opener-objectives(objectives, th)]
    ]
    #if plate != none [#figure-block(plate, th, height: 44mm, tail: 0pt)]
  ]
}

// B3 — vertical chapter label beside an oversized numeral and a full-measure
// title.
#let layout-opener-vertical(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 24mm, left: 30mm, right: 30mm), fill: th.paper)
  let co = opener-of(pg)
  let num = str(co.at("chapter_number", default: ""))
  let objectives = first-n(co.at("learning_objectives", default: ()).map(s => str(s)), 3)
  let plate = figure-of(pg)
  [
    #set par(justify: false, first-line-indent: 0em, leading: th.lead)
    #block(width: 100%, breakable: false, above: -4mm)[
      #grid(
        columns: (9mm, 1fr),
        column-gutter: 9mm,
        align: (left, left),
        // A vertical label needs its own box: stacked characters cannot take
        // part in a par line, so this one region is deliberately out of flow.
        box(
          width: 9mm,
          align(center + top)[
            #set par(justify: false, first-line-indent: 0em, leading: 3.4pt)
            #text(
              font: th.heading-font,
              size: scale.meta,
              weight: "bold",
              fill: th.terracotta,
              tracking: 2.2pt,
            )[
              #for ch in upper("Chapter " + num) [
                #ch
                \\
              ]
            ]
          ],
        ),
        block(width: 100%, breakable: false)[
          #opener-numeral(num, th, size: scale.giant-sm, color: th.brass, leading: 1.32 * scale.giant-sm)
          #v(0.4em)
          #opener-title(str(co.at("chapter_title", default: "")), th)
          #v(0.9em)
          #accent-rule(th, accent: 26mm)
        ],
      )
    ]
    #v(1.3em)
    #grid(
      columns: (1fr, 44mm),
      column-gutter: 12mm,
      align: (left, left),
      block(width: 100%, breakable: false)[
        #let epi = opener-epigraph(co, th)
        #if epi != none [
          #epi
          #v(0.6em)
        ]
        #if objectives.len() > 0 [#opener-objectives(objectives, th)]
      ],
      if plate != none { figure-block(plate, th, height: 50mm, tail: 0pt) } else { block(width: 100%, breakable: false)[] },
    )
  ]
}

// B4 — centred, rule-driven, plate beneath. The quietest of the four.
#let layout-opener-centered(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 26mm, left: 32mm, right: 32mm), fill: th.paper)
  let co = opener-of(pg)
  let num = str(co.at("chapter_number", default: ""))
  let objectives = first-n(co.at("learning_objectives", default: ()).map(s => str(s)), 3)
  let plate = figure-of(pg)
  [
    #set par(justify: false, first-line-indent: 0em, leading: th.lead)
    #block(width: 100%, breakable: false)[
      #align(center)[
        #label("Chapter " + num, th, color: th.terracotta)
        #v(0.9em)
        #block(width: 116mm)[
          #set par(justify: false, first-line-indent: 0em, leading: scale.display * 1.1)
          #align(center)[#heading(level: 1)[#dsp(str(co.at("chapter_title", default: "")), th, size: scale.display)]]
        ]
        #v(1.1em)
        #side-rule(th, weight: 1.6pt, color: th.brass, length: 26mm)
        #v(1.1em)
        #let epi = opener-epigraph(co, th)
        #if epi != none [
          #block(width: 92mm)[
            #set par(justify: false, first-line-indent: 0em, leading: scale.lead * 1.4)
            #align(center)[#lead(epi, th, color: th.slate)]
          ]
        ]
      ]
    ]
    #v(1.4em)
    #if objectives.len() > 0 [
      #block(width: 112mm, breakable: false)[#opener-objectives(objectives, th)]
    ]
    #if plate != none [#figure-block(plate, th, height: 24mm, tail: 0pt)]
  ]
}


// ============================================================================
//  C · DARK FEATURE OPENER
//  Full-bleed ink. The book's running head is switched off for this page and a
//  light footer drawn locally, because brass-on-paper chrome disappears against
//  ink. Two internal arrangements, so three dark openers are not identical.
// ============================================================================
#let layout-dark-feature-opener(pg, doc, th) = {
  // The book's global footer is drawn in slate and brass, which vanish against
  // ink, so this page supplies its own -- in the page's footer region, not in
  // the flow. Drawn in the flow it landed wherever the opener's content ended,
  // which on a sparse opener is the middle of the sheet: three chapters opened
  // with their folio floating at the waist.
  set page(
    margin: (top: 28mm, bottom: 22mm, left: 28mm, right: 28mm),
    fill: th.ink,
    header: none,
    footer: context {
      let n = text(counter(page).display("1"), font: th.heading-font,
                   size: scale.meta, weight: "bold", fill: th.brass, tracking: 0.9pt)
      set text(font: th.heading-font, size: scale.meta, fill: th.dark-note, tracking: 1.4pt)
      box(width: 100%)[
        #set par(justify: false, first-line-indent: 0em)
        #line(length: 100%, stroke: 0.4pt + rgb("#4A423A"))
        #v(0.5em)
        #grid(columns: (1fr, auto), [#upper(str(doc.at("title", default: "")))], n)
      ]
    },
  )
  let co = opener-of(pg)
  let num = str(co.at("chapter_number", default: ""))
  let title = str(co.at("chapter_title", default: ""))
  let objectives = first-n(co.at("learning_objectives", default: ()).map(s => str(s)), 3)
  let plate = figure-of(pg)
  let hair = rgb("#4A423A")
  let split = calc.rem(variant-of(pg), 2) == 0
  [
    #set par(justify: false, first-line-indent: 0em, leading: th.lead)
    #set text(fill: th.paper)
    #label("Chapter " + num, th, color: th.brass)
    #v(0.8em)
    #rule(th, weight: 1.4pt, color: th.brass, width: 22mm)
    #v(1.4em)
    #if split [
      #grid(
        columns: (1fr, 52mm),
        column-gutter: 10mm,
        align: (left, left),
        block(width: 100%, breakable: false)[
          #set par(justify: false, first-line-indent: 0em, leading: scale.display * 1.08)
          #dsp(title, th, size: scale.display, color: th.paper)
          #v(0.9em)
          #block(width: 100%, breakable: false)[
            #set par(justify: false, first-line-indent: 0em, leading: scale.lead * 1.38)
            #text(font: th.body-font, size: scale.lead, fill: th.dark-note)[
              #upper(first-sentence(no-content(co.at("epigraph", default: ""))))
            ]
          ]
          #v(0.9em)
          #block(width: 100%, breakable: false)[
            #set par(justify: false, first-line-indent: 0em, leading: scale.body * 1.45)
            #for o in objectives [
              #dash-row(o, th, size: scale.body - 0.5pt, color: th.brass)
              #v(0.18em)
            ]
          ]
        ],
        opener-numeral(num, th, size: scale.giant-sm, color: th.terracotta, leading: 1.32 * scale.giant-sm),
      )
    ] else [
      #opener-numeral(num, th, size: scale.giant-sm, color: th.terracotta,
        leading: 1.32 * scale.giant-sm)
      // Explicit clearance, not leading: par(leading:) spaces baselines, and a
      // single-line paragraph's box does not grow the way the numeral's glyph
      // box does. The chapter title's first line was crossing the numeral's
      // descender by nine points.
      #v(1.1em)
      #block(width: 100%, breakable: false)[
        #set par(justify: false, first-line-indent: 0em, leading: scale.display * 1.08)
        #dsp(title, th, size: scale.display, color: th.paper)
      ]
      #v(0.8em)
      #rule(th, weight: 0.4pt, color: hair, width: 60%)
      #v(1.2em)
      #block(width: 100%, breakable: false)[
        #set par(justify: false, first-line-indent: 0em, leading: scale.body * 1.5)
        #columns(2, gutter: 8mm)[
          #for o in objectives [
            #dash-row(o, th, size: scale.body - 0.5pt, color: th.brass)
            #v(0.3em)
          ]
        ]
      ]
    ]
    // The motif is placed, not flowed. A full-bleed ink page has no vertical
    // room to spend on a figure block, and the brief's allowance for fixed
    // positioning is exactly this case: a short bounded decorative element on
    // a deliberately composed page. It occupies the lower margin band, so no
    // type is ever under it.
    #if plate != none [
      #place(bottom + right, dx: -22mm, dy: 6mm, contour-motif(th, rows: 3, cols: 14))
    ]
  ]
}


// ============================================================================
//  D · ASYMMETRIC MAGAZINE GRID
//  A 70/26 split with a visible gutter. The sidebar is a reserved column, so no
//  line of main text can ever run under it.
// ============================================================================
#let sidebar-entry(b, th) = {
  if is-type(b, ("image_instruction")) {
    block(width: 100%, breakable: false)[
      #figure-block(b.at("image", default: (:)), th, height: 96mm)
      #v(0.9em)
    ]
  } else if is-type(b, ("definition")) {
    block(width: 100%, breakable: false)[
      #set par(justify: false, first-line-indent: 0em, leading: scale.body-sm * 1.5)
      #dsp(str(b.at("definition", default: (:)).at("term", default: "")), th, size: scale.body)
      #v(0.15em)
      #text(size: scale.body-sm, fill: th.ink)[#text-of(b)]
      #v(0.85em)
    ]
  } else {
    // A callout loses its own box here: the rule and label already separate
    // it, and a boxed panel in a 42mm column reads as noise.
    block(width: 100%, breakable: false)[
      #set par(justify: false, first-line-indent: 0em, leading: scale.body-sm * 1.5)
      #label(
        str(b.at("callout", default: (:)).at("kind", default: "Note")),
        th,
        color: th.brass,
        size: scale.caption,
      )
      #v(0.3em)
      #text(size: scale.body-sm, fill: th.ink)[#str(b.at("callout", default: (:)).at("text", default: ""))]
      #v(0.85em)
    ]
  }
}

#let layout-asymmetric-grid(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 26mm, left: 28mm, right: 24mm), fill: th.paper)
  let blocks = blocks-of(pg)
  let plate = figure-of(pg)
  // The sidebar draws on the page's short, bounded material; everything else
  // flows in the main column.
  let is-side = b => is-type(b, ("definition", "callout", "image_instruction"))
  let side = blocks.filter(is-side)
  let main = blocks.filter(b => not is-side(b))
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #grid(
      columns: (1fr, 7mm, 42mm),
      align: (left, left, left),
      ruled-column([#body-flow(main, th)], th),
      block(width: 100%)[],
      block(width: 100%)[
        #set par(justify: false, first-line-indent: 0em, leading: scale.body-sm * 1.5)
        #label("Reference", th, color: th.terracotta, size: scale.caption)
        #v(0.7em)
        #rule(th, weight: 0.8pt, color: th.brass, width: 14mm)
        #v(0.8em)
        #if side.len() > 0 [
          #for b in side [#sidebar-entry(b, th)]
        ] else if plate != none [
          #figure-block(plate, th, height: 150mm)
        ]
      ],
    )
  ]
}


// ============================================================================
//  E · TEXT AND VISUAL SPLIT
//  62/38, alternating sides. `pg.illustration_side` decides which region holds
//  the image, so a run of illustrated pages never repeats the same edge.
// ============================================================================

// The visual column of a split page. The plate is capped to a share of the
// text height: uncapped, the artwork scales to the column width and its own
// aspect ratio, and on a tall plate that makes the grid row longer than the
// page. Typst then breaks the row and carries the text column's tail -- a
// two-line orphan -- onto a sheet of its own, which is how a case study landed
// as a full page plus a scrap.
#let SPLIT_VISUAL_HEIGHT = 132mm

#let split-visual(plate, th, pg, doc) = {
  if plate != none {
    figure-block(plate, th, height: SPLIT_VISUAL_HEIGHT)
  } else {
    // The region still has to be composed, or the spread reads half-empty. A
    // contour wash plus a caption states it without inventing content.
    block(width: 100%, height: 62mm, fill: th.panel-bg, radius: 2pt)[
      #block(width: 100%, height: 100%, stroke: 0.4pt + th.rule, radius: 2pt, inset: 0pt)[
        #place(top + right, dy: -7mm, dx: 7mm, contour-motif(th))
      ]
    ]
    v(0.7em)
    // The caption names the book's own subject, so the region reads as part of
    // the argument rather than as a stock illustration.
    caption(
      term(pg, "figure_note", "Read the boundaries of the problem before the "
        + term(pg, "unit", "item") + " itself. Structure, access and dependency "
        + "decide what any " + term(pg, "unit", "item") + " can be used for, and "
        + "they are recorded before the price is."),
      th,
    )
  }
}

#let layout-text-visual-split(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 26mm, left: 28mm, right: 24mm), fill: th.paper)
  let blocks = blocks-of(pg).filter(b => not is-type(b, ("image_instruction")))
  let plate = figure-of(pg)
  let main = block(width: 100%)[#body-flow(blocks, th)]
  let visual = block(width: 100%)[#split-visual(plate, th, pg, doc)]
  let visual-first = side-of(pg) == "left"
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #grid(
      columns: (1fr, 9mm, 0.62fr),
      align: (left, left, left),
      if visual-first { visual } else { ruled-column(main, th) },
      block(width: 100%)[],
      if visual-first { main } else { visual },
    )
  ]
}


// ============================================================================
//  F · FRAMED EDITORIAL FEATURE
//  One inset frame with corner brackets and a header band, for a highlighted
//  concept. Not a frame around ordinary prose.
// ============================================================================
#let layout-framed-feature(pg, doc, th) = {
  set page(margin: (top: 32mm, bottom: 28mm, left: 28mm, right: 26mm), fill: th.paper)
  let blocks = blocks-of(pg).filter(b => not is-type(b, ("image_instruction")))
  let head = lead-heading(blocks)
  let rest = without-head(blocks, head)
  let plate = figure-of(pg)
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #title-band(or-label(pg, "Framework"), th, fill: th.ink)
    #v(4mm)
    #block(width: 100%, breakable: false)[
      #block(
        width: 100%,
        breakable: false,
        inset: (left: 11mm, right: 9mm, top: 7mm, bottom: 8mm),
      )[
        #set par(justify: false, first-line-indent: 0em, leading: th.lead)
        #corner-brackets(th, size: 11pt, weight: 0.9pt)
        #v(7pt)
        #if head != none [
          #page-title(head, th, size: scale.section)
          #v(0.4em)
          #rule(th, weight: 1.2pt, color: th.terracotta, width: 24mm)
          #v(0.7em)
        ]
        #body-flow(rest, th)
      ]
    ]
    #v(6mm)
    #if plate != none [#block(width: 100%)[#figure-block(plate, th, height: 128mm)]]
  ]
}


// ============================================================================
//  G · FULL-WIDTH FEATURE PAGE
//  A large title across the top, one dominant element beneath, and support text
//  held in a narrower measure at the foot. Landscape when the content is
//  genuinely wide and the renderer says so.
// ============================================================================
#let layout-full-width-feature(pg, doc, th) = {
  // The sheet size is the plan's to set, at the break in book_pages.typ, so the
  // family only chooses the margins that suit a wide measure.
  if str(pg.at("orientation", default: "portrait")) == "landscape" {
    set page(
      margin: (top: 24mm, bottom: 20mm, left: 26mm, right: 24mm),
      fill: th.paper,
    )
  } else {
    set page(margin: (top: 30mm, bottom: 26mm, left: 28mm, right: 24mm), fill: th.paper)
  }
  let blocks = blocks-of(pg)
  let plate = figure-of(pg)
  let head = lead-heading(blocks)
  let is-fig = b => is-type(b, ("image_instruction"))
  let is-steps = b => is-type(b, ("process_diagram", "list", "list_item"))
  let is-tbl = b => is-type(b, ("table"))
  let rest = without-head(blocks, head)
  // One dominant element: the figure if there is one, otherwise the table,
  // otherwise the step diagram. Everything else is support.
  let dom = rest.filter(is-fig)
  if dom.len() == 0 { dom = rest.filter(is-tbl) }
  if dom.len() == 0 { dom = rest.filter(is-steps) }
  let support = rest.filter(b => not (is-fig(b) or is-steps(b) or is-tbl(b)))
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #label(or-label(pg, "Overview"), th, color: th.terracotta)
    #v(0.7em)
    #page-title(head, th, size: scale.section + 3pt)
    #v(0.35em)
    #accent-rule(th, accent: 26mm)
    #v(0.8em)
    #if dom.len() > 0 [
      #block(width: 100%)[#render-blocks(dom, th)]
      #v(1em)
    ]
    #block(width: 100% - 26mm)[#body-flow(support, th)]
  ]
}


// ============================================================================
//  H · CASE-STUDY EDITORIAL PAGE
//  Scenario, analysis and decision in named regions; the takeaway gets an inset
//  panel. The prose is never shrunk to make it fit.
// ============================================================================
#let layout-case-study-editorial(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 26mm, left: 28mm, right: 26mm), fill: th.paper)
  let blocks = blocks-of(pg).filter(b => not is-type(b, ("image_instruction")))
  let studies = blocks.filter(b => is-type(b, ("case_study")))
  let others = blocks.filter(b => not is-type(b, ("case_study")))
  let meta = if studies.len() > 0 { studies.at(0).at("case_study", default: (:)) } else { (:) }
  let lead = if studies.len() > 0 { str(meta.at("title", default: "")) } else { lead-heading(blocks) }
  let scenario = if studies.len() > 0 { str(meta.at("context", default: "")) } else { "" }
  let tail = without-head(others, lead)
  // The takeaway holds the page's final short paragraph — the part a reader
  // acts on — and repeats nothing the body already says.
  let paras = tail.filter(b => is-type(b, ("paragraph")))
  let take = if paras.len() > 0 { paras.last() } else { none }
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #label("Case study", th, color: th.terracotta)
    #v(0.65em)
    #if lead != "" [
      #page-title(lead, th, size: scale.display-sm)
      #v(0.3em)
    ]
    #v(0.15em)
    #rule(th, weight: 1.4pt, color: th.terracotta, width: 28mm)
    #v(0.85em)
    #if scenario != "" [
      #block(width: 100%, breakable: true)[
        #set par(justify: true, first-line-indent: 0em, leading: scale.lead * 1.34)
        #text(font: th.body-font, size: scale.lead, fill: th.ink)[#scenario]
      ]
      #v(0.8em)
    ]
    #block(width: 100%)[#body-flow(tail, th)]
    #v(1em)
    #if take != none [
      #tinted-panel(
        [
          #set par(justify: true, first-line-indent: 0em, leading: th.lead)
          #label("What to carry forward", th, color: th.terracotta, size: scale.caption)
          #v(0.5em)
          #text(size: scale.body)[#text-of(take)]
        ],
        th,
        fill: th.warn-bg,
        edge: th.terracotta,
        pad: 12pt,
      )
    ]
  ]
}


// ============================================================================
//  I · WORKED-EXAMPLE PAGE
//  Inputs, calculation and outcome each get a region, and the outcome gets a
//  result panel labelled as illustrative arithmetic rather than a transaction.
// ============================================================================
#let layout-worked-example-page(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 26mm, left: 28mm, right: 26mm), fill: th.paper)
  let blocks = blocks-of(pg).filter(b => not is-type(b, ("image_instruction")))
  let exs = blocks.filter(b => is-type(b, ("worked_example")))
  let ex = if exs.len() > 0 { exs.at(0).at("worked_example", default: (:)) } else { (:) }
  let others = blocks.filter(b => not is-type(b, ("worked_example")))
  let idx = int(pg.at("example_index", default: 1))
  let given = ex.at("given", default: ())
  let steps = ex.at("steps", default: ())
  let answer = str(ex.at("answer", default: "")).trim()
  let problem = str(ex.at("problem", default: "")).trim()
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #grid(
      columns: (24mm, 1fr),
      column-gutter: 8mm,
      align: (left, left),
      block(width: 100%, breakable: false)[
        #set par(justify: false, first-line-indent: 0em, leading: 30pt)
        #text(
          font: th.mono-font,
          size: scale.display-sm,
          weight: "bold",
          fill: th.cream-deep,
        )[#str(idx)]
        #v(0.2em)
        #side-rule(th, weight: 1.8pt, color: th.brass, length: 16mm)
      ],
      block(width: 100%, breakable: false)[
        #label("Worked example", th, color: th.terracotta)
        #v(0.55em)
        #let et = str(ex.at("title", default: "")).trim()
        #if et != "" [
          #page-title(et, th, size: scale.section)
          #v(0.25em)
        ]
        #rule(th, weight: 0.8pt, color: th.brass, width: 22mm)
        #v(0.75em)
        #if problem != "" [
          #block(width: 100%, breakable: true)[
            #body-flow(([type: "paragraph", content: problem],), th)
          ]
          #v(0.8em)
        ]
      ],
    )
    #v(0.9em)
    #if given.len() > 0 [
      #block(width: 100%, breakable: true)[
        #label("Inputs and assumptions", th, color: th.slate, size: scale.caption)
        #v(0.55em)
        #grid(
          columns: range(calc.min(3, given.len())).map(_ => 1fr),
          gutter: 4mm,
          ..given.map(g => input-cell(
            if type(g) == array { str(g.at(0, default: "Input")) } else { "Input" },
            if type(g) == array { str(g.at(1, default: "")) } else { str(g) },
            th,
          )),
        )
        #v(0.9em)
      ]
    ]
    #if steps.len() > 0 [
      #block(width: 100%, breakable: true)[
        #label("Calculation", th, color: th.slate, size: scale.caption)
        #v(0.55em)
        #block(width: 100%)[
          #set par(justify: false, first-line-indent: 0em, leading: scale.body * 1.5)
          #for i in range(steps.len()) [
            #numbered-row(i + 1, str(steps.at(i)), th)
            #v(0.22em)
          ]
        ]
        #v(0.9em)
      ]
    ]
    #if answer != "" [
      #block(width: 100%, breakable: true)[
        #result-panel(answer, "Result — illustrative figures only", th)
      ]
    ]
    #if others.len() > 0 [
      #v(0.9em)
      #block(width: 100%)[#body-flow(others, th)]
    ]
  ]
}


// ============================================================================
//  J · WORKBOOK PAGE
//  Title, instructions, numbered steps, then ruled answer space sized to the
//  height actually left over. `pg.answer_rules` is fitted by the renderer.
// ============================================================================
#let layout-workbook-exercise(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 24mm, left: 28mm, right: 24mm), fill: th.paper)
  let blocks = blocks-of(pg)
  let exs = blocks.filter(b => is-type(b, ("exercise")))
  let rest = blocks.filter(b => not is-type(b, ("exercise")))
  let idx = int(pg.at("exercise_index", default: 1))
  // Every exercise on the page is drawn by this family, each with its own ruled
  // response area. Routing the second and third through the generic card would
  // draw a second and third set of rules with no page left for them, and the
  // spread read as a title over three clipped cards.
  let rules = int(pg.at("answer_rules", default: 8))
  let fields = exs.map(e => e.at("exercise", default: (:)))
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #block(width: 100%, breakable: false)[
      #grid(
        columns: (1fr, auto),
        align: (left, right),
        label("Workbook", th, color: th.terracotta),
        number-badge("W" + str(idx), th),
      )
      #v(0.75em)
      #accent-rule(th, accent: 20mm)
    ]
    #v(0.9em)
    #if rest.len() > 0 [
      #block(width: 100% - 14mm)[#body-flow(rest, th)]
      #v(0.8em)
    ]
    #for (n, ex) in fields.enumerate() [
      #block(width: 100%, breakable: false)[
        #grid(
          columns: (11mm, 1fr),
          column-gutter: 5mm,
          align: (left, left),
          text(
            font: th.mono-font,
            size: scale.body,
            weight: "bold",
            fill: th.brass,
          )[#{str(n + 1)}.],
          block(width: 100%)[
            #set par(justify: false, first-line-indent: 0em, leading: th.lead)
            #let kind = str(ex.at("kicker", default: "Task")).trim()
            #let title = str(ex.at("title", default: "")).trim()
            #if kind != "" [
              #label(kind, th, color: th.slate, size: scale.caption)
              #v(0.2em)
            ]
            #if title != "" [
              #dsp(title, th, size: scale.sub)
              #v(0.3em)
            ]
            #let instr = str(ex.at("instructions", default: "")).trim()
            #let question = str(ex.at("question", default: "")).trim()
            #if instr != "" [
              #text(size: scale.body, fill: th.ink)[#instr]
              #v(0.25em)
            ]
            #if question != "" [
              #text(size: scale.body, style: "italic", fill: th.ink)[#question]
              #v(0.25em)
            ]
            #let hints = ex.at("hints", default: ())
            #if hints.len() > 0 [
              #caption(hints.join("  "), th)
              #v(0.25em)
            ]
          ],
        )
        #v(0.35em)
        #side-rule(th, weight: 0.8pt, color: th.brass, length: 12mm)
        #v(0.3em)
        #answer-area(rules, th, gap: 13pt)
      ]
      #if n < fields.len() - 1 [#v(0.5em)]
    ]
  ]
}


// ============================================================================
//  K · CHECKLIST PAGE
//  Heading, a short introduction, then checkbox rows. Two columns only when the
//  items are short enough to keep a comfortable measure.
// ============================================================================
#let layout-checklist-page(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 26mm, left: 28mm, right: 26mm), fill: th.paper)
  let blocks = blocks-of(pg)
  let items = list-items(blocks)
  let head = lead-heading(blocks)
  let rest = without-head(blocks.filter(b => not is-type(b, ("list", "list_item", "checklist"))), head)
  let two-col = items.len() >= 8 and items.all(i => i.len() <= 88)
  let warn-words = ("never", "always", "must", "avoid", "before you", "critical", "do not", "without")
  let is-warn = i => warn-words.any(w => w in i.lower())
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #if head != "" [
      #label(or-label(pg, "Checklist"), th, color: th.terracotta)
      #v(0.6em)
      #page-title(head, th, size: scale.section)
      #v(0.3em)
      #accent-rule(th, accent: 24mm)
      #v(0.8em)
    ]
    #block(width: 100% - 22mm)[#body-flow(rest, th)]
    #v(0.9em)
    #if items.len() > 0 [
      #block(width: 100%, breakable: false)[
        #set par(justify: false, first-line-indent: 0em, leading: th.lead)
        #if two-col [
          #columns(2, gutter: 9mm)[
            #for i in items [
              #checkbox-item(i, th, warn: is-warn(i))
              #v(0.3em)
            ]
          ]
        ] else [
          #for i in items [
            #checkbox-item(i, th, warn: is-warn(i))
            #v(0.34em)
          ]
        ]
      ]
    ]
  ]
}


// ============================================================================
//  L · PULL-QUOTE PAGE
//  One statement at display size and a lot of air. Fed only from a quotation
//  block the manuscript actually contains.
// ============================================================================
#let layout-pull-quote-page(pg, doc, th) = {
  set page(margin: (top: 52mm, bottom: 34mm, left: 38mm, right: 40mm), fill: th.paper)
  let blocks = blocks-of(pg)
  let quotes = blocks.filter(b => is-type(b, ("quotation", "pull_quote")))
  let head = lead-heading(blocks)
  let q = if quotes.len() > 0 { quotes.at(0) } else { none }
  let qtext = if q == none { "" } else { text-of(q) }
  let qattr = if q == none { none } else { str(q.at("pull_quote", default: (:)).at("author", default: "")) }
  let support = blocks.filter(b => b != q)
  let support = without-head(support, head)
  block(width: 100%)[
    #set par(justify: false, first-line-indent: 0em, leading: th.lead)
    #if head != "" [
      #label(or-label(pg, "In practice"), th, color: th.terracotta)
      #v(0.6em)
      #page-title(head, th, size: scale.sub)
      #v(0.4em)
      #rule(th, weight: 0.8pt, color: th.brass, width: 20mm)
    ]
    #v(1.6em)
    #if qtext != "" [
      #pull-quote(
        qtext,
        th,
        attribution: if qattr == "" { none } else { qattr },
        size: 26pt,
      )
    ] else if support.len() > 0 [
      #pull-quote(first-sentence(support.at(0), limit: 260), th, size: 24pt)
    ]
    #v(1.4em)
    #if support.len() > 0 [
      #block(width: 100% - 14mm)[
        #set par(justify: true, first-line-indent: 0em, leading: th.lead)
        #text(size: scale.body)[#text-of(support.at(0))]
      ]
    ]
  ]
}


// ============================================================================
//  M · DIAGRAM PAGE
//  Title, one sentence of explanation, then the diagram gets the page. The
//  figure number and caption are part of the composition.
// ============================================================================
#let layout-diagram-page(pg, doc, th) = {
  set page(margin: (top: 28mm, bottom: 24mm, left: 26mm, right: 24mm), fill: th.paper)
  let blocks = blocks-of(pg)
  let plate = figure-of(pg)
  let head = lead-heading(blocks)
  let is-steps = b => is-type(b, ("process_diagram", "list", "list_item"))
  let steps = list-items(blocks)
  let rest = blocks.filter(
    b => not (is-steps(b) or is-type(b, ("image_instruction")) or is-type(b, ("quotation"))))
  let rest = without-head(rest, head)
  let intro = if rest.len() > 0 { first-sentence(rest.at(0), limit: 180) } else { "" }
  let fig-no = int(pg.at("figure_index", default: 1))
  let tail = if rest.len() > 1 { rest.slice(1) } else { () }
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #label("Diagram " + str(fig-no), th, color: th.terracotta)
    #v(0.55em)
    #if head != "" [
      #page-title(head, th, size: scale.section)
      #v(0.25em)
    ]
    #accent-rule(th, accent: 24mm)
    #v(0.7em)
    #if intro != "" [
      #block(width: 100% - 26mm)[
        #set par(justify: false, first-line-indent: 0em, leading: scale.lead * 1.32)
        #lead(intro, th, color: th.slate)
      ]
    ]
    #v(1em)
    #if plate != none [
      #block(width: 100%, breakable: true)[
        #figure-block(plate, th)
        #figure-caption(fig-no, str(plate.at("caption", default: "")), th)
      ]
    ] else if steps.len() > 0 [
      #block(width: 100%, breakable: true)[
        #process-diagram(steps, th)
        #figure-caption(
          fig-no,
          "The working sequence for this section. Take the steps in order: each "
            + "one narrows the " + term(pg, "collection", "record set")
            + " to what still needs a decision, and none can be skipped without "
            + "accepting a known " + term(pg, "stake", "risk") + ".",
          th,
        )
      ]
    ]
    #v(1em)
    #if tail.len() > 0 [
      #block(width: 100% - 18mm)[#body-flow(tail, th)]
    ]
  ]
}


// ============================================================================
//  N · DATA TABLE PAGE
//  Landscape, because a wide analytical table is the one content in this book
//  that genuinely needs the width. Rows are separated by rules, not shading,
//  so the type stays legible.
// ============================================================================
#let layout-data-table-page(pg, doc, th) = {
  // The sheet size is the plan's to set, at the break in book_pages.typ: a page
  // takes its size from the settings in force where it starts, and a family that
  // set one in its own body was overridden by the outer scope anyway -- and
  // `flipped: true` with a landscape width and height asked for a portrait
  // sheet, since flipped means the dimensions are given portrait-first.
  set page(
    margin: (top: 24mm, bottom: 20mm, left: 26mm, right: 24mm),
    fill: th.paper,
  )
  let blocks = blocks-of(pg)
  let head = lead-heading(blocks)
  let tables = blocks.filter(b => is-type(b, ("table")))
  let rest = without-head(blocks.filter(b => not is-type(b, ("table"))), head)
  let support = rest.filter(b => not is-type(b, ("heading")))
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #label(or-label(pg, "Reference table"), th, color: th.terracotta)
    #v(0.55em)
    #if head != "" [
      #page-title(head, th, size: scale.section)
      #v(0.25em)
    ]
    #accent-rule(th, accent: 26mm)
    #v(0.75em)
    #if support.len() > 0 [
      #block(width: 100% - 34mm)[#body-flow(support, th)]
      #v(0.6em)
    ]
    #block(width: 100%, breakable: true)[
      #set text(size: scale.body-sm)
      #render-blocks(tables, th)
    ]
  ]
}


// ============================================================================
//  O · RECAP AND ACTION PLAN
//  The chapter's closing spread: lessons left, action checklist right, so the
//  page reads as "what you now know / what you now do".
// ============================================================================
#let layout-recap-plan-page(pg, doc, th) = {
  set page(margin: (top: 34mm, bottom: 26mm, left: 28mm, right: 26mm), fill: th.paper)
  let rd = pg.at("recap_data", default: (:))
  let summary = str(rd.at("summary", default: "")).trim()
  let points = rd.at("points", default: ()).map(s => str(s))
  let practice = rd.at("practice", default: ())
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #label("Chapter recap", th, color: th.terracotta)
    #v(0.6em)
    #page-title(str(rd.at("title", default: "Chapter recap")), th, size: scale.section + 1pt)
    #v(0.3em)
    #accent-rule(th, accent: 26mm)
    #v(0.9em)
    #if summary != "" [
      #block(width: 100%, breakable: true)[
        #set par(justify: true, first-line-indent: 0em, leading: scale.lead * 1.32)
        #lead(summary, th, color: th.ink)
      ]
      #v(0.9em)
    ]
    #grid(
      columns: (1fr, 9mm, 0.62fr),
      align: (left, left, left),
      ruled-column([
        #set par(justify: false, first-line-indent: 0em, leading: scale.body * 1.5)
        #label("Lessons", th, color: th.slate, size: scale.caption)
        #v(0.65em)
        #for i in range(calc.min(points.len(), 7)) [
          #numbered-row(i + 1, points.at(i), th)
          #v(0.3em)
        ]
      ], th, inset: 5mm),
      block(width: 100%)[],
      block(width: 100%)[
        #set par(justify: false, first-line-indent: 0em, leading: scale.body * 1.5)
        #label("Action plan", th, color: th.slate, size: scale.caption)
        #v(0.65em)
        #if practice.len() > 0 [
          #for p in practice [
            #checkbox-item(
              str(p.at("subject", default: "")),
              th,
              warn: str(p.at("kind", default: "")) != "Exercise",
            )
            #v(0.3em)
          ]
        ] else [
          #text(size: scale.body-sm, fill: th.slate)[No exercises were set for this chapter.]
        ]
        #v(0.9em)
        #side-rule(th, weight: 1.4pt, color: th.brass, length: 16mm)
      ],
    )
  ]
}


// ============================================================================
//  P · GLOSSARY AND REFERENCE PAGE
//  Term in the display face, definition in the body face, entries separated by
//  whitespace and a hairline. Two columns only when the measure stays readable.
// ============================================================================
#let layout-reference-page(pg, doc, th) = {
  set page(margin: (top: 30mm, bottom: 26mm, left: 28mm, right: 26mm), fill: th.paper)
  let blocks = blocks-of(pg)
  let is-glossary = str(pg.at("purpose", default: "")) == "glossary"
  let title = if is-glossary { "Glossary" } else { "Sources and further reading" }
  let label-text = "Reference"
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, leading: th.lead)
    #label(label-text, th, color: th.terracotta)
    #v(0.6em)
    #page-title(title, th, size: scale.section)
    #v(0.3em)
    #accent-rule(th, accent: 24mm)
    #v(0.9em)
    #if is-glossary [
      #let entries = pg.at("glossary_data", default: (:)).at("entries", default: ())
      #let narrow = entries.len() <= 6 or entries.all(e => str(e.at("definition", default: "")).len() < 150)
      #if narrow [
        #block(width: 100%)[
          #set par(justify: true, first-line-indent: 0em, leading: th.lead)
          #for e in entries [
            #grid(
              columns: (44mm, 1fr),
              column-gutter: 5mm,
              align: (left, left),
              dsp(str(e.at("term", default: "")), th, size: scale.body + 0.5pt),
              text(size: scale.body, fill: th.ink)[#str(e.at("definition", default: ""))],
            )
            #v(0.75em)
            #rule(th, weight: 0.3pt)
            #v(0.6em)
          ]
        ]
      ] else [
        #block(width: 100%)[
          #set par(justify: true, first-line-indent: 0em, leading: th.lead)
          #columns(2, gutter: 8mm)[
            #for e in entries [
              #dsp(str(e.at("term", default: "")), th, size: scale.body + 0.5pt)
              #v(0.18em)
              #text(size: scale.body-sm, fill: th.ink)[#str(e.at("definition", default: ""))]
              #v(0.7em)
            ]
          ]
        ]
      ]
    ] else [
      #let declared = pg.at("references_data", default: (:)).at("entries", default: ())
      #let refs = if declared.len() > 0 {
        declared
      } else {
        blocks.filter(b => is-type(b, ("reference"))).map(b => text-of(b))
      }
      #block(width: 100% - 22mm)[
        #set par(justify: true, first-line-indent: 0em, leading: scale.body * 1.5)
        #for i in range(refs.len()) [
          #numbered-row(i + 1, str(refs.at(i)), th)
          #v(0.55em)
          #rule(th, weight: 0.3pt)
          #v(0.5em)
        ]
      ]
    ]
  ]
}
