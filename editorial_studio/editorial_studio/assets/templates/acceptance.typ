// Minimal acceptance template — renders content as raw text to avoid eval issues
#let doc = json("assets/content.json")
#let p = doc.at("preset", default: ( : ))

// ── Preset helpers
#let body-font    = p.at("body_font",    default: "PT Serif")
#let heading-font = p.at("heading_font", default: "PT Sans")
#let mono-font    = p.at("mono_font",    default: "Source Code Pro")
#let accent-color = rgb(p.at("accent_color",  default: "#1d3557"))
#let head-color   = rgb(p.at("heading_color", default: "#1d3557"))
#let muted-color  = rgb(p.at("muted_color",   default: "#64748b"))
#let body-color   = rgb(p.at("body_color",    default: "#1a1a1a"))
#let text-size    = eval(p.at("text_size", default: "10.5pt"), mode: "code")
#let h1-size      = eval(p.at("h1_size",   default: "16pt"),   mode: "code")
#let h2-size      = eval(p.at("h2_size",   default: "13pt"),   mode: "code")
#let h3-size      = eval(p.at("h3_size",   default: "11pt"),   mode: "code")
#let show-toc     = p.at("show_toc", default: true)
#let do-number    = p.at("numbered_headings", default: true)

#let page-w = eval(p.at("paper", default: "a4"), mode: "code")

#set page(
  paper: page-w,
  margin: (
    left:   eval(p.at("margin_left",   default: "2.5cm"), mode: "code"),
    right:  eval(p.at("margin_right",  default: "2.5cm"), mode: "code"),
    top:    eval(p.at("margin_top",    default: "2.5cm"), mode: "code"),
    bottom: eval(p.at("margin_bottom", default: "2.5cm"), mode: "code"),
  ),
  header: context {
    if here().page() > 1 {
      set text(font: heading-font, size: 8pt, fill: muted-color)
      doc.title
      h(1fr)
      counter(page).display("1")
    }
  },
)

#set text(
  font: body-font,
  size: text-size,
  fill: body-color,
  lang: doc.language,
  hyphenate: true,
)
#set par(
  justify: true,
  leading: eval(p.at("leading", default: "0.65em"), mode: "code"),
  spacing: 1.1em,
)
#show raw: set text(font: mono-font, size: 0.88em)

#show heading.where(level: 1): it => {
  v(1.5em)
  set text(font: heading-font, size: h1-size, weight: "bold", fill: head-color)
  if do-number { set heading(numbering: "1.") }
  it
  v(0.5em)
}
#show heading.where(level: 2): it => {
  v(1em)
  set text(font: heading-font, size: h2-size, weight: "semibold", fill: head-color)
  if do-number { set heading(numbering: "1.1") }
  it
  v(0.4em)
}
#show heading.where(level: 3): it => {
  v(0.6em)
  set text(font: heading-font, size: h3-size, weight: "semibold", fill: head-color)
  it
  v(0.3em)
}

// ── Cover
v(4cm)
align(center)[
  #set text(font: heading-font, size: 28pt, weight: "bold", fill: head-color)
  doc.title
  v(1.5em)
  #set text(font: body-font, size: 13pt, fill: muted-color, style: "italic")
  doc.author
]
pagebreak()

// ── TOC
#outline(title: none, indent: 1.5em, depth: 2)
pagebreak()

// ── Body
#set page(numbering: "1")
#counter(page).update(1)

#if do-number {
  set heading(numbering: "1.1")
}

#for (si, section) in doc.sections.enumerate() {
  let lvl = section.level
  if lvl == 1 {
    heading(level: 1)[#section.title]
  }
  else if lvl == 2 { heading(level: 2)[#section.title] }
  else { heading(level: 3)[#section.title] }

  // Render content as raw text paragraphs (no eval)
  let paras = section.content.split("\n\n").map(s => s.trim()).filter(s => s != "")
  for p in paras {
    par[p]
  }

  // Render images
  for im in section.images {
    let w = im.at("width", default: "85%")
    if w == "full" { w = "100%" }
    v(0.9em, weak: true)
    figure(
      image(im.at("_local", default: im.path), width: eval(w, mode: "code")),
      caption: if im.at("caption", default: "") != "" { [#im.caption] } else { none },
      supplement: none,
    )
    v(0.9em, weak: true)
  }

  // Render tables
  for tbl in section.tables {
    v(0.7em)
    let col-count = tbl.headers.len()
    figure(
      table(
        columns: col-count,
        fill: (_, row) => if row == 0 { luma(225) } else if calc.odd(row) { luma(250) } else { white },
        stroke: 0.5pt + luma(185),
        inset: (x: 8pt, y: 5pt),
        ..tbl.headers.map(h => text(weight: "semibold")[#h]),
        ..tbl.rows.flatten().map(cell => [#cell]),
      ),
      caption: if tbl.caption != "" { tbl.caption } else { none },
      supplement: none,
    )
    v(0.5em)
  }

  // Render code
  for cb in section.code_blocks {
    v(0.6em)
    block(
      width: 100%,
      fill: luma(246),
      stroke: (left: 3pt + luma(200), rest: 0.5pt + luma(215)),
      radius: 3pt,
      inset: (x: 12pt, y: 10pt),
    )[
      #if cb.caption != "" or cb.language != "" [
        #set text(font: mono-font, size: 7.5pt, fill: luma(100))
        #cb.language#if cb.caption != "" and cb.language != "" [ — ]#cb.caption
        #v(0.4em)
      ]
      #set text(font: mono-font, size: 9pt)
      #raw(cb.code, lang: if cb.language != "" { cb.language } else { none })
    ]
    v(0.5em)
  }

  // Render callouts
  for co in section.callouts {
    let colors = (
      info:    (bg: rgb("#e8f4fd"), border: rgb("#2980b9"), icon: "ℹ"),
      warning: (bg: rgb("#fef9e7"), border: rgb("#e67e22"), icon: "⚠"),
      tip:     (bg: rgb("#eafaf1"), border: rgb("#27ae60"), icon: "✓"),
      danger:  (bg: rgb("#fdf2f2"), border: rgb("#c0392b"), icon: "✗"),
      quote:   (bg: rgb("#faf6ef"), border: rgb("#c8b48a"), icon: "❝"),
    )
    let c = colors.at(co.kind, default: colors.info)
    v(0.6em)
    block(
      width: 100%,
      fill: c.bg,
      stroke: (left: 3pt + c.border),
      inset: (left: 11pt, right: 9pt, top: 8pt, bottom: 8pt),
      radius: (right: 3pt),
    )[
      #set text(size: 0.92em)
      #raw(co.text)
    ]
    v(0.6em)
  }
}