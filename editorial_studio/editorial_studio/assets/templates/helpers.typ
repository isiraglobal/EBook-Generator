// ============================================================================
//  Editorial component library
// ----------------------------------------------------------------------------
//  Every function below is a pure code expression. Branching always uses the
//  braced form (`if cond { ... } else { ... }`); the un-braced markup form
//  (`#if cond [x]` followed by a bare `else if`) is parsed as literal text and
//  leaks Typst source into the rendered page.
//
//  Theme values arrive through the `th` dictionary so this file stays
//  theme-agnostic; `theme()` resolves the defaults.
// ============================================================================

// ── Palette defaults (warm paper / ink / brass editorial system) ────────────
#let default-palette = (
  paper:      "#F7F3EC",
  ink:        "#1A1815",
  brass:      "#B08D57",
  terracotta: "#A0523D",
  slate:      "#6B6560",
  rule:       "#D9CFBF",
  cream:      "#EFE8DB",
  cream_deep: "#E4D9C6",
  green:      "#5C7A5C",
  warn_bg:    "#F6ECE6",
  panel_bg:   "#F3EDE3",
  panel_bg_2: "#F6F1E7",
  ink_on_dark: "#F7F3EC",
  dark_note:  "#C8BCA8",
)

// ── Dimension parsing (accepts "10.5pt", "10.5", "1.45em", "210mm") ────────
#let dim(value, fallback-pt) = {
  let s = str(value).trim()
  if s == "" { return fallback-pt }
  let ends-unit = s.ends-with("pt") or s.ends-with("em") or s.ends-with("mm") or s.ends-with("cm")
  eval(if ends-unit { s } else { s + "pt" }, mode: "code")
}

// ── Theme resolution ────────────────────────────────────────────────────────
#let theme(preset) = {
  let pal = preset.at("palette", default: (:))
  let pick = (name, fallback) => rgb(str(pal.at(name, default: fallback)))
  let size = dim(preset.at("text_size", default: "10.5pt"), 10.5pt)
  (
    paper: pick("paper", default-palette.paper),
    ink: pick("ink", default-palette.ink),
    brass: pick("brass", default-palette.brass),
    terracotta: pick("terracotta", default-palette.terracotta),
    slate: pick("slate", default-palette.slate),
    rule: pick("rule", default-palette.rule),
    cream: pick("cream", default-palette.cream),
    cream-deep: pick("cream_deep", default-palette.cream_deep),
    green: pick("green", default-palette.green),
    warn-bg: pick("warn_bg", default-palette.warn_bg),
    panel-bg: pick("panel_bg", default-palette.panel_bg),
    panel-bg-2: pick("panel_bg_2", default-palette.panel_bg_2),
    ink-on-dark: pick("ink_on_dark", default-palette.ink_on_dark),
    dark-note: pick("dark_note", default-palette.dark_note),

    // The design_system theme's faces, aligned with `grid.typ`. These were
    // "PT Serif"/"PT Sans"/"PT Mono", which put two typefaces in one book: every
    // page reached through `on-grid` was set in Source, and every page reached
    // through this theme -- the front matter and the imprint -- was set in PT.
    // The PT family stays in each stack as the fallback for a machine without
    // the bundled files, so a fallback build still succeeds.
    body-font: preset.at("body_font", default: ("Source Serif 4", "PT Serif", "Charter", "Georgia")),
    heading-font: preset.at("heading_font", default: ("Source Sans 3", "PT Sans", "Helvetica", "Arial")),
    mono-font: preset.at("mono_font", default: ("Source Code Pro", "PT Mono", "Menlo", "Courier New")),

    text-size: size,
    h1-size: dim(preset.at("h1_size", default: "22pt"), 22pt),
    h2-size: dim(preset.at("h2_size", default: "13.5pt"), 13.5pt),
    h3-size: dim(preset.at("h3_size", default: "11pt"), 11pt),
    // `par.leading` only accepts a length, and a length is *added to* the
    // font's em box rather than making up the baseline distance -- so
    // "1.45em" produced a 22.6pt pitch on 10.5pt type, and a bare 1.45 is
    // rejected as a float. The renderer measures each font's em box and passes
    // the remainder here, so the total baseline distance is exactly
    // text-size * leading_ratio no matter where the rule is applied.
    lead: size * float(preset.at("leading_extra_ratio", default: 0.75)),
    par-space: size * float(preset.at("par_space_ratio", default: 0.68)),

    page-w: dim(preset.at("page_width", default: "210mm"), 210mm),
    page-h: dim(preset.at("page_height", default: "297mm"), 297mm),

    eyebrow-size: 7.5pt,
    micro-size: 8pt,
    label-size: 8.5pt,
    kicker: str(preset.at("kicker", default: "FIELD MANUAL")),
  )
}

// ── Typography primitives ───────────────────────────────────────────────────
#let caps(t, th, color: none, size: none) = text(
  upper(str(t)),
  font: th.heading-font,
  size: if size == none { th.eyebrow-size } else { size },
  weight: "bold",
  fill: if color == none { th.brass } else { color },
  tracking: 1.6pt,
)

// The primary face of a font setting, which may be a single name or a
// fallback list.
#let face-name(f) = {
  let v = if type(f) == array { f.at(0) } else { f }
  str(v)
}

#let muted-note(t, th) = text(  font: th.body-font,
  size: th.micro-size,
  style: "italic",
  fill: th.slate,
)[#str(t)]

#let hair-rule(th, width: 100%, thickness: 0.5pt, color: none) = line(
  length: width,
  stroke: thickness + (if color == none { th.rule } else { color }),
)

#let lead-par(th) = (
  par(justify: true, first-line-indent: 0em, spacing: th.par-space, leading: th.lead),
)

// ── Callout ─────────────────────────────────────────────────────────────────
#let callout-palette(th) = (
  note:  (bg: th.cream,     edge: th.brass,       tag: "Note"),
  tip:   (bg: th.cream,     edge: th.green,       tag: "Practice"),
  step:  (bg: th.cream,     edge: th.brass,       tag: "Method"),
  goal:  (bg: th.panel-bg,  edge: th.green,       tag: "Learning objective"),
  warn:  (bg: th.warn-bg,   edge: th.terracotta,  tag: "Caution"),
  risk:  (bg: th.warn-bg,   edge: th.terracotta,  tag: "Risk"),
)

#let normalize-callout(kind) = {
  let k = lower(str(kind).replace("_", " ").replace("-", " ").trim())
  if k == "warning" { "warn" }
  else if k in ("danger", "error") { "risk" }
  else if k == "success" { "tip" }
  else if k in ("learning objective", "objective", "goal") { "goal" }
  else if k in ("info", "") { "note" }
  else if k in ("note", "tip", "step", "warn", "risk", "goal") { k }
  else { "note" }
}

#let callout-box(body, kind, th) = {
  let spec = callout-palette(th).at(normalize-callout(kind), default: callout-palette(th).note)
  block(
    width: 100%,
    fill: spec.bg,
    stroke: (left: 2.5pt + spec.edge, rest: 0.5pt + th.rule),
    inset: (left: 11pt, right: 10pt, top: 8pt, bottom: 8pt),
    radius: (right: 2pt),
  )[
    #set par(justify: false, first-line-indent: 0em, spacing: 0.34em)
    #set text(size: th.text-size * 0.93)
    #caps(spec.tag, th, color: spec.edge)
    #v(0.4em)
    #body
  ]
}

// ── Definition ──────────────────────────────────────────────────────────────
#let definition-block(term, body, th) = block(
  width: 100%,
  inset: (left: 10pt, right: 4pt, top: 3pt, bottom: 5pt),
  stroke: (left: 1.2pt + th.brass),
  breakable: true,
)[
  #set par(justify: true, first-line-indent: 0em, spacing: 0.3em, leading: th.lead)
  #text(font: th.heading-font, size: th.label-size + 0.5pt, weight: "bold", fill: th.ink)[#str(term)]
  #v(0.2em)
  #body
]

// ── Pull quote ──────────────────────────────────────────────────────────────
#let pull-quote(quote, author, th) = block(
  width: 100%,
  inset: (left: 14pt, right: 8pt, top: 5pt, bottom: 5pt),
  stroke: (left: 2.5pt + th.brass),
  breakable: true,
)[
  #set par(justify: false, first-line-indent: 0em, leading: 1.34em)
  #text(font: th.body-font, size: th.text-size + 2.2pt, style: "italic", fill: th.ink)[“#str(quote)”]
  #if str(author) != "" [
    #v(0.55em)
    #caps(author, th, color: th.slate, size: 8pt)
  ]
]

// ── Figure ──────────────────────────────────────────────────────────────────
#let figure-block(img, th, height: none, tail: 1.1em) = {
  let path = str(img.at("path", default: ""))
  let caption = str(img.at("caption", default: ""))
  if path != "" {
    block(width: 100%, breakable: false)[
      #set par(justify: false, first-line-indent: 0em)
      #box(
        width: 100%,
        fill: th.cream,
        stroke: 0.5pt + th.rule,
        inset: 0pt,
        clip: true,
      )[
        // A page family that composes to a fixed height can cap the artwork
        // here, so the figure never becomes the thing that pushes a page over.
        // `fit` needs both dimensions to be meaningful. With a height alone,
        // Typst fell back to the artwork's natural size and the cap did
        // nothing, which is what pushed composed openers onto a second sheet.
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
        #hair-rule(th, width: 1.6cm, thickness: 1pt, color: th.brass)
        #v(0.35em)
        #muted-note(caption, th)
      ]
      #v(tail)
    ]
  } else if caption != "" {
    v(0.7em)
    muted-note(caption, th)
    v(0.7em)
  }
}

// ── Code ────────────────────────────────────────────────────────────────────
#let code-block(cb, th) = {
  let lang = str(cb.at("language", default: ""))
  let caption = str(cb.at("caption", default: ""))
  let body = str(cb.at("code", default: ""))
  if body.trim() != "" {
    block(
      width: 100%,
      fill: th.panel-bg,
      stroke: (left: 2.5pt + th.slate, rest: 0.5pt + th.rule),
      inset: (left: 11pt, right: 10pt, top: 8pt, bottom: 8pt),
      radius: (right: 2pt),
    )[
      #set par(justify: false, first-line-indent: 0em, leading: 1.25em)
      #if lang != "" or caption != "" [
        #caps(lang, th, color: th.slate)
        #if caption != "" [
          #h(0.6em)
          #muted-note(caption, th)
        ]
        #v(0.45em)
        #hair-rule(th, thickness: 0.4pt)
        #v(0.5em)
      ]
      #text(font: th.mono-font, size: th.text-size * 0.84)[#body]
    ]
    v(0.9em, weak: true)
  }
}

// ── Editorial table ─────────────────────────────────────────────────────────
#let metric-table(tbl, th) = {
  let headers = tbl.at("headers", default: ())
  let rows = tbl.at("rows", default: ())
  let caption = str(tbl.at("caption", default: ""))
  if headers.len() > 0 and rows.len() > 0 {
    block(width: 100%, breakable: true)[
      #set par(justify: false, first-line-indent: 0em)
      #table(
        columns: headers.len(),
        align: (left,) * headers.len(),
        inset: (left: 7pt, right: 7pt, top: 5pt, bottom: 5pt),
        stroke: (x: 0.4pt + th.rule, y: 0.4pt + th.rule),
        fill: (x, y) => if y == 0 { th.cream-deep } else if calc.odd(y) { rgb("#FCFAF5") } else { white },
        table.header(
          repeat: true,
          ..headers.map(h => text(font: th.heading-font, size: th.label-size, weight: "bold", fill: th.ink)[#str(h)]),
        ),
        ..rows.flatten().map(c => text(size: th.text-size * 0.92)[#str(c)]),
      )
      #if caption != "" [
        #v(0.45em)
        #muted-note(caption, th)
      ]
    ]
    v(1em, weak: true)
  }
}

// ── Lists ───────────────────────────────────────────────────────────────────
#let dash-list(items, th) = {
  block(width: 100%, breakable: true)[
    #set par(justify: true, first-line-indent: 0em, spacing: 0.42em, leading: th.lead)
    #for it in items [
      #box(width: 11pt)[#text(font: th.heading-font, size: th.label-size, fill: th.brass)[—]]
      #h(0.4em)
      #text(size: th.text-size * 0.96)[#str(it)]
      #v(0.08em)
    ]
  ]
}

#let checklist(items, th) = {
  block(width: 100%, breakable: true)[
    #set par(justify: true, first-line-indent: 0em, spacing: 0.5em, leading: th.lead)
    #for it in items [
      #box(width: 10pt, height: 10pt, stroke: 0.7pt + th.brass, radius: 1.5pt, baseline: 1.5pt)[]
      #h(0.55em)
      #text(size: th.text-size * 0.96)[#str(it)]
      #v(0.08em)
    ]
  ]
}

// ── Case study ──────────────────────────────────────────────────────────────
#let case-study-card(study, body, th) = block(
  width: 100%,
  breakable: true,
  stroke: (top: 1.4pt + th.brass, bottom: 0.5pt + th.rule),
  inset: (left: 0pt, right: 0pt, top: 8pt, bottom: 9pt),
)[
  #set par(justify: true, first-line-indent: 0em, spacing: 0.55em, leading: th.lead)
  #set text(size: th.text-size)
  #caps("Case study", th, color: th.terracotta)
  #v(0.3em)
  #if str(study.at("title", default: "")) != "" [
    #text(font: th.heading-font, size: th.h3-size, weight: "bold", fill: th.ink)[#study.title]
    #v(0.15em)
  ]
  #body
]

// ── Worked example ──────────────────────────────────────────────────────────
#let worked-example-card(example, body, th) = {
  let steps = example.at("steps", default: ())
  let answer = str(example.at("answer", default: ""))
  let verification = str(example.at("verification", default: ""))
  block(
    width: 100%,
    breakable: true,
    fill: th.cream,
    stroke: (left: 2.5pt + th.terracotta),
    inset: (left: 11pt, right: 10pt, top: 8pt, bottom: 9pt),
    radius: (right: 2pt),
  )[
    #set par(justify: true, first-line-indent: 0em, spacing: 0.5em, leading: th.lead)
    #set text(size: th.text-size * 0.95)
    #caps("Worked example", th, color: th.terracotta)
    #v(0.3em)
    #if str(example.at("title", default: "")) != "" [
      #text(font: th.heading-font, size: th.h3-size, weight: "bold", fill: th.ink)[#example.title]
      #v(0.35em)
    ]
    #if body != none [ #body ]
    #if steps.len() > 0 [
      #v(0.4em)
      #for s in steps {
        let n = if type(s) == dictionary { str(s.at("number", default: "")) } else { "" }
        let desc = if type(s) == dictionary { str(s.at("description", default: "")) } else { str(s) }
        let calc = if type(s) == dictionary { str(s.at("calculation", default: "")) } else { "" }
        let note = if type(s) == dictionary { str(s.at("explanation", default: "")) } else { "" }
        block(width: 100%, breakable: true)[
          #set par(justify: true, first-line-indent: 0em, spacing: 0.22em, leading: th.lead)
          #box(width: 1.5em)[
            #text(font: th.heading-font, size: th.label-size, weight: "bold", fill: th.terracotta)[#if n == "" { "·" } else { n }]
          ]
          #text(size: th.text-size * 0.93)[#desc]
          #if calc != "" [
            #v(0.25em)
            #block(width: 100%, fill: white, stroke: 0.4pt + th.rule, inset: (left: 7pt, right: 6pt, top: 4pt, bottom: 4pt))[
              #set par(justify: false, first-line-indent: 0em, leading: 1.2em)
              #text(font: th.mono-font, size: th.text-size * 0.82)[#calc]
            ]
          ]
          #if note != "" [
            #v(0.2em)
            #muted-note(note, th)
          ]
          #v(0.25em)
        ]
      }
    ]
    #if answer != "" [
      #v(0.35em)
      #block(width: 100%, fill: white, stroke: (left: 2pt + th.brass), inset: (left: 8pt, right: 6pt, top: 5pt, bottom: 5pt))[
        #set par(justify: false, first-line-indent: 0em, leading: 1.3em)
        #caps("Result", th, color: th.ink)
        #v(0.25em)
        #text(size: th.text-size * 0.93, weight: "medium")[#answer]
      ]
    ]
    #if verification != "" [
      #v(0.35em)
      #muted-note(verification, th)
    ]
  ]
  v(1em, weak: true)
}

// ── Exercise ────────────────────────────────────────────────────────────────
#let exercise-card(ex, body, th) = {
  let hints = ex.at("hints", default: ())
  let response = str(ex.at("response_type", default: "lines"))
  let lines = calc.min(8, calc.max(0, int(ex.at("response_lines", default: 4))))
  block(
    width: 100%,
    breakable: true,
    fill: th.panel-bg-2,
    stroke: (top: 1.2pt + th.ink, rest: 0.5pt + th.rule),
    inset: (left: 10pt, right: 10pt, top: 8pt, bottom: 9pt),
    radius: (bottom: 2pt),
  )[
    #set par(justify: true, first-line-indent: 0em, spacing: 0.45em, leading: th.lead)
    #caps(str(ex.at("kicker", default: "Exercise")), th, color: th.terracotta)
    #v(0.3em)
    #if str(ex.at("title", default: "")) != "" [
      #text(font: th.heading-font, size: th.h3-size, weight: "bold", fill: th.ink)[#str(ex.at("title", default: ""))]
      #v(0.35em)
    ]
    #if str(ex.at("instructions", default: "")) != "" [
      #text(size: th.text-size * 0.9, style: "italic", fill: th.slate)[#ex.instructions]
      #v(0.4em)
    ]
    #if body != none [ #body ]
    #if hints.len() > 0 [
      #v(0.3em)
      #caps("Hints", th, color: th.slate, size: 7.5pt)
      #v(0.3em)
      #dash-list(hints.map(s => str(s)), th)
    ]
    #if response == "lines" and lines > 0 [
      #v(0.5em)
      #for i in range(lines) [
        #v(0.6em, weak: true)
        #hair-rule(th, thickness: 0.4pt)
      ]
    ]
  ]
  v(1em, weak: true)
}

// ── Process diagram (typeset, not an image) ─────────────────────────────────
#let process-diagram(steps, th) = {
  if steps.len() > 0 {
    let cols = calc.min(3, calc.max(2, steps.len()))
    block(width: 100%, breakable: false)[
      #set par(justify: false, first-line-indent: 0em, spacing: 0.25em, leading: 1.25em)
      #let idx = 0
      #for row in steps.chunks(cols) {
        grid(
          columns: cols,
          gutter: 9pt,
          ..row.map(s => {
            idx = idx + 1
            block(
              width: 100%,
              fill: th.cream,
              stroke: 0.5pt + th.rule,
              inset: (left: 8pt, right: 8pt, top: 7pt, bottom: 7pt),
              radius: 2pt,
            )[
              #set par(justify: false, first-line-indent: 0em, spacing: 0.2em, leading: 1.25em)
              #caps(calc.repr(idx), th, size: 6.5pt)
              #v(0.25em)
              #text(font: th.heading-font, size: th.label-size, fill: th.ink)[#str(s)]
            ]
          }),
        )
        v(9pt)
      }
    ]
    v(1em, weak: true)
  }
}

// ── Recap ───────────────────────────────────────────────────────────────────
#let recap-card(items, th) = block(
  width: 100%,
  breakable: true,
  stroke: (left: 2.5pt + th.brass),
  inset: (left: 11pt, right: 6pt, top: 2pt, bottom: 2pt),
)[
  #set par(justify: true, first-line-indent: 0em, spacing: 0.4em, leading: th.lead)
  #caps("Chapter recap", th)
  #v(0.55em)
  #for it in items [
    #box(width: 11pt)[#text(font: th.heading-font, size: th.label-size, fill: th.terracotta)[•]]
    #h(0.35em)
    #text(size: th.text-size * 0.94)[#str(it)]
    #v(0.08em)
  ]
]

// The chapter's own closing paragraph, set as a lede above the recap.
#let summary-note(body, th) = block(
  width: 100%,
  breakable: true,
  above: 0.2em,
  below: 0.9em,
  inset: (left: 11pt, right: 8pt, top: 5pt, bottom: 5pt),
  fill: th.panel-bg,
  radius: 1.5pt,
)[
  #set par(justify: true, first-line-indent: 0em, leading: th.lead)
  #caps("Chapter summary", th, color: th.terracotta, size: 7.5pt)
  #v(0.3em)
  #text(size: th.text-size * 0.95, fill: th.ink)[#body]
]

// One exercise the chapter set, labelled by its kind.
#let practice-row(kind, subject, th) = block(
  width: 100%,
  breakable: true,
  below: 0.45em,
)[
  #set par(justify: false, first-line-indent: 0em, leading: th.lead)
  #grid(
    columns: (26%, 1fr),
    gutter: 10pt,
    align: (left, left),
    text(
      font: th.heading-font,
      size: th.text-size * 0.82,
      weight: "bold",
      fill: th.terracotta,
    )[#kind],
    text(size: th.text-size * 0.95, fill: th.ink)[#subject],
  )
]

// ── Block dispatcher ────────────────────────────────────────────────────────
#let render-block(blk, th) = {
  let kind = str(blk.at("type", default: "paragraph"))
  let raw = str(blk.at("content", default: ""))
  let body = text(raw)

  if kind == "heading" {
    // A real heading element, so section titles reach the contents page and the
    // PDF bookmarks. book_pages.typ owns the treatment for each level; drawing
    // the title here as loose text left the book's own navigation empty.
    let lvl = int(blk.at("level", default: 2))
    let level = if lvl <= 1 { 1 } else if lvl == 2 { 2 } else { 3 }
    heading(level: level)[#raw]
  } else if kind == "paragraph" or kind == "unknown" {
    block(breakable: true, width: 100%)[#text(size: th.text-size)[#raw]]
  } else if kind == "list" or kind == "list_item" {
    let items = blk.at("list", default: (:)).at("items", default: ())
    let use = if items.len() > 0 { items.map(s => str(s)) } else { raw.split("\n").filter(s => s.trim() != "") }
    dash-list(use, th)
    v(0.7em, weak: true)
  } else if kind == "checklist" {
    let items = blk.at("list", default: (:)).at("items", default: ())
    let use = if items.len() > 0 { items.map(s => str(s)) } else { raw.split("\n").filter(s => s.trim() != "") }
    checklist(use, th)
    v(0.7em, weak: true)
  } else if kind == "definition" {
    let d = blk.at("definition", default: (:))
    definition-block(str(d.at("term", default: "Term")), body, th)
    v(0.7em, weak: true)
  } else if kind == "table" {
    metric-table(blk.at("table", default: (:)), th)
  } else if kind == "code" {
    code-block(blk.at("code", default: (:)), th)
  } else if kind == "image_instruction" {
    figure-block(blk.at("image", default: (:)), th)
  } else if kind == "exercise" {
    exercise-card(blk.at("exercise", default: (:)), if raw == "" { none } else { body }, th)
  } else if kind == "worked_example" {
    worked-example-card(blk.at("worked_example", default: (:)), if raw == "" { none } else { body }, th)
  } else if kind == "case_study" {
    case-study-card(blk.at("case_study", default: (:)), body, th)
    v(0.9em, weak: true)
  } else if kind in ("warning", "callout") {
    let c = blk.at("callout", default: (:))
    let k = if kind == "warning" { "warn" } else { str(c.at("kind", default: "note")) }
    // Prefer the cleaned text: content still carries the block's pipeline
    // label, which the callout kicker already states.
    let copy = if str(c.at("text", default: "")) != "" { text(c.text) } else { body }
    v(0.4em)
    callout-box(copy, k, th)
    v(0.4em)
  } else if kind == "quotation" {
    let q = blk.at("pull_quote", default: (:))
    pull-quote(str(q.at("text", default: raw)), str(q.at("author", default: "")), th)
    v(0.9em, weak: true)
  } else if kind == "reference" {
    block(width: 100%, breakable: true, inset: (left: 1.2em))[
      #set par(justify: true, first-line-indent: -1.2em, spacing: 0.4em, leading: th.lead)
      #text(size: th.text-size * 0.92)[#raw]
    ]
  } else if kind == "footnote" {
    footnote(body)
  } else if kind == "page_break" {
    pagebreak(weak: true)
  } else if kind == "section_break" {
    v(0.8em, weak: true)
  } else if kind == "process_diagram" {
    let steps = blk.at("list", default: (:)).at("items", default: ())
    process-diagram(steps.map(s => str(s)), th)
  } else {
    block(breakable: true, width: 100%)[#text(size: th.text-size)[#raw]]
  }
}

#let render-blocks(blocks, th) = {
  for b in blocks { render-block(b, th) }
}
