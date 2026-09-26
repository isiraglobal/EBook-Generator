// ============================================================================
//  chrome.typ — the book's furniture
// ============================================================================
//
//  Running heads, folios, front matter, drop caps, marginalia. Everything a
//  book has on every page regardless of what the page contains.
//
//  The patterns are taken from the inspected references:
//  · bookly (`src/themes/classic.typ`) runs a hydra in the head -- the chapter
//    on the verso, the current section on the recto -- with a hairline under
//    it. Adopted, with the folio moved out of the head into the foot.
//  · beautiful-pdf-mcp (`templates/book.typ`) puts the folio on the outer edge
//    and suppresses furniture on the first leaves. Adopted.
//  · typst-pandoc (`templates/layman.typ`) builds its sidebars as margin notes
//    against inside/outside margins. Adopted, resolved onto this book's own
//    margin column rather than a package's.
// ============================================================================

#import "grid.typ": *
// Aliased, not star-imported: `content.typ` re-exports `helpers.typ`, which
// binds `theme` to a *function* that resolves a preset. A bare `theme` here
// would therefore be that function rather than the grid's theme dictionary, and
// `T.ink-deep` would fail at the first page. Aliasing makes the intent explicit
// and independent of import order.
#import "grid.typ": theme as grid-theme
#import "content.typ": *

// ── Running head ────────────────────────────────────────────────────────────
// A hydra: the chapter name on the verso, the live section title on the recto.
// Both are set in the small tracked sans at caption size, aligned to the outer
// edge, with a hairline under the head that stops short of the fore-edge --
// the rule is the only thing that says "this is a running head, not a rule".
// ── Running head ────────────────────────────────────────────────────────────
// A hydra: the chapter on the verso, the section on the recto.
//
// The two strings are handed to the family by `head-data` rather than found by
// querying the document from inside the header. Two reasons. The first is that
// a query inside a header is answered in the header's own scope, where a
// heading's appearance is resolved rather than its text, so the head printed
// chapter titles at the display size of their openers -- three lines deep, half
// of it off the top of the sheet. The second is that `here()` in a header is
// *before* the page's own body, so "the section in force on this page" is the
// section on the page before it. The page already knows both strings; the head
// only has to be told.
#let head-data(pg) = {
  let co = opener-of(pg)
  let section = lead-heading(blocks-of(pg))
  let chapter = str(co.at("chapter_title", default: ""))
  let number = str(co.at("chapter_number", default: ""))
  let recto = if section == none or section == "" { chapter } else { section }
  let verso = if number == "" { chapter } else { number + "   " + chapter }
  (recto: recto, verso: verso)
}

// `context` because the recto/verso decision needs the page number, which is
// only known once the page is being laid out.
#let running-head(T, data) = context {
  if data == none { return none }
  let recto = calc.odd(here().page())
  let title = if recto { data.recto } else { data.verso }
  if title == "" { return none }
  block(width: 100%)[
    #set par(justify: false, first-line-indent: 0em, leading: T.meta-size * 1.3)
    #text(
      font: T.heading-font,
      size: T.meta-size,
      fill: T.slate,
      tracking: 1.3pt,
      if recto { align(right)[#title] } else { align(left)[#title] },
    )
    #v(-2.5pt)
    #line(length: 100%, stroke: 0.4pt + T.rule)
  ]
}

// ── Folio ───────────────────────────────────────────────────────────────────
// The page number on the outer edge, so the reader's thumb never covers it.
// Set in the serif at micro size, because a folio is furniture and should not
// compete with the last line of the text block.
#let folio(T) = context {
  let pg = here().page()
  if pg > 3 {
    set text(font: T.body-font, size: T.micro-size, fill: T.slate)
    set par(justify: false, first-line-indent: 0em)
    if calc.odd(pg) { align(right, []) } else { align(left, []) }
    counter(page).display("1")
  }
}

// The default running chrome: a hydra head, a folio on the outer edge, and a
// hairline above the folio only on rectos, where the two are furthest apart.
#let standard-chrome(T, doc) = (
  header: running-head(T, doc),
  footer: folio(T),
)

// ── Blank chrome ────────────────────────────────────────────────────────────
// Cover, title page, imprint, contents, and every full-bleed page: no head, no
// folio, and the folio counter suppressed for the front matter.
#let no-chrome = (header: none, footer: none)

// ── Drop cap ────────────────────────────────────────────────────────────────
// A raised initial on the first paragraph of a chapter, set three lines deep in
// the serif at display weight. It sits in the margin, not in the measure: the
// cap's width is subtracted from the first two lines, so the first line still
// starts on the grid and the following lines do not move.
#let drop-cap(body, T, lines: 3) = {
  let letters = upper(body.slice(0, 1))
  let rest = body.slice(1)
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead)
    #place(
      dx: 0pt,
      dy: 1pt,
      text(
        font: T.body-font,
        size: T.pitch * lines * 0.82,
        weight: "bold",
        fill: T.brass,
        tracking: -1pt,
      )[#letters],
    )
    #h(T.pitch * 0.62)
    #rest
  ]
}

// ── Marginalia ──────────────────────────────────────────────────────────────
// A note set in the margin column, outside the measure. This is the single
// cheapest way to make a page look designed rather than typeset, and it is the
// reason the grid reserves a margin column at all.
#let margin-note(body, T) = block(width: T.margin-column, breakable: true)[
  #set par(justify: false, first-line-indent: 0em, leading: 1.32em)
  #text(font: T.heading-font, size: T.caption-size, fill: T.slate, body)
]

// A page with marginalia: the body measure narrowed to nine columns, the note
// in the three columns beyond it, aligned to its own baseline.
#let with-margin-note(body, note, T) = {
  let note-width = T.measure-width - span(0, 9) - T.gutter
  block(width: 100%, breakable: false)[
    #grid(
      columns: (span(0, 9), note-width),
      column-gutter: T.gutter,
      align: (left, left),
      body,
      block(width: note-width, breakable: false)[
        #set par(justify: false, first-line-indent: 0em, leading: 1.32em)
        #text(font: T.heading-font, size: T.caption-size, fill: T.slate, note)
      ],
    )
  ]
}

// ── Front matter ────────────────────────────────────────────────────────────
// Front matter is numbered in lowercase roman and starts at i, so the arabic
// sequence begins at 1 on the first chapter opener. `numbering: "i"` on the
// page does both.
#let front-matter-numbering = "i"

// ── The opener's learning objectives ─────────────────────────────────────────
// A list of what the chapter will enable, set in the measure with a hairline
// above it. Kept here rather than in a family because both opener compositions
// use it and it must look identical on either.
#let opener-objectives(objectives, T) = block(width: 100%, breakable: false)[
  #set par(justify: false, first-line-indent: 0em, leading: T.lead)
  #divider(T, level: "hair")
  #v(0.7em)
  #label-text("In this chapter", fill: T.terracotta, size: T.micro-size)
  #v(0.65em)
  #for o in objectives [
    #dash-row(o, T, size: T.small-size, color: T.brass)
    #v(0.2em)
  ]
]

// ── A figure, capped ────────────────────────────────────────────────────────
// The artwork, contained, with its caption beneath it. `height` is the cap: a
// family passes the type height less whatever the page has already used, and
// this is where the artwork is held to it. Both `width` and `height` must be
// given for `fit: "contain"` to do anything -- with a height alone Typst falls
// back to the artwork's natural size and the cap silently does nothing, which
// is what pushed composed pages onto a second sheet in the old system.
#let figure-block(plate, T, height: none, tail: 1.1em) = {
  if plate == none { return none }
  let path = str(plate.at("path", default: ""))
  if path == "" { return none }
  let caption = str(plate.at("caption", default: ""))
  block(width: 100%, breakable: false)[
    #box(
      width: 100%,
      fill: T.paper-warm,
      stroke: 0.5pt + T.rule,
      inset: 0pt,
      clip: true,
    )[
      #if height == none [
        #image(path, width: 100%, fit: "contain")
      ] else [
        #align(center + horizon)[
          #image(path, width: 100%, height: height, fit: "contain")
        ]
      ]
    ]
    #if caption != "" [
      #v(0.5em)
      #line(length: 16mm, stroke: 0.9pt + T.brass)
      #v(0.35em)
      #caption-text(caption, T)
    ]
  ]
}

// ── Two columns, deterministically ──────────────────────────────────────────
// Typst's `columns()` balances a multi-column region against a height it has to
// discover, which inside an unbreakable block collapses to one column and leaves
// half the measure empty. Since a family already knows the type height, the
// split is done here instead: the list is cut in half and the halves are laid in
// a grid on the column spans. The result is a real two-column page whose two
// sides are always equal in height, which is also what QA reads as two columns.
#let two-column-list(items, T, gutter: none) = {
  let half = calc.ceil(items.len() / 2)
  let left-col = items.slice(0, half)
  let right-col = if half >= items.len() { () } else { items.slice(half, items.len()) }
  grid(
    columns: (1fr, 1fr),
    column-gutter: if gutter == none { T.gutter + 2mm } else { gutter },
    align: (left, left),
    ..left-col,
    ..right-col,
  )
}

// ── The grid sheet ──────────────────────────────────────────────────────────
// The page every grid family is set on: A4, the Van de Graaf margins, the paper
// tint, and the running chrome. It lives here rather than in a family because
// the sheet is not a compositional choice -- it is the grid, and a family that
// could set its own margins could not be checked against it.
#let grid-page-setup(T) = (
  paper: T.paper-size,
  width: T.sheet-width,
  height: T.sheet-height,
  margin: page-margins(T),
  fill: T.paper,
)

// The wrapper a grid family is registered through. The sheet and the chrome are
// set here; the family only ever composes inside the type area it is given.
// The legacy theme argument the dispatcher passes is deliberately ignored: these
// families are set from `grid.typ` alone.
#let on-grid(body, T: grid-theme, head: (:)) = {
  set page(
    ..grid-page-setup(T),
    header: running-head(T, head),
    footer: folio(T),
  )
  // The page's own typography. Without this a grid family inherits whatever the
  // document happened to set -- the design_system theme's body face, at the
  // design_system's leading -- and the book ends up with two typefaces in it:
  // the front matter in PT Serif and every body page in PT Serif with Source
  // headings on top. A family that could be re-typed by something outside its
  // own file is not self-contained, and this is what makes it so.
  set text(font: T.body-font, size: T.text-size, fill: T.ink)
  set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
  // Typst's own heading block carries spacing and a keep-with-next rule. A grid
  // page places its own headings at its own vertical positions and expresses the
  // gaps in baselines, so the defaults are cleared here rather than fought with
  // in thirteen places.
  show heading: set block(above: 0pt, below: 0pt, breakable: false)
  // The two heading appearances. They are written out here rather than returned
  // from a helper because `show` is only legal directly in code and content
  // blocks, and a family that could not be restyled from one place would drift.
  //
  // The leading is set inside the appearance rather than on the element, so it
  // is in force both on the page and in the contents page -- which renders the
  // same heading bodies in the front-matter scope, where a rule set inside a
  // page family does not reach.
  show heading.where(level: 1): it => block(
    width: 100%,
    breakable: false,
    above: 0pt,
    below: 0pt,
  )[
    #set par(justify: false, first-line-indent: 0em, leading: T.h1-size * 1.1)
    #text(
      font: T.heading-font,
      size: T.h1-size,
      weight: "bold",
      fill: chapter-ink.get(),
      tracking: -0.5pt,
      [#it.body],
    )
  ]
  show heading.where(level: 3): it => block(
    width: 100%,
    breakable: false,
    above: 0pt,
    below: 0pt,
  )[
    #set par(justify: false, first-line-indent: 0em, leading: T.h3-size * 1.16)
    #text(
      font: T.heading-font,
      size: T.h3-size,
      weight: "semibold",
      fill: T.ink,
      [#it.body],
    )
  ]
  show heading.where(level: 2): it => block(
    width: 100%,
    breakable: false,
    above: 0pt,
    below: 0pt,
  )[
    #set par(justify: false, first-line-indent: 0em, leading: T.h2-size * 1.16)
    #text(
      font: T.heading-font,
      size: T.h2-size,
      weight: "semibold",
      fill: T.ink,
      [#it.body],
    )
  ]
  body
}

#let grid-family(f) = (pg, doc, _) => on-grid(
  f(pg, doc, grid-theme),
  head: head-data(pg),
)
