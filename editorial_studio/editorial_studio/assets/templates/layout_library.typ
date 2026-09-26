// ============================================================================
//  Editorial layout library
// ----------------------------------------------------------------------------
//  One function per layout family. Each takes the page dictionary, the document
//  dictionary and the resolved theme, and returns the page content.
//
//  Shape convention: a layout body computes its data in code mode, then emits a
//  single markup block. Statements outside that block are code-mode calls, so
//  they must not carry a `#` prefix — a stray one is a hard parse error.
// ============================================================================

#import "helpers.typ": *
#import "families.typ": *

// ── Cover ───────────────────────────────────────────────────────────────────
// The gilt frame is built as a full-height bordered block in normal flow
// rather than an overlay: `place(scope: "parent")` requires floating
// placement, and a floating box the size of the page pushes the text off it.
#let layout-cover(pg, doc, th) = {
  set page(margin: 15mm, fill: th.paper)
  let cd = pg.at("cover_data", default: (:))
  let title = str(cd.at("title", default: doc.at("title", default: "")))
  let subtitle = str(cd.at("subtitle", default: doc.at("subtitle", default: "")))
  let author = str(cd.at("author", default: doc.at("author", default: "")))
  let publisher = str(cd.at("publisher", default: ""))
  block(
    width: 100%,
    height: 100%,
    stroke: 0.7pt + th.brass,
    inset: 4mm,
  )[
    #block(width: 100%, height: 100%, stroke: 0.3pt + th.rule, inset: 12mm)[
      #v(24mm)
      #align(center)[
        #caps(th.kicker, th, color: th.terracotta, size: 8.5pt)
        #v(6mm)
        #line(length: 22mm, stroke: 1.6pt + th.brass)
        #v(9mm)
        #block(width: 122mm)[
          #set par(justify: false, first-line-indent: 0em, leading: 1.06em)
          #text(font: th.heading-font, size: 40pt, weight: "bold", fill: th.ink, tracking: -0.4pt)[#title]
        ]
        #if subtitle != "" [
          #v(7mm)
          #block(width: 108mm)[
            #set par(justify: false, first-line-indent: 0em, leading: 1.4em)
            #text(font: th.body-font, size: 13pt, style: "italic", fill: th.slate)[#subtitle]
          ]
        ]
        #v(9mm)
        #line(length: 22mm, stroke: 1.6pt + th.brass)
        #v(8mm)
        #if author != "" [
          #text(font: th.body-font, size: 12pt, fill: th.ink)[#author]
          #v(2.5mm)
        ]
        #if publisher != "" [ #caps(publisher, th, size: 8pt) ]
      ]
      #v(1fr)
      #align(center)[#caps("Field Edition", th, color: th.slate, size: 7.5pt)]
      #v(6mm)
    ]
  ]
}

// ── Title page ──────────────────────────────────────────────────────────────
#let layout-title-page(pg, doc, th) = {
  set page(margin: (top: 56mm, bottom: 30mm, left: 32mm, right: 32mm), fill: th.paper)
  let td = pg.at("title_data", default: (:))
  let title = str(td.at("title", default: doc.at("title", default: "")))
  let subtitle = str(td.at("subtitle", default: doc.at("subtitle", default: "")))
  let author = str(td.at("author", default: doc.at("author", default: "")))
  let publisher = str(td.at("publisher", default: ""))
  [
    #align(center)[
      #line(length: 30mm, stroke: 1.6pt + th.brass)
      #v(10mm)
      #block(width: 120mm)[
        #set par(justify: false, first-line-indent: 0em, leading: 1.1em)
        #text(font: th.heading-font, size: 30pt, weight: "bold", fill: th.ink, tracking: -0.3pt)[#title]
      ]
    ]
    #if subtitle != "" [
      #v(8mm)
      #align(center)[
        #block(width: 110mm)[
          #set par(justify: false, first-line-indent: 0em, leading: 1.42em)
          #text(font: th.body-font, size: 12.5pt, style: "italic", fill: th.slate)[#subtitle]
        ]
      ]
      #v(9mm)
      #align(center)[#line(length: 30mm, stroke: 1.6pt + th.brass)]
    ]
    #v(1fr)
    #align(center)[
      #set par(justify: false, first-line-indent: 0em, spacing: 2.5mm)
      #if author != "" [
        #text(font: th.body-font, size: 12pt, fill: th.ink)[#author]
        #v(6mm)
      ]
      #caps(publisher, th, size: 8pt)
    ]
  ]
}

// ── Copyright / imprint ─────────────────────────────────────────────────────
#let layout-copyright(pg, doc, th) = {
  set page(margin: (top: 56mm, bottom: 26mm, left: 34mm, right: 34mm), fill: th.paper)
  let blocks = pg.at("blocks", default: ())
  [
    #align(center)[
      #line(length: 24mm, stroke: 1.2pt + th.brass)
      #v(7mm)
      #caps("Imprint", th, color: th.slate, size: 8pt)
    ]
    #v(9mm)
    #block(width: 100%)[
      #set par(justify: true, first-line-indent: 0em, spacing: 0.7em, leading: 1.42em)
      #for b in blocks [
        #text(size: th.text-size * 0.9, fill: th.slate)[#str(b.at("content", default: ""))]
        #v(0.7em)
      ]
    ]
    #v(6mm)
    #hair-rule(th, thickness: 0.4pt)
    #v(3.5mm)
    #block(width: 100%)[
      #set par(justify: false, first-line-indent: 0em, spacing: 0.35em)
      #caps(doc.at("title", default: ""), th, color: th.terracotta, size: 7.5pt)
      #v(0.2em)
      #muted-note("Typeset in " + face-name(th.body-font) + ", " + face-name(th.heading-font) + " and " + face-name(th.mono-font) + ". Composed with Typst.", th)
    ]
  ]
}

// ── Table of contents ───────────────────────────────────────────────────────
// The contents page, built from the document's own headings.
//
// It is built from `query` rather than from `outline` for one concrete reason:
// an outline entry is rendered through the heading's own show rule, so a chapter
// title that the grid sets at 30pt on the page came out at 30pt in the contents
// as well and ran off the sheet. A contents entry is a reference line, so the
// entry is composed here at its own size and nothing else can change it.
#let toc-line(title, number, th, size: 10.5pt) = block(width: 100%, breakable: false)[
  #set par(justify: false, first-line-indent: 0em, leading: size * 1.34)
  #grid(
    columns: (1fr, auto),
    column-gutter: 6pt,
    align: (left, right),
    text(size: size, fill: th.ink)[#title],
    text(font: th.heading-font, size: size * 0.9, fill: th.slate)[#number],
  )
  #v(0.9em)
  #line(length: 100%, stroke: 0.3pt + th.rule)
  #v(0.9em)
]

// Two columns, so the page number cannot wrap under a long section title. Run
// inline it sits at the end of the title's text; when the title filled the
// column the number dropped to the next line at the left margin, on top of the
// next entry.
#let toc-section-line(title, number, th) = block(width: 100%, breakable: false)[
  #set par(justify: false, first-line-indent: 0em, leading: 1.3em)
  #grid(
    columns: (1fr, auto),
    column-gutter: 4pt,
    align: (left, right),
    text(size: 8.6pt, fill: th.slate)[#title],
    text(font: th.heading-font, size: 8.2pt, fill: th.brass)[#number],
  )
  #v(0.5em)
]

#let layout-toc(pg, doc, th) = {
  // The queries and the entries that depend on them are inside one `context`:
  // a page number is only known once the page is laid out, and Typst resolves
  // the whole block together.
  context {
    // Every heading in the document, not the ones before this page: the
    // contents is printed before the chapters it lists, so `.before(here())`
    // finds nothing at all and the page comes out empty.
    let chapters = query(heading.where(level: 1))
    let sections = query(heading.where(level: 2))
    [
    #block(width: 100%)[
      #set par(justify: false, first-line-indent: 0em)
      #caps(th.kicker, th, color: th.terracotta, size: 8pt)
      #v(0.4em)
      #text(font: th.heading-font, size: 30pt, weight: "bold", fill: th.ink)[Contents]
      #v(0.5em)
      #hair-rule(th, thickness: 1.4pt, color: th.brass)
      #v(1.1em)
    ]
    #for h in chapters [
      #toc-line(h.body, counter(page).display("1", at: h.location()), th)
    ]
    #block(width: 100%, breakable: false)[
      #set par(justify: false, first-line-indent: 0em)
      #v(1.1em)
      #hair-rule(th, thickness: 0.4pt)
      #v(0.9em)
      #caps("Sections", th, color: th.slate, size: 7.5pt)
      #v(0.3em)
    ]
    #let half = calc.ceil(sections.len() / 2)
    #grid(
      columns: (1fr, 1fr),
      column-gutter: 9mm,
      align: (left, left),
      ..sections.slice(0, half).map(h => toc-section-line(
        h.body, counter(page).display("1", at: h.location()), th,
      )),
      ..sections.slice(half, sections.len()).map(h => toc-section-line(
        h.body, counter(page).display("1", at: h.location()), th,
      )),
    )
    ]
  }
}

// ── Chapter opener ──────────────────────────────────────────────────────────
#let layout-chapter-opener(pg, doc, th) = {
  set page(margin: (top: 42mm, bottom: 24mm, left: 30mm, right: 26mm), fill: th.paper)
  let co = pg.at("chapter_opener_data", default: (:))
  let num = str(co.at("chapter_number", default: ""))
  let title = str(co.at("chapter_title", default: ""))
  let objectives = co.at("learning_objectives", default: ()).map(s => str(s))
  let epigraph = str(co.at("epigraph", default: ""))
  let plate = pg.at("illustration", default: (:))
  [
      #block(width: 100%, breakable: false)[
        #set par(justify: false, first-line-indent: 0em)
        #caps("Chapter", th, color: th.terracotta, size: 8.5pt)
        #v(0.6em)
        // An explicit leading keeps the display numeral's line box from
        // descending into the chapter title's ascenders.
        #block(width: 100%, breakable: false)[
          #set par(justify: false, first-line-indent: 0em, leading: 42pt)
          #text(
            font: th.heading-font,
            size: 54pt,
            weight: "bold",
            fill: th.cream-deep,
            tracking: -1pt,
          )[#num]
        ]
        #v(-0.3em)
        #hair-rule(th, thickness: 1.6pt, color: th.brass)
      ]
    // Registered heading: the display treatment comes from the show rule in
    // book_pages.typ; the outline and running head read it from the counter.
    #heading(level: 1)[#title]
    #if epigraph != "" [
      #v(0.2em)
      #block(width: 92%, breakable: false)[
        #set par(justify: false, first-line-indent: 0em, leading: 1.36em)
        #text(font: th.body-font, size: th.text-size + 1.5pt, style: "italic", fill: th.slate)[#epigraph]
      ]
    ]
    #if objectives.len() > 0 [
      #v(0.9em)
      #block(width: 100%, breakable: false)[
        #set par(justify: false, first-line-indent: 0em)
        #hair-rule(th, thickness: 0.4pt)
        #v(0.65em)
        #caps("In this chapter", th, color: th.terracotta, size: 7.5pt)
        #v(0.6em)
      ]
      #dash-list(objectives.slice(0, calc.min(3, objectives.len())), th)
    ]
    #if str(plate.at("path", default: "")) != "" [
      #v(1.1em)
      #figure-block(plate, th)
    ]
  ]
}

// ── Reading (default body page) ─────────────────────────────────────────────
#let layout-reading(pg, doc, th) = {
  let blocks = pg.at("blocks", default: ())
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #render-blocks(blocks, th)
  ]
}

// ── Two-column reading ──────────────────────────────────────────────────────
#let layout-reading-two-col(pg, doc, th) = {
  let blocks = pg.at("blocks", default: ())
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #set text(size: th.text-size * 0.95)
    #columns(2, gutter: 7mm)[
      #render-blocks(blocks, th)
    ]
  ]
}

// ── Image-led ───────────────────────────────────────────────────────────────
#let layout-image-led(pg, doc, th) = {
  let blocks = pg.at("blocks", default: ())
  let is-fig = b => str(b.at("type", default: "")) == "image_instruction"
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #for f in blocks.filter(is-fig) { figure-block(f.at("image", default: (:)), th) }
    #render-blocks(blocks.filter(b => not is-fig(b)), th)
  ]
}

// ── Case study ──────────────────────────────────────────────────────────────
#let layout-case-study(pg, doc, th) = {
  layout-reading(pg, doc, th)
}

// ── Worked example ──────────────────────────────────────────────────────────
#let layout-worked-example(pg, doc, th) = {
  layout-reading(pg, doc, th)
}

// ── Exercise ────────────────────────────────────────────────────────────────
#let layout-exercise(pg, doc, th) = {
  layout-reading(pg, doc, th)
}

// ── Checklist ───────────────────────────────────────────────────────────────
#let layout-checklist(pg, doc, th) = {
  let blocks = pg.at("blocks", default: ())
  let is-list = b => str(b.at("type", default: "")) in ("list", "list_item", "checklist")
  let items = ()
  for b in blocks.filter(is-list) {
    let src = b.at("list", default: (:)).at("items", default: ())
    if src.len() > 0 { items = items + src.map(s => str(s)) }
  }
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #render-blocks(blocks.filter(b => not is-list(b)), th)
    #v(0.3em)
    #block(width: 100%, fill: th.cream, inset: (left: 11pt, right: 10pt, top: 8pt, bottom: 9pt), radius: 2pt)[
      #set par(justify: true, first-line-indent: 0em, spacing: 0.4em, leading: th.lead)
      #caps("Checklist", th)
      #v(0.6em)
      #if items.len() > 0 {
        checklist(items, th)
      } else {
        text(size: th.text-size * 0.92, fill: th.slate)[No checklist items were scheduled for this spread.]
      }
    ]
  ]
}

// ── Process diagram ─────────────────────────────────────────────────────────
#let layout-process-diagram(pg, doc, th) = {
  let blocks = pg.at("blocks", default: ())
  let is-steps = b => str(b.at("type", default: "")) in ("process_diagram", "list", "list_item")
  let steps = ()
  for b in blocks.filter(is-steps) {
    let src = b.at("list", default: (:)).at("items", default: ())
    if src.len() > 0 { steps = steps + src.map(s => str(s)) }
  }
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #caps("Process", th, color: th.terracotta, size: 7.5pt)
    #v(0.4em)
    #process-diagram(steps, th)
    #render-blocks(blocks.filter(b => not is-steps(b)), th)
  ]
}

// ── Recap ───────────────────────────────────────────────────────────────────
#let layout-recap(pg, doc, th) = {
  let blocks = pg.at("blocks", default: ())
  let rd = pg.at("recap_data", default: (:))
  let points = rd.at("points", default: ()).map(s => str(s))
  let practice = rd.at("practice", default: ())
  let summary = str(rd.at("summary", default: ""))
  if points.len() == 0 {
    points = blocks
      .filter(b => str(b.at("type", default: "")) in ("paragraph", "case_study", "callout"))
      .map(b => str(b.at("content", default: "")))
      .map(s => if s.len() > 200 { s.slice(0, 197) + "…" } else { s })
  }
  block(width: 100%, breakable: false)[
    #set par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead)
    #caps("End of chapter", th, color: th.terracotta, size: 8pt)
    #v(0.45em)
    #text(font: th.heading-font, size: th.h1-size, weight: "bold", fill: th.ink)[#str(rd.at("title", default: "What to carry forward"))]
    #v(0.5em)
    #hair-rule(th, thickness: 1.2pt, color: th.brass)
    #v(1.1em)
    #if summary != "" { summary-note(summary, th) }
    #if practice.len() > 0 {
      v(1.3em)
      caps("What to practise", th, color: th.terracotta, size: 7.5pt)
      v(0.4em)
      for p in practice {
        practice-row(str(p.at("kind", default: "Exercise")), str(p.at("subject", default: "")), th)
      }
    }
    #if points.len() > 0 { recap-card(points, th) }
  ]
}

// ── Glossary ────────────────────────────────────────────────────────────────
#let layout-glossary(pg, doc, th) = {
  let entries = pg.at("glossary_data", default: (:)).at("entries", default: ())
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: 0.6em, leading: th.lead)
    #caps("Reference", th, color: th.terracotta, size: 8pt)
    #v(0.45em)
    #text(font: th.heading-font, size: th.h1-size, weight: "bold", fill: th.ink)[Glossary]
    #v(0.5em)
    #hair-rule(th, thickness: 1.2pt, color: th.brass)
    #v(1.1em)
    #if entries.len() > 0 {
      for e in entries {
        definition-block(str(e.at("term", default: "")), text(str(e.at("definition", default: ""))), th)
        v(0.7em)
      }
    } else {
      text(size: th.text-size, fill: th.slate)[No glossary terms were scheduled for this edition.]
    }
  ]
}

// ── References ──────────────────────────────────────────────────────────────
#let layout-references(pg, doc, th) = {
  let entries = pg.at("references_data", default: (:)).at("entries", default: ())
  block(width: 100%)[
    #set par(justify: true, first-line-indent: 0em, spacing: 0.5em, leading: th.lead)
    #caps("Reference", th, color: th.terracotta, size: 8pt)
    #v(0.45em)
    #text(font: th.heading-font, size: th.h1-size, weight: "bold", fill: th.ink)[Sources and further reading]
    #v(0.5em)
    #hair-rule(th, thickness: 1.2pt, color: th.brass)
    #v(1.2em)
    #if entries.len() > 0 {
      for e in entries {
        block(width: 100%, breakable: true, inset: (left: 1.2em))[
          #set par(justify: true, first-line-indent: -1.2em, spacing: 0.45em, leading: th.lead)
          #text(size: th.text-size * 0.94)[#str(e)]
        ]
      }
    } else {
      text(size: th.text-size, fill: th.slate)[No sources were recorded for this edition.]
    }
  ]
}

// ── Back cover ──────────────────────────────────────────────────────────────
#let layout-back-cover(pg, doc, th) = {
  set page(margin: 15mm, fill: th.ink)
  let bc = pg.at("back_cover_data", default: (:))
  block(width: 100%, height: 100%, stroke: 0.6pt + th.brass, inset: 4mm)[
    #block(width: 100%, height: 100%, inset: 12mm)[
      #v(58mm)
      #align(center)[
        #line(length: 20mm, stroke: 1.4pt + th.brass)
        #v(8mm)
        #block(width: 112mm)[
          #set par(justify: false, first-line-indent: 0em, leading: 1.16em)
          #text(font: th.heading-font, size: 19pt, weight: "bold", fill: th.ink-on-dark)[#str(doc.at("title", default: ""))]
        ]
        #v(7mm)
        #block(width: 94mm)[
          #set par(justify: false, first-line-indent: 0em, leading: 1.42em)
          #text(font: th.body-font, size: 10.5pt, style: "italic", fill: th.dark-note)[#str(bc.at("text", default: ""))]
        ]
      ]
      #v(1fr)
      #align(center)[#caps(th.kicker, th, size: 7.5pt)]
      #v(6mm)
    ]
  ]
}

// ── Composed page design families ───────────────────────────────────────────
// The sixteen editorial geometries live in page_families.typ. They are
// registered here alongside the original reading layouts so a page that falls
// back to a plain measure still has a home, and so the renderer can address any
// family by name.
#import "page_families.typ": (
  layout-minimal-editorial,
  layout-opener-split,
  layout-opener-stacked,
  layout-opener-vertical,
  layout-opener-centered,
  layout-dark-feature-opener,
  layout-asymmetric-grid,
  layout-text-visual-split,
  layout-framed-feature,
  layout-full-width-feature,
  layout-case-study-editorial,
  layout-worked-example-page,
  layout-workbook-exercise,
  layout-checklist-page,
  layout-pull-quote-page,
  layout-diagram-page,
  layout-data-table-page,
  layout-recap-plan-page,
  layout-reference-page,
)

// ── Registry ────────────────────────────────────────────────────────────────
// Keys must match the strings emitted by typst_renderer.layout_function_map.
#let layout-functions = (
  "cover": layout-cover,
  "title-page": layout-title-page,
  "copyright": layout-copyright,
  "toc": layout-toc,
  "chapter-opener": layout-chapter-opener,
  "reading": layout-reading,
  "reading-two-col": layout-reading-two-col,
  "image-led": layout-image-led,
  "case-study": layout-case-study,
  "worked-example": layout-worked-example,
  "checklist": layout-checklist,
  "process-diagram": layout-process-diagram,
  "exercise": layout-exercise,
  "recap": layout-recap,
  "glossary": layout-glossary,
  "references": layout-references,
  "back-cover": layout-back-cover,

  // Editorial design families (A–P).
  "minimal-editorial": layout-minimal-editorial,
  "opener-split": layout-opener-split,
  "opener-stacked": layout-opener-stacked,
  "opener-vertical": layout-opener-vertical,
  "opener-centered": layout-opener-centered,
  "dark-feature-opener": layout-dark-feature-opener,
  "asymmetric-grid": layout-asymmetric-grid,
  "text-visual-split": layout-text-visual-split,
  "framed-feature": layout-framed-feature,
  "full-width-feature": layout-full-width-feature,
  "case-study-editorial": layout-case-study-editorial,
  "worked-example-page": layout-worked-example-page,
  "workbook-exercise": layout-workbook-exercise,
  "checklist-page": layout-checklist-page,
  "pull-quote-page": layout-pull-quote-page,
  "diagram-page": layout-diagram-page,
  "data-table-page": layout-data-table-page,
  "recap-plan-page": layout-recap-plan-page,
  "reference-page": layout-reference-page,
)

// Families whose geometry is a fixed frame: the renderer must not hand them
// more text than the frame can hold.
#let fixed-geometry-families = (
  "framed-feature",
  "case-study-editorial",
  "diagram-page",
  "pull-quote-page",
)

// ── The grid families ───────────────────────────────────────────────────────
// The page compositions in families.typ, registered on the grid. They are
// reachable under two vocabularies: their own names, and the renderer's
// existing family keys. The second mapping is deliberate -- the planner, the
// capacity model, the landscape rules and the QA thresholds are all written
// against those keys, and re-pointing a key is a much smaller and much more
// reviewable change than re-deriving the whole planner.
//
// Where a key has no honest grid equivalent it keeps its legacy composition, and
// that is recorded rather than papered over: `framed-feature` and
// `text-visual-split` are still the design_system families.
#let grid-families = (
  "chapter-opener-ink": grid-family(chapter-opener-ink),
  "chapter-opener-marginal": grid-family(chapter-opener-marginal),
  "chapter-body": grid-family(chapter-body),
  "body-marginalia": grid-family(body-marginalia),
  "body-figure": grid-family(body-figure),
  "feature-quote": grid-family(feature-quote),
  "case-study-grid": grid-family(case-study),
  "worked-example-grid": grid-family(worked-example),
  "workbook-grid": grid-family(workbook),
  "checklist-grid": grid-family(checklist-page),
  "diagram-grid": grid-family(diagram-page),
  "data-table-grid": grid-family(data-table),
  "recap-grid": grid-family(recap),
  "reference-grid": grid-family(reference),

  // The renderer's vocabulary, re-pointed at the grid.
  "reading": grid-family(chapter-body),
  "minimal-editorial": grid-family(body-marginalia),
  "asymmetric-grid": grid-family(body-figure),
  // These three were the last body families still resolving to `layout-functions`,
  // which is the pre-grid composition set. Reaching them meant a body page was
  // typeset by the design_system theme -- PT Serif/PT Sans body, and, for
  // `full-width-feature`, a 297mm landscape sheet -- while its neighbours were set
  // on the grid in Source. Seven case-study pages came out that way: a short
  // paragraph in the wrong typeface on a rotated sheet in a portrait book. Each
  // key now names the grid family that already composes the same geometry.
  "full-width-feature": grid-family(body-figure),
  "framed-feature": grid-family(feature-quote),
  "text-visual-split": grid-family(body-marginalia),
  "image-led": grid-family(diagram-page),
  "case-study-editorial": grid-family(case-study),
  "worked-example-page": grid-family(worked-example),
  "workbook-exercise": grid-family(workbook),
  "checklist-page": grid-family(checklist-page),
  "pull-quote-page": grid-family(feature-quote),
  "diagram-page": grid-family(diagram-page),
  "data-table-page": grid-family(data-table),
  "recap-plan-page": grid-family(recap),
  "reference-page": grid-family(reference),
  "opener-split": grid-family(chapter-opener-marginal),
  "opener-stacked": grid-family(chapter-opener-marginal),
  "opener-vertical": grid-family(chapter-opener-marginal),
  "opener-centered": grid-family(chapter-opener-marginal),
  "dark-feature-opener": grid-family(chapter-opener-ink),
)

#let resolve-layout(name) = {
  let key = str(name)
  if key.starts-with("layout-") { key = key.slice(7) }
  grid-families.at(key, default: layout-functions.at(key, default: layout-reading))
}
