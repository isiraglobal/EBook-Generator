// ============================================================================
//  families.typ — the book's page compositions
// ============================================================================
//
//  Thirteen compositions, all on the grid in `grid.typ`. What distinguishes
//  them is not decoration: it is which columns the content occupies, how many
//  of them, whether the sheet is portrait or landscape, and whether the page
//  is paper or ink. A page that changes one of those reads as a different page
//  of the same book; a page that changes only its font size does not.
//
//  The families, in the order the planner reaches for them:
//
//    A  chapter-opener-ink      full-bleed ink, numeral, title, own light foot
//    B  chapter-opener-marginal  paper, numeral set in the margin column
//    C  chapter-body            the reading page: one measure, nothing else
//    D  body-marginalia         9 columns of text + a note in the margin
//    E  body-figure             7 columns of text + 5 columns of figure
//    F  feature-quote           a quotation across 8 columns, attribution out
//    G  case-study              a case with a scenario panel and a verdict
//    H  worked-example          inputs, a numbered calculation, a result
//    J  workbook                a task and its ruled response area
//    K  checklist-page               an action list in two columns
//    L  diagram                 a process across the full measure
//    M  data-table              a landscape sheet
//    N  recap                   the chapter's closing spread
//    O  reference               glossary and sources
//
//  Rules that hold for every family here:
//
//  · No family writes a width. It writes a span, and `grid.typ` resolves it.
//  · No family writes vertical space in points. It uses `bl()`, a multiple of
//    the baseline pitch, so a family cannot drift off the rhythm.
//  · No family sets a page size. The plan owns the sheet; a family sets only
//    the fill and the margins it needs.
//  · A component that cannot fit moves whole. There is no fixed-height box
//    anywhere in this file that holds real text.
// ============================================================================

// Import order matters and is deliberate. A star-import lets a later module
// shadow an earlier binding of the same name, so the newest definition has to be
// the one we want: `chrome.typ` last, because its grid-native `figure-block`
// and `opener-objectives` must win over the design_system-era ones of the same
// name that arrive through `content.typ` and `helpers.typ`.
#import "grid.typ": *
#import "content.typ": *
#import "helpers.typ": *
#import "chrome.typ": *

// ============================================================================
//  Shared parts
// ============================================================================

// A section heading: the sans at section size, on the grid, with a short
// terracotta rule under it. This is the only heading style in the book, and it
// is used identically in every family, so a section always looks the same
// wherever it appears.
#let section-heading(body, T) = block(
  width: 100%,
  breakable: false,
  above: T.space-before-head,
  below: T.space-after-head,
)[
  #section-heading-element(body, T)
  #v(0.3em)
  #line(length: 13mm, stroke: rule-strength(T, level: "minor"))
]

// A run of body text in the measure. One definition, used everywhere, so the
// justification, the indent and the leading of body text are the same on every
// page of the book.
#let prose(body, T, indent: false) = block(width: 100%)[
  #set par(
    justify: true,
    leading: T.lead,
    spacing: T.par-space,
    first-line-indent: if indent { 1.1em } else { 0em },
  )
  #body
]

// A figure: the artwork in its span, and the caption beneath it in the caption
// face, left-aligned, at most four lines. The caption is what makes a
// generated diagram look like a diagram and not like decoration, so it is never
// omitted and never abbreviated to a label.
#let figure-panel(plate, caption, T, width: 100%) = {
  let path = if plate == none { "" } else { str(plate.at("path", default: "")) }
  block(width: width)[
    #if path != "" [
      #box(
        width: 100%,
        fill: T.paper-warm,
        stroke: 0.5pt + T.rule,
        inset: 0pt,
        clip: true,
      )[#image(path, width: 100%, fit: "contain")]
      #v(T.space-tight)
    ]
    #block(width: 100%, breakable: false)[
      #set par(justify: false, first-line-indent: 0em, leading: 1.34em)
      #text(font: T.heading-font, size: T.caption-size, fill: T.slate, caption)
    ]
  ]
}

// The ruled response area of a workbook spread. The rules are the page's only
// "content" below the prompt, so they are the reason a workbook page is not
// underfilled: they are ink, they span the measure, and the QA pass measures
// them.
#let response-area(rules, T, gap: 13pt) = block(width: 100%, breakable: false)[
  #for _ in range(rules) [
    #v(gap, weak: true)
    #line(length: 100%, stroke: 0.45pt + T.rule)
  ]
]

// ============================================================================
//  A · Chapter opener, full-bleed ink
// ============================================================================
//
//  Three of twelve. The only full-bleed page in the book, and the only one that
//  draws its own running foot, because the book's chrome is slate on paper and
//  would vanish. The numeral is set in the margin column so the title can take
//  the full measure; a numeral behind the title is a watermark, and a watermark
//  is not what an opener is for.
#let chapter-opener-ink(pg, doc, T) = {
  set page(
    fill: T.ink-deep,
    header: none,
    footer: none,
  )
  // A dark sheet takes a paper-coloured chapter title.
  chapter-ink.update(T.paper)
  let co = opener-of(pg)
  let num = str(co.at("chapter_number", default: ""))
  let title = str(co.at("chapter_title", default: ""))
  let objectives = first-n(co.at("learning_objectives", default: ()).map(s => str(s)), 3)
  // The block is given the full type area so the two `place` calls below have
  // the whole of it to place into: a composition whose regions are positioned
  // rather than flowed is only anchored if the region it sits in is full height.
  block(width: 100%, height: 100%, breakable: false)[
    #set par(justify: false, first-line-indent: 0em)
    #place(top + left, dy: bl(3), block(width: 100%)[
      #label-text("Chapter " + num, fill: T.brass, size: T.meta-size)
      #v(bl(0.5))
      #line(length: 22mm, stroke: 1.4pt + T.brass)
      #v(bl(1))
      #chapter-heading(title, T)
      #v(bl(0.75))
      #line(length: 100%, stroke: 0.4pt + rgb("#3A342C"))
      #v(bl(1))
      #block(width: span(0, 8))[
        #set par(justify: true, first-line-indent: 0em, leading: T.lead * 1.25)
        #text(font: T.body-font, size: T.lead-size, fill: rgb("#C8C1B5"))[
          #first-sentence(co.at("epigraph", default: (:)))
        ]
      ]
    ])
    // `#place`, with the hash: inside a content block a bare `place(...)` is
    // markup, and it was being typeset as the words "place(bottom + left, ...)"
    // in the middle of the chapter's opening page.
    #if objectives.len() > 0 [
      #place(bottom + left, dy: -bl(1), block(width: span(0, 8))[
        #set par(justify: false, first-line-indent: 0em, leading: T.lead)
        #for o in objectives [
          #dash-row(o, T, size: T.small-size, color: T.brass)
          #v(T.space-tight)
        ]
      ])
    ]
    // A quiet mark, placed in the fore-edge margin, so a dark sheet is not just
    // a dark sheet with text on it.
    #place(bottom + right, dx: -T.gutter, dy: bl(1), contour-motif(T, rows: 2, cols: 9))
  ]
}

// ============================================================================
//  B · Chapter opener, paper with a marginal numeral
// ============================================================================
//
//  The working opener. The numeral is huge and sits in the margin column, the
//  title takes nine columns, and the rule between them is the only division on
//  the page. No fill, no panel, no frame.
#let chapter-opener-marginal(pg, doc, T) = {
  chapter-ink.update(T.ink)
  let co = opener-of(pg)
  let num = str(co.at("chapter_number", default: ""))
  let title = str(co.at("chapter_title", default: ""))
  let objectives = first-n(co.at("learning_objectives", default: ()).map(s => str(s)), 3)
  let plate = figure-of(pg)
  // Three rows over the full type area: the title at the head, an elastic row,
  // and the objectives and plate at the foot. The slack is absorbed by the
  // middle row rather than left as a hole at the bottom, which is what makes an
  // opener read as a composed page instead of a page with a title on it.
  block(width: 100%, height: 100%, breakable: false)[
    #set par(justify: false, first-line-indent: 0em, leading: T.lead)
    #grid(
      rows: (auto, 1fr, auto),
      row-gutter: bl(1.5),
      columns: (1fr,),
      // Row one: the title in the measure, the numeral in the margin.
      grid(
        columns: (span(0, 9), T.margin-column),
        column-gutter: T.gutter,
        align: (left, top),
        block(width: span(0, 9), breakable: false)[
          #v(bl(3))
          #label-text("Chapter " + num, fill: T.terracotta)
          #v(bl(0.5))
          #chapter-heading(title, T)
          #v(bl(0.75))
          #line(length: 26mm, stroke: rule-strength(T, level: "major"))
          #v(bl(1))
          #block(width: span(0, 7), breakable: false)[
            #set par(justify: true, first-line-indent: 0em, leading: T.lead * 1.25)
            #text(font: T.body-font, size: T.lead-size, fill: T.slate)[
              #first-sentence(co.at("epigraph", default: (:)))
            ]
          ]
        ],
        block(width: T.margin-column, breakable: false)[
          #text(
            font: T.heading-font,
            size: T.giant-size,
            weight: "bold",
            fill: T.brass-tint,
            tracking: -2.5pt,
          )[#num]
        ],
      ),
      // Row two is the elastic one: nothing is written into it.
      none,
      // Row three: a hairline, then what the chapter will enable and the plate
      // that carries the chapter's argument.
      block(width: 100%, breakable: false)[
        #divider(T, level: "hair")
        #v(bl(1))
        #grid(
          columns: (span(0, 7), span(0, 5) - T.gutter),
          column-gutter: T.gutter,
          align: (left, top),
          block(width: span(0, 7), breakable: false)[
            #if objectives.len() > 0 [#opener-objectives(objectives, T)]
          ],
          if plate != none {
            figure-panel(plate, str(plate.at("caption", default: "")), T, width: span(0, 5) - T.gutter)
          },
        )
      ],
    )
  ]
}

// ============================================================================
//  C · The reading page
// ============================================================================
//
//  One measure of text, a hydra head and an outer folio. Nothing else. This is
//  the page that has to be invisible, and it is the page most of the book is
//  made of.
#let chapter-body(pg, doc, T) = {
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    #flow-blocks(blocks-of(pg), T, lead-drop-cap: true)
  ]
}

// ============================================================================
//  D · Body with marginalia
// ============================================================================
//
//  The same nine columns of text as the reading page, plus a note set in the
//  margin column. The measure is 9/12 of the full one, which is 110mm -- still
//  inside the 60-75 character band, so the justification stays clean.
#let body-marginalia(pg, doc, T) = {
  let blocks = blocks-of(pg)
  let notes = blocks
    .filter(b => is-type(b, ("callout")))
    .map(b => str(b.at("callout", default: (:)).at("text", default: "")))
  let rest = blocks.filter(b => not is-type(b, ("callout")))
  let note = if notes.len() > 0 { notes.first() } else { "" }
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    #if note == "" { flow-blocks(rest, T) } else { with-margin-note(flow-blocks(rest, T), note, T) }
  ]
}

// ============================================================================
//  E · Body with a figure
// ============================================================================
//
//  Seven columns of text and five of figure, side by side, on the same
//  baseline. The figure is capped at the type height so it can never be the
//  reason the page overflows; if the artwork is taller it is contained, not
//  cropped.
#let body-figure(pg, doc, T) = {
  let blocks = blocks-of(pg)
  let head = lead-heading(blocks)
  let plate = figure-of(pg)
  let body = without-head(blocks, head)
  let fig-h = T.type-height - bl(2)
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    #if head != "" [#section-heading(head, T) #v(-T.space-after-head)]
    #grid(
      columns: (span(0, 7), span(0, 5)),
      column-gutter: T.gutter,
      align: (left, top),
      block(width: span(0, 7))[#flow-blocks(body, T)],
      block(width: span(0, 5), breakable: false)[
        #figure-block(plate, T, height: fig-h, tail: 0pt)
      ],
    )
  ]
}

// ============================================================================
//  F · Feature quote
// ============================================================================
//
//  A quotation across eight columns with the attribution and the source set
//  small in the margin column. No panel, no tint, no centred block: a pull
//  quote that is centred and boxed is a poster, and this is a book.
#let feature-quote(pg, doc, T) = {
  let q = quote-of(pg)
  // A framed feature is the page's set-off moment, not its whole content. The
  // rest of the page used to be discarded here, so a framed-feature page whose
  // blocks were a heading and a case study printed neither.
  let rest = blocks-of(pg).filter(b => not is-type(b, ("quotation", "pull_quote", "feature_quote")))
  block(width: 100%, breakable: true)[
    #v(bl(2))
    #grid(
      columns: (span(0, 8), T.margin-column),
      column-gutter: T.gutter,
      align: (left, top),
      block(width: span(0, 8), breakable: true)[
        #set par(justify: true, first-line-indent: 0em, leading: T.lead * 1.1)
        #text(font: T.body-font, size: T.lead-size * 1.5, style: "italic", fill: T.ink)[
          #q.at("text", default: "")
        ]
        #v(bl(0.75))
        #line(length: 18mm, stroke: rule-strength(T, level: "minor"))
      ],
      block(width: T.margin-column, breakable: false)[
        #v(bl(1))
        #set par(justify: false, first-line-indent: 0em, leading: 1.3em)
        #text(font: T.heading-font, size: T.small-size, weight: "semibold", fill: T.ink)[
          #q.at("attribution", default: "")
        ]
        #v(0.2em)
        #text(font: T.heading-font, size: T.caption-size, fill: T.slate)[
          #q.at("source", default: "")
        ]
      ],
    )
    #if rest.len() > 0 [
      #v(T.space-block)
      #flow-blocks(rest, T)
    ]
  ]
}

// ============================================================================
//  G · Case study
// ============================================================================
//
//  A case is a piece of argument, so it is set as an argument: the situation in
//  a tinted panel, the analysis as ordinary body text, and a verdict at the foot
//  separated by a rule. The case number sits in the margin column, so the
//  measure is unbroken.
#let case-study(pg, doc, T) = {
  let blocks = blocks-of(pg)
  let head = lead-heading(blocks)
  let cs = blocks
    .filter(b => is-type(b, ("case_study")))
    .map(b => b.at("case_study", default: (:)))
  let body = blocks.filter(b => not is-type(b, ("case_study")))
  // A short case reads as one argument on one page, and a numbered margin gives
  // it its place in the run. A long one -- a full underwriting, a diligence
  // narrative -- has to be allowed to run overleaf instead of being clipped by a
  // frame sized for the short case, so the numbered plate is dropped and the
  // measure goes full width once the case stops fitting a single sheet.
  let long_case = cs.len() > 0 and (
    str(cs.first().at("context", default: "")).len() > 1400
    or body.len() > 6
  )
  let case = if cs.len() > 0 { cs.first() } else { (:) }
  let num = str(pg.at("case_index", default: ""))
  let cols = if long_case { (span(0, 12),) } else { (span(0, 10), T.margin-column) }
  let main-cell = block(width: 100%, breakable: true)[
    #if head != "" [#section-heading(head, T) #v(-T.space-after-head)]
    #label-text("Case study" + (if num != "" { " " + num } else { "" }), fill: T.terracotta)
    #v(T.space-tight)
    #minor-heading(str(case.at("title", default: "")), T)
    #v(T.space-tight)
    #panel([
      #label-text("Situation", fill: T.slate, size: T.micro-size)
      #v(0.2em)
      #str(case.at("context", default: ""))
    ], T)
    #v(T.space-tight)
    #if str(case.at("analysis", default: "")) != "" [
      #label-text("Analysis", fill: T.slate, size: T.micro-size)
      #v(0.15em)
      #str(case.at("analysis", default: ""))
      #v(T.space-tight)
    ]
    #if str(case.at("decision", default: "")) != "" [
      #label-text("Decision", fill: T.slate, size: T.micro-size)
      #v(0.15em)
      #str(case.at("decision", default: ""))
      #v(T.space-tight)
    ]
    #v(T.space-block)
    #if body.len() > 0 [#flow-blocks(body, T)]
    #v(T.space-block)
    #divider(T, level: "minor")
    #v(T.space-tight)
    #label-text("What to carry forward", fill: T.terracotta, size: T.micro-size)
    #v(0.2em)
    #text(size: T.small-size, fill: T.ink)[#str(case.at("lesson", default: ""))]
    // Every case in this book is constructed for teaching. The page says so, so
    // a reader cannot mistake an illustrative scenario for a documented deal.
    #if str(case.at("basis", default: "")) != "" [
      #v(T.space-tight)
      #text(size: T.micro-size, fill: T.slate, style: "italic")[
        #str(case.at("basis", default: ""))
      ]
    ]
  ]
  let plate-cell = block(width: T.margin-column, breakable: false)[
    #v(bl(1.5))
    #text(
      font: T.heading-font,
      size: T.giant-sm-size,
      weight: "bold",
      fill: T.brass-tint,
      tracking: -1.5pt,
    )[#num]
  ]
  // The numbered plate is a one-column grid: a long case spends the whole
  // twelve-column measure on its argument instead of holding a margin back for a
  // numeral it will not reach the bottom of.
  let cells = (main-cell,) + if long_case { () } else { (plate-cell,) }
  block(width: 100%, breakable: true)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    #grid(
      columns: cols,
      column-gutter: T.gutter,
      align: (left, top),
      ..cells,
    )
  ]
}

// ============================================================================
//  H · Worked example
// ============================================================================
//
//  The only page with three distinct regions, and the only one that reads as a
//  calculation: the inputs across the top in a tinted strip, the procedure as a
//  numbered list in the measure, and the result in a panel at the foot. The
//  three regions share the grid, so the page is one composition rather than
//  three stacked boxes.
#let worked-example(pg, doc, T) = {
  let blocks = blocks-of(pg)
  let head = lead-heading(blocks)
  // The page's own calculation is the first worked example. Any further one that
  // shares the page used to be filtered out of `others` along with the first and
  // never printed, so a second example on the same page was silently lost; they
  // go to the body flow below the calculation instead.
  let ex_blocks = blocks.filter(b => is-type(b, ("worked_example")))
  let ex = ex_blocks
    .map(b => b.at("worked_example", default: (:)))
    .first(default: (:))
  let spill = if ex_blocks.len() > 1 { ex_blocks.slice(1) } else { () }
  let others = without-head(
    blocks.filter(b => not is-type(b, ("worked_example"))) + spill, head
  )
  let num = str(pg.at("example_index", default: ""))
  let problem = str(ex.at("problem", default: ""))
  let given = ex.at("given", default: ())
  let steps = ex.at("steps", default: ())
  let answer = str(ex.at("answer", default: ""))
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    // Title band: the number in the margin column, the title in the measure.
    #grid(
      columns: (span(0, 10), T.margin-column),
      column-gutter: T.gutter,
      align: (left, top),
      block(width: span(0, 10), breakable: false)[
        #label-text("Worked example" + (if num != "" { " " + num } else { "" }), fill: T.terracotta)
        #v(T.space-tight)
        #minor-heading(
          if head != "" { head } else { str(ex.at("title", default: "")) },
          T,
        )
      ],
      block(width: T.margin-column, breakable: false)[
        #text(
          font: T.heading-font,
          size: T.giant-sm-size,
          weight: "bold",
          fill: T.brass-tint,
          tracking: -1.5pt,
        )[#num]
      ],
    )
    #v(T.space-tight)
    // Region one: the problem, and the inputs beneath it.
    #block(width: 100%, breakable: false)[
      #label-text("Problem", fill: T.slate, size: T.micro-size)
      #v(0.2em)
      #text(size: T.lead-size, fill: T.ink)[#problem]
    ]
    #if given.len() > 0 [
      #v(T.space-tight)
      #grid(
        columns: (1fr,) * calc.min(3, given.len()),
        column-gutter: T.gutter,
        inset: 5pt,
        fill: T.slate-tint,
        stroke: (top: 0.4pt + T.rule, bottom: 0.4pt + T.rule),
        ..given.map(g => block(width: 100%, breakable: false)[
          #set par(justify: false, first-line-indent: 0em, leading: 1.3em)
          #text(font: T.heading-font, size: T.micro-size, fill: T.slate, tracking: 0.8pt)[
            #upper(str(g.at("label", default: "")))
          ]
          #v(0.2em)
          #text(size: T.small-size, weight: "semibold", fill: T.ink)[#str(g.at("value", default: ""))]
        ]),
      )
    ]
    // Region two: the procedure.
    #if steps.len() > 0 [
      #v(T.space-block)
      #label-text("Calculation", fill: T.slate, size: T.micro-size)
      #v(0.3em)
      #for (i, step) in steps.enumerate() [
        #numbered-row(i + 1, str(step), T, size: T.small-size)
        #v(T.space-tight)
      ]
    ]
    // Region three: the result.
    #if answer != "" [
      #v(T.space-tight)
      #panel([
        #label-text("Result", fill: T.terracotta, size: T.micro-size)
        #v(0.2em)
        #text(size: T.lead-size, fill: T.ink)[#answer]
      ], T, accent: T.terracotta)
    ]
    #if others.len() > 0 [
      #v(T.space-block)
      #divider(T, level: "hair")
      #v(T.space-tight)
      #flow-blocks(others, T)
    ]
  ]
}

// ============================================================================
//  J · Workbook
// ============================================================================
//
//  A task and the room to answer it. The number is in the margin column, the
//  prompt is in the measure, and the response area is ruled across the full
//  measure below a rule that stops at the margin gutter -- so the answer space
//  reads as a ruled field and not as a stack of loose lines.
#let workbook(pg, doc, T) = {
  let blocks = blocks-of(pg)
  let exs = blocks.filter(b => is-type(b, ("exercise")))
  let rest = blocks.filter(b => not is-type(b, ("exercise")))
  let idx = int(pg.at("exercise_index", default: 1))
  let rules = int(pg.at("answer_rules", default: 8))
  let fields = exs.map(e => e.at("exercise", default: (:)))
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    #grid(
      columns: (span(0, 10), T.margin-column),
      column-gutter: T.gutter,
      align: (left, top),
      block(width: span(0, 10), breakable: false)[
        #label-text("Workbook " + str(idx), fill: T.terracotta)
        #v(T.space-tight)
        #line(length: 26mm, stroke: rule-strength(T, level: "major"))
      ],
      block(width: T.margin-column, breakable: false)[
        #text(
          font: T.heading-font,
          size: T.h3-size,
          weight: "bold",
          fill: T.brass-tint,
          tracking: -0.5pt,
        )[W#idx]
      ],
    )
    #if rest.len() > 0 [
      #v(T.space-block)
      #flow-blocks(rest, T)
    ]
    #for (n, ex) in fields.enumerate() [
      #v(T.space-block)
      #grid(
        columns: (8mm, span(0, 9) - 8mm - T.gutter, T.margin-column),
        column-gutter: T.gutter,
        align: (left, left, top),
        text(
          font: T.heading-font,
          size: T.small-size,
          weight: "bold",
          fill: T.brass,
        )[#(n + 1).],
        block(width: span(0, 9) - 8mm - T.gutter, breakable: false)[
          #set par(justify: true, first-line-indent: 0em, leading: T.lead)
          #let kind = str(ex.at("kicker", default: "Task")).trim()
          #let title = str(ex.at("title", default: "")).trim()
          #if kind != "" [
            #label-text(kind, fill: T.slate, size: T.micro-size)
            #v(0.2em)
          ]
          #if title != "" [
            #text(font: T.heading-font, size: T.lead-size, weight: "semibold", fill: T.ink)[#title]
            #v(0.25em)
          ]
          #let instr = str(ex.at("instructions", default: "")).trim()
          #let question = str(ex.at("question", default: "")).trim()
          #if instr != "" [ text(size: T.text-size, fill: T.ink)[#instr] #v(0.2em) ]
          #if question != "" [ text(style: "italic", fill: T.ink)[#question] #v(0.2em) ]
          #let hints = ex.at("hints", default: ())
          #if hints.len() > 0 [
            #text(font: T.heading-font, size: T.caption-size, fill: T.slate)[#hints.join("  ")]
            #v(0.2em)
          ]
        ],
        // The hint column: a marginal note beside each task, which is what
        // turns a form into a workbook.
        block(width: T.margin-column, breakable: false)[
          #let hints = ex.at("hints", default: ())
          #if hints.len() > 0 [
            #set par(justify: false, first-line-indent: 0em, leading: 1.3em)
            #text(font: T.heading-font, size: T.caption-size, fill: T.slate)[
              #hints.join(" · ")
            ]
          ]
        ],
      )
      #v(T.space-tight)
      #divider(T, width: 100%, level: "hair")
      #v(T.space-tight)
      #response-area(rules, T, gap: 13pt)
    ]
  ]
}

// ============================================================================
//  K · Checklist
// ============================================================================
//
//  An action list in two columns of six, with the count in the margin column.
//  Two columns is the only place in this book where body text is set in
//  columns: the list is short enough that a single measure would leave half the
//  page empty, and the items are short enough that the narrower column does not
//  need a hyphen to stay justified.
#let checklist-page(pg, doc, T) = {
  let blocks = blocks-of(pg)
  let head = lead-heading(blocks)
  // Typst has no `flatMap`, so the items are collected with a loop. A checklist
  // block is the only source, and there may be several on one page.
  let items = ()
  for b in blocks {
    if is-type(b, ("checklist")) {
      for item in b.at("checklist", default: (:)).at("items", default: ()) {
        items = items + (str(item),)
      }
    }
  }
  let body = without-head(blocks.filter(b => not is-type(b, ("checklist"))), head)
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    #if head != "" [#section-heading(head, T) #v(-T.space-after-head)]
    #grid(
      columns: (span(0, 9), T.margin-column),
      column-gutter: T.gutter,
      align: (left, top),
      block(width: span(0, 9), breakable: false)[
        #let rows = ()
        #for item in items {
          rows = rows + (block(width: 100%, breakable: false)[
            #check-row(item, T)
          ],)
        }
        #two-column-list(rows, T)
        #if body.len() > 0 [
          #v(T.space-block)
          #flow-blocks(body, T)
        ]
      ],
      block(width: T.margin-column, breakable: false)[
        #v(bl(0.5))
        #text(
          font: T.heading-font,
          size: T.giant-sm-size,
          weight: "bold",
          fill: T.brass-tint,
          tracking: -1.5pt,
        )[#items.len()]
        #v(0.2em)
        #label-text("items", fill: T.slate, size: T.micro-size)
      ],
    )
  ]
}

// ============================================================================
//  L · Diagram
// ============================================================================
//
//  A process across the full measure, with the step count in the margin. The
//  artwork is capped at the type height so the diagram is the reason for the
//  page and never the reason the page overflows.
#let diagram-page(pg, doc, T) = {
  let blocks = blocks-of(pg)
  let head = lead-heading(blocks)
  let plate = figure-of(pg)
  let body = without-head(blocks.filter(b => not is-type(b, ("heading"))), head)
  let fig-h = T.type-height - bl(4)
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    #if head != "" [
      #grid(
        columns: (span(0, 9), T.margin-column),
        column-gutter: T.gutter,
        align: (left, top),
        block(width: span(0, 9), breakable: false)[
          #section-heading(head, T)
        ],
        block(width: T.margin-column, breakable: false)[
          #label-text("process", fill: T.terracotta, size: T.micro-size)
        ],
      )
    ]
    #v(T.space-tight)
    #block(width: 100%, breakable: false)[
      #figure-block(plate, T, height: fig-h, tail: 0pt)
    ]
    #if body.len() > 0 [
      #v(T.space-block)
      #grid(
        columns: (span(0, 9), T.margin-column),
        column-gutter: T.gutter,
        align: (left, top),
        block(width: span(0, 9))[#flow-blocks(body, T)],
        block(width: T.margin-column)[
          #divider(T, level: "minor")
        ],
      )
    ]
  ]
}

// ============================================================================
//  M · Data table, landscape
// ============================================================================
//
//  The only landscape sheet. A table needs the measure more than it needs a
//  portrait page, and a four-column comparison set at 110 characters will not
//  fit a portrait measure without either a 7pt face or a rotation. The sheet
//  size is the plan's; this family sets the fill and the running chrome only.
// One block per table cell, in row-major order, ready to splice into a `grid`.
// A cell is bounded: it holds a short value, and a long one is the data's fault
// rather than the layout's, so it breaks rather than overflows.
#let table-cells(rows, n, colw, T) = {
  let out = ()
  for r in rows {
    for c in r {
      out = out + (block(width: colw, breakable: false)[
        #set par(justify: false, first-line-indent: 0em, leading: 1.3em)
        #text(size: T.small-size, fill: T.ink)[#str(c)]
      ],)
    }
  }
  out
}

#let data-table(pg, doc, T) = {
  let blocks = blocks-of(pg)
  let head = lead-heading(blocks)
  let tables = blocks.filter(b => is-type(b, ("table")))
  let rest = without-head(blocks.filter(b => not is-type(b, ("table"))), head)
  let t = if tables.len() > 0 { tables.first().at("table", default: (:)) } else { (:) }
  let headers = t.at("headers", default: ())
  let rows = t.at("rows", default: ())
  let caption = t.at("caption", default: "")
  let n = headers.len()
  let colw = (T.measure-width - T.gutter * (n - 1)) / n
  block(width: 100%, breakable: false)[
    #set par(justify: false, first-line-indent: 0em, leading: T.lead)
    #if head != "" [
      #label-text("Reference", fill: T.terracotta)
      #v(T.space-tight)
      #display(head, T.h2-size, fill: T.ink, tracking: -0.3pt)
      #v(T.space-tight)
    ]
    #if headers.len() > 0 [
      // The header row is set in the sans, tracked out, over a brass tint, with
      // a full-weight rule under it. The body rows are separated by hairlines
      // and nothing else -- no zebra, no boxed cells, no vertical rules.
      #grid(
        columns: (colw,) * n,
        column-gutter: T.gutter,
        inset: (x: 4pt, y: 4pt),
        fill: (x, y) => if y == 0 { T.brass-tint } else { none },
        stroke: (_, y) => 0.4pt + T.rule,
        grid.header(..headers.map(h => block(width: colw)[
          #set par(justify: false, first-line-indent: 0em, leading: 1.25em)
          #text(
            font: T.heading-font,
            size: T.micro-size,
            weight: "semibold",
            fill: T.ink,
            tracking: 1.1pt,
          )[#upper(str(h))]
        ])),
        // The rows are spliced rather than mapped, because `grid` takes a flat
        // argument list and Typst has no `flatMap`.
        ..table-cells(rows, n, colw, T),
      )
    ]
    #if caption != "" [
      #v(T.space-tight)
      #block(width: 100%, breakable: false)[
        #set par(justify: false, first-line-indent: 0em, leading: 1.34em)
        #text(font: T.heading-font, size: T.caption-size, fill: T.slate)[#caption]
      ]
    ]
    #if rest.len() > 0 [
      #v(T.space-block)
      #flow-blocks(rest, T)
    ]
  ]
}

// ============================================================================
//  N · Recap
// ============================================================================
//
//  The chapter's closing page, in three regions across the grid: the summary in
//  the measure, the sections it covered in the second column, and the practice
//  it set in the margin. A recap that is a bulleted list of everything is a
//  recap nobody reads; this one states the point, the route, and the work.
#let recap(pg, doc, T) = {
  let d = pg.at("recap_data", default: (:))
  let summary = str(d.at("summary", default: ""))
  let points = flatten-strings(d.at("points", default: ()))
  let practice = flatten-strings(d.at("practice", default: ()))
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    #grid(
      columns: (span(0, 10), T.margin-column),
      column-gutter: T.gutter,
      align: (left, top),
      block(width: span(0, 10), breakable: false)[
        #label-text("Chapter recap", fill: T.terracotta)
        #v(T.space-tight)
        #display(str(d.at("title", default: "")), T.h2-size, fill: T.ink, tracking: -0.3pt)
        #v(T.space-tight)
        #divider(T, width: 26mm, level: "major")
        #v(T.space-block)
        #if summary != "" [
          #text(size: T.lead-size, fill: T.ink)[#summary]
          #v(T.space-block)
        ]
        #if points.len() > 0 [
          #label-text("What this chapter covered", fill: T.slate, size: T.micro-size)
          #v(0.3em)
          #let rows = ()
          #for p in points {
            rows = rows + (block(width: 100%, breakable: false)[
              #dash-row(p, T, size: T.small-size, color: T.brass)
              #v(T.space-tight)
            ],)
          }
          #two-column-list(rows, T)
        ]
      ],
      block(width: T.margin-column, breakable: false)[
        #v(bl(1.5))
        #divider(T, level: "minor")
        #v(0.4em)
        #label-text("Practise", fill: T.terracotta, size: T.micro-size)
        #v(0.3em)
        #set par(justify: false, first-line-indent: 0em, leading: 1.3em)
        #for task in practice [
          #text(font: T.heading-font, size: T.caption-size, fill: T.ink)[#task]
          #v(0.35em)
        ]
      ],
    )
  ]
}

// ============================================================================
//  O · Reference
// ============================================================================
//
//  Glossary and sources, in the measure, two columns for the glossary once it
//  is long enough to need them. Term and definition share a line, separated by
//  a dotted leader rather than a box.
#let reference(pg, doc, T) = {
  let is-glossary = str(pg.at("purpose", default: "")) == "glossary"
  let entries = if is-glossary {
    pg.at("glossary_data", default: (:)).at("entries", default: ())
  } else {
    pg.at("references_data", default: (:)).at("entries", default: ())
  }
  let declared-title = pg.at("references_data", default: (:)).at("title", default: "")
  let title = if is-glossary { "Glossary" } else if declared-title != "" { declared-title } else { "Sources and further reading" }
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, leading: T.lead, spacing: T.par-space)
    #label-text("Reference", fill: T.terracotta)
    #v(T.space-tight)
    #display(title, T.h2-size, fill: T.ink, tracking: -0.3pt)
    #v(T.space-tight)
    #divider(T, width: 26mm, level: "major")
    #v(T.space-block)
    #if is-glossary [
      #columns(2, gutter: T.gutter + 3mm)[
        #for e in entries [
          #block(width: 100%, breakable: false)[
            #set par(justify: true, first-line-indent: 0em, leading: 1.3em)
            #text(font: T.heading-font, size: T.small-size, weight: "semibold", fill: T.ink)[
              #str(e.at("term", default: ""))
            ]
            #v(0.15em)
            #text(size: T.small-size, fill: T.slate)[#str(e.at("definition", default: ""))]
            #v(T.space-tight)
            #line(length: 100%, stroke: 0.3pt + T.rule)
            #v(T.space-tight)
          ]
        ]
      ]
    ] else [
      #for (i, r) in entries.enumerate() [
        #grid(
          columns: (8mm, 1fr),
          column-gutter: 3mm,
          align: (left, left),
          text(
            font: T.heading-font,
            size: T.small-size,
            weight: "semibold",
            fill: T.brass,
          )[#(i + 1).],
          block(width: 1fr)[
            #set par(justify: true, first-line-indent: 0em, leading: 1.3em)
            #text(size: T.small-size, fill: T.ink)[#str(r)]
          ],
        )
        #v(T.space-tight)
        #divider(T, level: "hair")
        #v(T.space-tight)
      ]
    ]
  ]
}
