// ============================================================================
//  grid.typ — the page grid the whole book is set on
// ============================================================================
//
//  Everything else in this book assumes this file. A page is not a set of
//  ad-hoc margins: it is a fixed sheet, a fixed text block, a fixed baseline
//  pitch, and a column grid the text block is divided into. A page family
//  chooses which columns its content occupies; it never invents a width.
//
//  The model comes from three inspected references, and the reasoning is
//  recorded because it is the part that is easy to get wrong:
//
//  · Van de Graaf / mirrored margins (beautiful-pdf-mcp, `templates/book.typ`):
//    `inside`/`outside` rather than `left`/`right`. On a recto the outside edge
//    is the right, on a verso the left, so the binding edge always carries the
//    wider margin and the text block never crowds the spine. The old system used
//    fixed left/right margins, which is why its text block sat at a different
//    distance from the edge on every page type.
//
//  · The grid as a column count with a gutter and a margin column
//  (typst-pandoc, `templates/layman.typ`): the page has a text block *and* an
//  outer margin column, so a sidenote, a figure caption or a pull quote can sit
//  outside the measure without hanging into the trim.
//
//  · Hydrunning heads and a folio on the outer edge (bookly, `src/themes/`): a
//  verso names the chapter, a recto names the section, and the page number
//  follows the outer edge so the reader's thumb covers the wrong one.
//
//  Van de Graaf ratios, applied to A4 (210 × 297 mm):
//
//      top      = 1 / 11 × 297  = 27.0 mm
//      bottom   = 2 / 11 × 297  = 54.0 mm      -> typographic page height
//      inside   = 1 / 10 × 210  = 21.0 mm
//      outside  = 2 / 10 × 210  = 42.0 mm
//
//  The 54mm foot is not decoration. It is where the running foot lives, and a
//  generous foot is the single cheapest thing that makes a book read as a book
//  rather than as a document.
//
//  The baseline pitch is 15.2pt and the body is 10.5pt, so the ratio is 1.448.
//  Every vertical measurement in this book is a multiple of that pitch. That is
//  what keeps headings, figures, panels and rules on the same rhythm as the text
//  instead of drifting a point or two off it.
// ============================================================================

#let grid-paper = "a4"

// ── The sheet ───────────────────────────────────────────────────────────────
#let sheet-width = 210mm
#let sheet-height = 297mm

// Van de Graaf. `inside` binds to the spine, `outside` is the fore-edge.
#let margin-top = 27mm
#let margin-bottom = 54mm
#let margin-inside = 21mm
#let margin-outside = 42mm

// The text block is what is left. One number, and every family works inside it.
#let measure-width = sheet-width - margin-inside - margin-outside
#let type-height = sheet-height - margin-top - margin-bottom

// ── The baseline grid ───────────────────────────────────────────────────────
#let body-size = 10.5pt
#let pitch = 15.2pt

// Typst's `par.leading` is *extra* leading, added to the line height the font
// itself asks for -- it is not the distance between baselines. Measured against
// the bundled Source Serif 4 at 10.5pt with `leading: 0pt`, the font contributes
// 7.33pt, so writing `leading: 15.2pt` produced a 22.5pt baseline distance
// rather than the 15.2pt the grid is built on. The figure was solved from a
// rendered build: with `body-leading` at 8.17pt the book set at 15.5pt, which
// put the font's own contribution at 7.33pt.
//
// The two numbers are therefore separate, and conflating them is the single
// easiest way to lose the rhythm: `pitch` is the design grid, `font-line-height`
// is what the font costs, and `body-leading` is what has to be added to reach
// the grid. Every vertical measurement in the book is a multiple of `pitch`.
//
// The 7.03pt is a property of Source Serif 4 at this size. If the serif face is
// changed, it has to be re-measured: set `leading: 0pt`, set three lines of
// 10.5pt body text, and read the baseline distance from the PDF with the same
// min-gap-per-column method tests/test_visual_regression.py uses.
#let font-line-height = 7.33pt
#let body-leading = pitch - font-line-height

// How many baselines the type area holds. This is the planner's capacity: the
// single most important number in the build, and the reason a page either fits
// or it does not.
#let lines-per-page = int(type-height / pitch)

// The typographic page height is not a whole number of baselines. The leftover
// goes to the foot, which is where a book puts it.
#let pitch-remainder = type-height - lines-per-page * pitch

// ── The column grid ─────────────────────────────────────────────────────────
// Twelve columns across the measure, with a 4mm gutter. A family never writes
// a width; it writes a span, and the span is resolved here.
//
// Named `column-count`, not `columns`: Typst's `columns()` is a layout
// function, and a module-level binding of that name star-imported into a
// template would shadow it and turn every two-column passage in the book into a
// call on the integer 12.
#let column-count = 12
#let gutter = 4mm

#let column-width = (measure-width - gutter * (column-count - 1)) / column-count

// A span of `n` columns starting at column `from` (0-indexed), as a length.
#let span(from, n) = n * column-width + (n - 1) * gutter

// The column a 1-based index starts at, as a left offset from the text block.
#let offset(from) = from * (column-width + gutter)

// How many columns a given measure takes, for checking a design intent.
#let columns-in(width) = {
  let n = 0
  while n < column-count and span(0, n + 1) <= width { n += 1 }
  n
}

// ── The margin column ───────────────────────────────────────────────────────
// The strip outside the text block, between the measure and the fore-edge. A
// sidenote, a figure caption or a margin note lives here and never narrows the
// body. It is 42mm less the 4mm gutter the grid reserves, which is enough for a
// caption set at caption size.
#let margin-column = margin-outside - gutter

// ── Colour ──────────────────────────────────────────────────────────────────
// The editorial palette, unchanged. It is the one asset of the old design system
// that was already right: warm paper, near-black ink, and two accents used
// sparingly enough that they still read as accents.
#let paper = rgb("#F7F3EC")
#let ink = rgb("#1A1815")
#let brass = rgb("#B08D57")
#let terracotta = rgb("#A0523D")
#let slate = rgb("#6B6560")
#let rule = rgb("#D9CFBF")

// A deeper ink for full-bleed pages, and the tints derived from the palette.
#let ink-deep = rgb("#12100E")
#let paper-warm = rgb("#EFE8DA")
#let brass-tint = rgb("#F1E7D3")
#let slate-tint = rgb("#E7E2DA")

// ── Type ────────────────────────────────────────────────────────────────────
// Source Serif 4 and Source Sans 3, both SIL Open Font License 1.1, bundled in
// `assets/fonts` with their licences. They are drawn for books and screens
// respectively, which is exactly the division of labour this book needs, and
// both embed and subset in the PDF (verified in tests/test_visual_regression.py).
// The PT family stays configured as the fallback so a machine without the
// bundled files still builds.
#let serif = ("Source Serif 4", "PT Serif", "Libertinus Serif", "New Computer Modern")
#let sans = ("Source Sans 3", "PT Sans", "Helvetica", "Arial")
#let mono = ("Source Code Pro", "PT Mono", "Menlo", "Courier New")

// The scale. Every step is a multiple of the body size, chosen so that the
// difference between adjacent steps is visible at arm's length and no two steps
// are close enough to be confused.
#let scale = (
  micro: 6.4pt,     // folios, table data, folios on the outer edge
  caption: 7.4pt,   // figure captions, notes
  meta: 8.2pt,      // kickers, running heads, exercise instructions
  small: 9.2pt,     // sidebars, table cells, marginalia
  body: body-size,  // 10.5pt
  lead: 12.4pt,     // standfirsts, the first line after a heading
  sub: 15pt,        // h3
  section: 20pt,    // h2
  display: 30pt,    // h1, chapter titles
  giant: 62pt,      // chapter numerals
  giant-sm: 40pt,   // chapter numerals on compact openers
)

// ── Vertical rhythm ─────────────────────────────────────────────────────────
// A rule for anyone adding a family: express vertical space in baselines, not
// in points and not in ems. `bl(1)` is one line of the grid; `bl(0.5)` is a
// deliberate half-step for optical adjustment only.
#let bl(n) = n * pitch

// Spacing between blocks, as multiples of the baseline. `par-space` is the gap
// between paragraphs; the rest are the gaps a page family is allowed to use.
#let space-par = bl(0.5)
#let space-tight = bl(0.25)
#let space-after-head = bl(0.75)
#let space-before-head = bl(1.5)
#let space-block = bl(1)

// ============================================================================
//  The theme dictionary
// ============================================================================
//  One object, passed to every family, holding every number the book is set
//  from. A family reads it; nothing else defines a measurement of its own.
#let theme = (
  // grid
  paper-size: grid-paper,
  sheet-width: sheet-width,
  sheet-height: sheet-height,
  margin-top: margin-top,
  margin-bottom: margin-bottom,
  margin-inside: margin-inside,
  margin-outside: margin-outside,
  measure-width: measure-width,
  type-height: type-height,
  margin-column: margin-column,
  columns: column-count,
  gutter: gutter,
  column-width: column-width,
  lines-per-page: lines-per-page,
  // rhythm
  pitch: pitch,
  lead: body-leading,
  par-space: space-par,
  space-tight: space-tight,
  space-after-head: space-after-head,
  space-before-head: space-before-head,
  space-block: space-block,
  // type
  body-font: serif,
  heading-font: sans,
  mono-font: mono,
  text-size: body-size,
  h1-size: scale.display,
  h2-size: scale.section,
  h3-size: scale.sub,
  lead-size: scale.lead,
  font-line-height: font-line-height,
  small-size: scale.small,
  caption-size: scale.caption,
  meta-size: scale.meta,
  micro-size: scale.micro,
  display-size: scale.display,
  giant-size: scale.giant,
  giant-sm-size: scale.giant-sm,
  scale: scale,
  // colour
  paper: paper,
  ink: ink,
  ink-deep: ink-deep,
  paper-warm: paper-warm,
  brass: brass,
  brass-tint: brass-tint,
  terracotta: terracotta,
  slate: slate,
  slate-tint: slate-tint,
  rule: rule,
)

// The mirrored page margins as Typst wants them: Typst takes `inside`/`outside`
// and resolves them per page, so the text block sits at a constant distance
// from the spine on both sides of the sheet.
#let page-margins(th) = (
  top: th.margin-top,
  bottom: th.margin-bottom,
  inside: th.margin-inside,
  outside: th.margin-outside,
)

// The base page. A family may override `fill`, `header` and `footer`; it may not
// override the margins, which are the grid.
#let grid-page(body, th: theme, fill: none, header: auto, footer: auto) = {
  set page(
    paper: th.paper-size,
    width: th.sheet-width,
    height: th.sheet-height,
    margin: page-margins(th),
    fill: if fill == none { th.paper } else { fill },
    header: header,
    footer: footer,
  )
  set text(
    font: th.body-font,
    size: th.text-size,
    fill: th.ink,
    lang: "en",
    // Cheap hyphenation, no runt lines, no widows or orphans. On a justified
    // measure of 60-70 characters these three costs are the difference between
    // tight lines and rivers.
    costs: (hyphenation: 5%, runt: 100%, widow: 100%, orphan: 100%),
  )
  set par(
    justify: true,
    leading: th.lead,
    spacing: th.par-space,
    first-line-indent: 0em,
  )
  show raw: set text(font: th.mono-font, size: th.text-size * 0.86)
  body
}

// ── A display line ──────────────────────────────────────────────────────────
// Display type is set tighter than body type because it has no descenders to
// worry about and every line is a headline. `tracking` is negative at display
// sizes and positive at caption sizes; the sign change is the point.
#let display(body, size, fill: ink, tracking: -0.4pt, weight: "bold") = text(
  font: sans,
  size: size,
  weight: weight,
  fill: fill,
  tracking: tracking,
  body,
)

// A small-caps-ish label: uppercase, tracked out, no weight.
#let label-text(body, fill: terracotta, size: none) = text(
  font: sans,
  size: if size == none { scale.meta } else { size },
  fill: fill,
  tracking: 1.7pt,
  upper(body),
)

// A caption, under a figure or a table. Never justified, never tracked out.
#let caption-text(body, th) = {
  set par(justify: false, first-line-indent: 0em, leading: 1.35em)
  text(font: th.heading-font, size: th.caption-size, fill: th.slate, body)
}

// ============================================================================
//  Shared components
// ============================================================================
//
//  These are here rather than in `chrome.typ` because both `chrome.typ` and
//  `content.typ` need them and `chrome.typ` imports `content.typ`: a component
//  that lived in the chrome could not be used by the block renderer without an
//  import cycle, and a cycle between two template modules is a build failure
//  that only shows up on the page that happens to use the block.

// ── A tinted panel ──────────────────────────────────────────────────────────
// The only panel this book uses. A pale brass field with a hairline left rule,
// no border, no radius, no shadow: the reason a panel reads as typeset rather
// than as a card dropped onto the page.
#let panel(body, T, fill: none, accent: brass, inset: 6pt) = block(
  width: 100%,
  breakable: false,
  fill: if fill == none { T.brass-tint } else { fill },
  inset: (left: inset + 5pt, right: inset, top: inset, bottom: inset),
  radius: 0pt,
  stroke: (left: 1.1pt + accent),
)[
  #set par(justify: true, first-line-indent: 0em, leading: T.lead)
  #body
]

// ── A rule ──────────────────────────────────────────────────────────────────
// Named weights, because a book has three rules and no more. The weight is a
// message: 1.6pt is a division, 0.9pt is a subsection, 0.4pt is a hairline.
#let rule-strength(T, level: "hair") = {
  if level == "major" { 1.6pt + T.brass }
  else if level == "minor" { 0.9pt + T.terracotta }
  else { 0.4pt + T.rule }
}

// A rule of a given width, used as a divider under a title or above a result.
#let divider(T, width: 100%, level: "hair", space-before: 0pt, space-after: 0pt) = block(
  width: width,
  breakable: false,
  above: space-before,
  below: space-after,
)[#line(length: 100%, stroke: rule-strength(T, level: level))]

// ── Headings ────────────────────────────────────────────────────────────────
// A heading is a real Typst `heading` element, not styled text. That is what
// puts a chapter in the PDF outline, what puts a section in the contents page,
// and what lets a running head ask the document what section it is inside --
// none of which works if the title is merely large text. The families supply the
// size, the weight and the rule; Typst's own spacing is neutralised in
// `on-grid`, so a heading looks the same wherever it is set.
// The heading's body is the title and nothing else -- a plain string. The
// display treatment is applied by a show rule in `on-grid`, which reads the
// ink the sheet calls for from `chapter-ink`.
//
// That indirection is not decoration. A running head asks the document which
// chapter it is inside and prints the answer, and a heading whose body is a
// 30pt styled block prints as a 30pt styled block: the verso of every chapter
// came out with its own title set at display size across two lines in the
// header. Keeping the body plain means the hydra prints text.
#let chapter-ink = state("chapter-ink", ink)

#let chapter-heading(body, T) = heading(
  level: 1,
  numbering: none,
  outlined: true,
)[#body]

// A section heading inside a chapter. `outlined: true`: a bookmark pane for a
// 200-page book is only useful if it can be taken two levels deep, and the
// contents page is built from the same headings, so one setting gives both.
#let section-heading-element(body, T, size: none) = heading(
  level: 2,
  numbering: none,
  outlined: true,
)[#body]

// A titled division inside a section: a case study, a worked example. These are
// the entries a reader navigates to, so they are real headings and they are in
// the outline -- a 200-page book with twenty worked examples is a book whose
// worked examples cannot be found.
#let minor-heading(body, T) = heading(
  level: 3,
  numbering: none,
  outlined: true,
)[#body]

// A caption, under a figure or a table. Never justified, never tracked out.
#let caption-text(body, th) = {
  set par(justify: false, first-line-indent: 0em, leading: 1.35em)
  text(font: th.heading-font, size: th.caption-size, fill: th.slate, body)
}

// ============================================================================
//  Shared components
// ============================================================================
//
//  These are here rather than in `chrome.typ` because both `chrome.typ` and
//  `content.typ` need them and `chrome.typ` imports `content.typ`: a component
//  that lived in the chrome could not be used by the block renderer without an
//  import cycle, and a cycle between two template modules is a build failure
//  that only shows up on the page that happens to use the block.

// ── A tinted panel ──────────────────────────────────────────────────────────
// The only panel this book uses. A pale brass field with a hairline left rule,
// no border, no radius, no shadow: the reason a panel reads as typeset rather
// than as a card dropped onto the page.
#let panel(body, T, fill: none, accent: brass, inset: 6pt) = block(
  width: 100%,
  breakable: false,
  fill: if fill == none { T.brass-tint } else { fill },
  inset: (left: inset + 5pt, right: inset, top: inset, bottom: inset),
  radius: 0pt,
  stroke: (left: 1.1pt + accent),
)[
  #set par(justify: true, first-line-indent: 0em, leading: T.lead)
  #body
]

// ── A rule ──────────────────────────────────────────────────────────────────
// Named weights, because a book has three rules and no more. The weight is a
// message: 1.6pt is a division, 0.9pt is a subsection, 0.4pt is a hairline.
#let rule-strength(T, level: "hair") = {
  if level == "major" { 1.6pt + T.brass }
  else if level == "minor" { 0.9pt + T.terracotta }
  else { 0.4pt + T.rule }
}

// A rule of a given width, used as a divider under a title or above a result.
#let divider(T, width: 100%, level: "hair", space-before: 0pt, space-after: 0pt) = block(
  width: width,
  breakable: false,
  above: space-before,
  below: space-after,
)[#line(length: 100%, stroke: rule-strength(T, level: level))]

// ── Headings ────────────────────────────────────────────────────────────────
// A heading is a real Typst `heading` element, not styled text. That is what
// puts a chapter in the PDF outline, what puts a section in the contents page,
// and what lets a running head ask the document what section it is inside --
// none of which works if the title is merely large text. The families supply the
// size, the weight and the rule; Typst's own spacing is neutralised in
// `on-grid`, so a heading looks the same wherever it is set.
// The heading's body is the title and nothing else -- a plain string. The
// display treatment is applied by a show rule in `on-grid`, which reads the
// ink the sheet calls for from `chapter-ink`.
//
// That indirection is not decoration. A running head asks the document which
// chapter it is inside and prints the answer, and a heading whose body is a
// 30pt styled block prints as a 30pt styled block: the verso of every chapter
// came out with its own title set at display size across two lines in the
// header. Keeping the body plain means the hydra prints text.
#let chapter-ink = state("chapter-ink", ink)

#let chapter-heading(body, T) = heading(
  level: 1,
  numbering: none,
  outlined: true,
)[#body]

// A section heading inside a chapter. `outlined: true`: a bookmark pane for a
// 200-page book is only useful if it can be taken two levels deep, and the
// contents page is built from the same headings, so one setting gives both.
#let section-heading-element(body, T, size: none) = heading(
  level: 2,
  numbering: none,
  outlined: true,
)[#body]

// A titled division inside a section: a case study, a worked example. These are
// the entries a reader navigates to, so they are real headings and they are in
// the outline -- a 200-page book with twenty worked examples is a book whose
// worked examples cannot be found.
#let minor-heading(body, T) = heading(
  level: 3,
  numbering: none,
  outlined: true,
)[#body]

// The two show rules that give a heading its appearance. The leading is set
// here rather than on the element so it is in force both on the page and in the
// contents page, which renders the same bodies in the front-matter scope.
#let heading-appearances(T) = (
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
  ],
  show heading.where(level: 2): it => block(
    width: 100%,
    breakable: false,
    above: 0pt,
    below: 0pt,
  )[
    #let size = T.h2-size
    #set par(justify: false, first-line-indent: 0em, leading: size * 1.16)
    #text(
      font: T.heading-font,
      size: size,
      weight: "semibold",
      fill: T.ink,
      [#it.body],
    )
  ],
)

// A caption, under a figure or a table. Never justified, never tracked out.
#let caption-text(body, th) = {
  set par(justify: false, first-line-indent: 0em, leading: 1.35em)
  text(font: th.heading-font, size: th.caption-size, fill: th.slate, body)
}

// ============================================================================
//  Shared components
// ============================================================================
//
//  These are here rather than in `chrome.typ` because both `chrome.typ` and
//  `content.typ` need them and `chrome.typ` imports `content.typ`: a component
//  that lived in the chrome could not be used by the block renderer without an
//  import cycle, and a cycle between two template modules is a build failure
//  that only shows up on the page that happens to use the block.

// ── A tinted panel ──────────────────────────────────────────────────────────
// The only panel this book uses. A pale brass field with a hairline left rule,
// no border, no radius, no shadow: the reason a panel reads as typeset rather
// than as a card dropped onto the page.
#let panel(body, T, fill: none, accent: brass, inset: 6pt) = block(
  width: 100%,
  breakable: false,
  fill: if fill == none { T.brass-tint } else { fill },
  inset: (left: inset + 5pt, right: inset, top: inset, bottom: inset),
  radius: 0pt,
  stroke: (left: 1.1pt + accent),
)[
  #set par(justify: true, first-line-indent: 0em, leading: T.lead)
  #body
]

// ── A rule ──────────────────────────────────────────────────────────────────
// Named weights, because a book has three rules and no more. The weight is a
// message: 1.6pt is a division, 0.9pt is a subsection, 0.4pt is a hairline.
#let rule-strength(T, level: "hair") = {
  if level == "major" { 1.6pt + T.brass }
  else if level == "minor" { 0.9pt + T.terracotta }
  else { 0.4pt + T.rule }
}

// A rule of a given width, used as a divider under a title or above a result.
#let divider(T, width: 100%, level: "hair", space-before: 0pt, space-after: 0pt) = block(
  width: width,
  breakable: false,
  above: space-before,
  below: space-after,
)[#line(length: 100%, stroke: rule-strength(T, level: level))]

// ── Headings ────────────────────────────────────────────────────────────────
// A heading is a real Typst `heading` element, not styled text. That is what
// puts a chapter in the PDF outline, what puts a section in the contents page,
// and what lets a running head ask the document what section it is inside --
// none of which works if the title is merely large text. The families supply the
// size, the weight and the rule; Typst's own spacing is neutralised in
// `on-grid`, so a heading looks the same wherever it is set.
// The leading is set *inside* the body, not by a show rule on the element. A
// show rule's paragraph settings belong to the scope it was set in, and the
// contents page renders these same bodies in the legacy front-matter scope --
// where the rule does not reach. The outline then measured each entry with one
// leading and the heading rendered with another, and consecutive entries
// overlapped. A setting that has to survive being rendered twice travels with
// the content.
#let chapter-heading(body, T, fill: none) = heading(
  level: 1,
  numbering: none,
  outlined: true,
)[#block(width: 100%, breakable: false, above: 0pt, below: 0pt)[
  #set par(justify: false, first-line-indent: 0em, leading: T.h1-size * 1.1)
  #text(
    font: T.heading-font,
    size: T.h1-size,
    weight: "bold",
    fill: if fill == none { T.ink } else { fill },
    tracking: -0.5pt,
    body,
  )
]]

// A section heading inside a chapter. `outlined: true`: a bookmark pane for a
// 200-page book is only useful if it can be taken two levels deep, and the
// contents page is built from the same headings, so one setting gives both.
#let section-heading-element(body, T, size: none) = heading(
  level: 2,
  numbering: none,
  outlined: true,
)[#block(width: 100%, breakable: false, above: 0pt, below: 0pt)[
  #set par(justify: false, first-line-indent: 0em, leading: (if size == none { T.h2-size } else { size }) * 1.16)
  #text(
    font: T.heading-font,
    size: if size == none { T.h2-size } else { size },
    weight: "semibold",
    fill: T.ink,
    body,
  )
]]
