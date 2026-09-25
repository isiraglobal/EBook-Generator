#import "helpers.typ": callout-box, render-code

#let doc = json("assets/content.json")
#let preset = doc.at("preset", default: (:))
#let pages = doc.at("pages", default: ())

#let body-font = preset.at("body_font", default: "PT Serif")
#let heading-font = preset.at("heading_font", default: "PT Sans")
#let mono-font = preset.at("mono_font", default: "PT Mono")
#let accent-color = rgb(preset.at("accent_color", default: "#1d3557"))
#let heading-color = rgb(preset.at("heading_color", default: "#1a1a1a"))
#let body-color = rgb(preset.at("body_color", default: "#1a1a1a"))
#let muted-color = rgb(preset.at("muted_color", default: "#64748b"))
#let sidebar-bg = rgb(preset.at("sidebar_bg", default: "#f8f9fa"))
#let table-header = rgb(preset.at("table_header", default: "#f1f1f1"))
#let table-row-alt = rgb(preset.at("table_row_alt", default: "#fafafa"))
#let text-size = eval(preset.at("text_size", default: "10.5pt"), mode: "code")
#let h1-size = eval(preset.at("h1_size", default: "22pt"), mode: "code")
#let h2-size = eval(preset.at("h2_size", default: "14pt"), mode: "code")
#let h3-size = eval(preset.at("h3_size", default: "11.5pt"), mode: "code")
#let show-running = preset.at("show_header_footer", default: true)
#let header-rule = preset.at("header_rule", default: true)
#let page-number-position = preset.at("page_num_position", default: "bottom-center")

#set page(
  width: eval(preset.at("page_width", default: "210mm"), mode: "code"),
  height: eval(preset.at("page_height", default: "297mm"), mode: "code"),
  margin: (
    top: eval(preset.at("margin_top", default: "25mm"), mode: "code"),
    bottom: eval(preset.at("margin_bottom", default: "25mm"), mode: "code"),
    inside: eval(preset.at("margin_inner", default: "25mm"), mode: "code"),
    outside: eval(preset.at("margin_outer", default: "25mm"), mode: "code"),
  ),
  header: context {
    if show-running and here().page() > 2 [
      #set text(font: heading-font, size: 7.5pt, fill: muted-color)
      #let number = counter(page).display("1")
      #if page-number-position == "top-left" [#number #h(1fr) #doc.title]
      else if page-number-position == "top-center" [#grid(columns: (1fr, auto, 1fr), align(left)[#doc.title], number, [])]
      else if page-number-position == "top-right" [#doc.title #h(1fr) #number]
      else if calc.odd(here().page()) [#doc.title #h(1fr) #number]
      else [#number #h(1fr) #doc.title]
      #v(-3pt)
      #if header-rule { line(length: 100%, stroke: 0.4pt + luma(210)) }
    ]
  },
  footer: context {
    if show-running and here().page() > 2 and page-number-position.starts-with("bottom") [
      #set text(font: heading-font, size: 7.5pt, fill: muted-color)
      #align(
        if page-number-position == "bottom-left" { left }
        else if page-number-position == "bottom-right" { right }
        else { center }
      )[#counter(page).display("1")]
    ]
  },
)

#set text(
  font: body-font,
  size: text-size,
  fill: body-color,
  lang: doc.at("language", default: "en"),
  hyphenate: preset.at("hyphenate", default: true),
)

#set par(
  justify: preset.at("justify", default: true),
  leading: eval(preset.at("leading", default: "1.4em"), mode: "code"),
  spacing: 0.65em,
  first-line-indent: eval(preset.at("indent", default: "0em"), mode: "code"),
)

#show raw: set text(font: mono-font, size: 0.88em)
#show figure.caption: it => [
  #set text(font: heading-font, size: 8pt, style: "italic", fill: muted-color)
  #set par(justify: false, first-line-indent: 0em)
  #align(center)[#it.body]
]

#show heading.where(level: 1): it => [
  #v(0.8em)
  #align(left)[
    #set text(font: heading-font, size: h1-size, weight: "bold", fill: heading-color)
    #it.body
  ]
  #v(0.25em)
  #line(length: 100%, stroke: 1pt + accent-color)
  #v(0.7em)
]

#show heading.where(level: 2): it => [
  #v(1em)
  #set text(font: heading-font, size: h2-size, weight: "semibold", fill: heading-color)
  #it
  #v(0.3em)
]

#show heading.where(level: 3): it => [
  #v(0.7em)
  #set text(font: heading-font, size: h3-size, weight: "semibold", fill: heading-color)
  #it
  #v(0.2em)
]

#let render-table(tbl) = {
  let headers = tbl.at("headers", default: ("Item", "Detail"))
  let rows = tbl.at("rows", default: ())
  v(0.6em, weak: true)
  block(breakable: true, width: 100%)[
    #table(
      columns: headers.len(),
      fill: (_, row) => if row == 0 { table-header } else if calc.odd(row) { table-row-alt } else { white },
      stroke: (_, row) => if row == 0 { 0.7pt + accent-color } else { 0.35pt + luma(220) },
      inset: (x: 6pt, y: 4pt),
      align: left,
      ..headers.map(value => text(size: 8.5pt, weight: "semibold")[#value]),
      ..rows.flatten().map(value => text(size: 8.5pt)[#value]),
    )
    #let caption = tbl.at("caption", default: "")
    #if caption != "" [
      #v(0.3em)
      #text(size: 8pt, style: "italic", fill: muted-color)[#caption]
    ]
  ]
  v(0.5em, weak: true)
}

#let render-list(blk) = {
  let content = blk.at("content", default: "")
  let items = blk.at("list", default: ()).at("items", default: ())
  if items.len() == 0 { items = content.split("\n").filter(value => value.trim() != "") }
  block(width: 100%, breakable: true)[
    #set par(first-line-indent: 0em, spacing: 0.3em)
    #for item in items [
      #text[• #item]
      #v(0.2em)
    ]
  ]
  v(0.4em, weak: true)
}

#let render-image(blk) = {
  let image-data = blk.at("image", default: (:))
  let path = image-data.at("path", default: "")
  let caption = image-data.at("caption", default: blk.at("content", default: ""))
  if path != "" {
    let width = image-data.at("width", default: "85%")
    if width == "full" { width = "100%" }
    figure(
      image(path, width: eval(width, mode: "code")),
      caption: [#caption],
      supplement: none,
    )
  } else {
    callout-box([
      #text(weight: "semibold", fill: accent-color)[Illustration brief]
      #linebreak()
      #caption
    ], "info")
  }
  v(0.5em, weak: true)
}

#let render-exercise(blk) = {
  let exercise = blk.at("exercise", default: (:))
  let content = blk.at("content", default: "")
  callout-box([
    #set par(first-line-indent: 0em, justify: false)
    #text(weight: "bold", fill: accent-color)[#exercise.at("title", default: "Exercise")]
    #v(0.4em)
    #let instructions = exercise.at("instructions", default: "")
    #if instructions != "" [
      #text(style: "italic", fill: muted-color)[#instructions]
      #v(0.4em)
    ]
    #content
    #let hints = exercise.at("hints", default: ())
    #if hints.len() > 0 [
      #v(0.5em)
      #text(weight: "semibold")[Hints]
      #for hint in hints [
        #v(0.2em)
        #text[• #hint]
      ]
    ]
    #if exercise.at("response_type", default: "lines") == "lines" {
      for _ in range(int(exercise.at("response_lines", default: 4))) {
        v(0.55em, weak: true)
        line(length: 100%, stroke: 0.4pt + luma(205))
      }
    }
  ], "info")
}

#let render-worked-example(blk) = {
  let example = blk.at("worked_example", default: (:))
  let content = blk.at("content", default: "")
  block(width: 100%, fill: sidebar-bg, stroke: (left: 3pt + accent-color), inset: 12pt, breakable: true)[
    #set par(first-line-indent: 0em, justify: false)
    #text(size: 12pt, weight: "bold", fill: accent-color)[Worked example]
    #let title = example.at("title", default: "")
    #if title != "" [
      #v(0.2em)
      #text(weight: "semibold")[#title]
    ]
    #v(0.5em)
    #content
    #let steps = example.at("steps", default: ())
    #if steps.len() > 0 {
      for step in steps [
        #let step-number = if type(step) == dictionary { step.at("number", default: "") } else { "" }
        #let step-description = if type(step) == dictionary { step.at("description", default: "") } else { step }
        #let calculation = if type(step) == dictionary { step.at("calculation", default: "") } else { "" }
        #let explanation = if type(step) == dictionary { step.at("explanation", default: "") } else { "" }
        #v(0.45em)
        #if step-number != "" [#text(weight: "semibold")[Step #step-number] #v(0.2em)]
        #step-description
        #if calculation != "" [
          #v(0.25em)
          #block(fill: luma(245), inset: 7pt, radius: 2pt)[#text(font: mono-font, size: 8.5pt)[#calculation]]
        ]
        #if explanation != "" [
          #v(0.2em)
          #text(size: 8.5pt, style: "italic", fill: muted-color)[#explanation]
        ]
      ]
    }
    #let answer = example.at("answer", default: "")
    #if answer != "" [
      #v(0.5em)
      #text(weight: "semibold", fill: accent-color)[Result: #answer]
    ]
    #let verification = example.at("verification", default: "")
    #if verification != "" [
      #v(0.2em)
      #text(size: 8.5pt, fill: muted-color)[#verification]
    ]
  ]
  v(0.6em, weak: true)
}

#let render-block(blk) = {
  let kind = blk.at("type", default: "paragraph")
  let content = blk.at("content", default: "")
  if kind == "heading" {
    heading(level: int(blk.at("level", default: 2)))[#content]
  } else if kind == "paragraph" or kind == "unknown" {
    block(breakable: true)[#content]
  } else if kind == "list" or kind == "list_item" {
    render-list(blk)
  } else if kind == "definition" {
    let definition = blk.at("definition", default: (:))
    callout-box([
      #text(weight: "bold", fill: accent-color)[#definition.at("term", default: "Definition")]
      #linebreak()
      #content
    ], "info")
  } else if kind == "table" {
    render-table(blk.at("table", default: (:)))
  } else if kind == "code" {
    render-code(blk.at("code", default: (:)), mono-font)
  } else if kind == "image_instruction" {
    render-image(blk)
  } else if kind == "exercise" {
    render-exercise(blk)
  } else if kind == "worked_example" {
    render-worked-example(blk)
  } else if kind == "case_study" {
    let study = blk.at("case_study", default: (:))
    block(width: 100%, fill: sidebar-bg, stroke: (top: 1pt + accent-color, bottom: 1pt + accent-color), inset: 11pt, breakable: true)[
      #set par(first-line-indent: 0em)
      #text(weight: "bold", fill: accent-color)[Case study]
      #let title = study.at("title", default: "")
      #if title != "" [
        #v(0.2em)
        #text(weight: "semibold")[#title]
      ]
      #v(0.45em)
      #content
    ]
    v(0.5em, weak: true)
  } else if kind == "warning" or kind == "callout" {
    let callout = blk.at("callout", default: (:))
    let callout-kind = "info"
    if kind == "warning" { callout-kind = "warning" }
    callout-box(content, callout.at("kind", default: callout-kind))
  } else if kind == "quotation" {
    let quote = blk.at("pull_quote", default: (:))
    block(width: 88%, inset: (left: 12pt, right: 8pt), stroke: (left: 2pt + accent-color), breakable: true)[
      #set par(justify: false, first-line-indent: 0em)
      #text(style: "italic")[“#quote.at("text", default: content)”]
      #let author = quote.at("author", default: "")
      #if author != "" [
        #v(0.3em)
        #align(right)[#text(size: 8.5pt, fill: muted-color)[— #author]]
      ]
    ]
    v(0.5em, weak: true)
  } else if kind == "reference" {
    let reference = blk.at("reference", default: (:))
    block(width: 100%, inset: (left: 1em), breakable: true)[
      #set par(first-line-indent: -1em, spacing: 0.45em)
      #reference.at("text", default: content)
    ]
  } else if kind == "footnote" {
    footnote(content)
  } else if kind == "page_break" {
    pagebreak(weak: true)
  } else if kind == "section_break" {
    v(0.6em, weak: true)
  } else {
    block(breakable: true)[#content]
  }
}

#let render-blocks(blocks) = {
  for block in blocks { render-block(block) }
}

#for (page-index, page-data) in pages.enumerate() {
  let purpose = page-data.at("purpose", default: "content")
  let page-width = page-data.at("width_mm", default: 210) * 1mm
  let page-height = page-data.at("height_mm", default: 297) * 1mm
  let page-margins = page-data.at("margins", default: (:))
  set page(
    width: page-width,
    height: page-height,
    margin: (
      top: page-margins.at("top_mm", default: 25) * 1mm,
      bottom: page-margins.at("bottom_mm", default: 25) * 1mm,
      inside: page-margins.at("left_mm", default: 25) * 1mm,
      outside: page-margins.at("right_mm", default: 25) * 1mm,
    ),
  )

  if purpose == "cover" {
    let cover = page-data.at("cover_data", default: (:))
    set page(margin: 0pt, fill: rgb(cover.at("background_color", default: "#f4f0e6")))
    set par(justify: false, first-line-indent: 0em)
    align(center + horizon)[
      #line(length: 5cm, stroke: 2pt + accent-color)
      #v(1cm)
      #text(font: heading-font, size: 36pt, weight: "bold", fill: heading-color)[#doc.title]
      #let subtitle = doc.at("subtitle", default: "")
      #if subtitle != "" [
        #v(0.7cm)
        #text(font: body-font, size: 16pt, style: "italic", fill: muted-color)[#subtitle]
      ]
      #v(0.8cm)
      #line(length: 5cm, stroke: 2pt + accent-color)
      #v(1.4cm)
      #let author = doc.at("author", default: "")
      #if author != "" [#text(size: 13pt)[#author]]
      #v(1.2cm)
      #text(size: 10pt, fill: muted-color)[FIELD EDITION]
    ]
  } else if purpose == "title_page" {
    set page(margin: (top: 4cm, bottom: 3cm, inside: 3cm, outside: 3cm))
    align(center + horizon)[
      #text(font: heading-font, size: 28pt, weight: "bold", fill: heading-color)[#doc.title]
      #let subtitle = doc.at("subtitle", default: "")
      #if subtitle != "" [
        #v(0.6cm)
        #text(size: 14pt, style: "italic", fill: muted-color)[#subtitle]
      ]
      #v(0.8cm)
      #line(length: 6cm, stroke: 1pt + accent-color)
      #v(0.7cm)
      #let author = doc.at("author", default: "")
      #if author != "" [#text(size: 12pt)[#author]]
    ]
  } else if purpose == "toc" {
    set page(margin: (top: 3cm, bottom: 2.5cm, inside: 2.5cm, outside: 2.5cm))
    align(center)[
      #text(font: heading-font, size: 20pt, weight: "bold", fill: heading-color)[Contents]
      #v(0.35cm)
      #line(length: 5cm, stroke: 1pt + accent-color)
    ]
    v(0.8cm)
    outline(title: none, indent: 1.4em, depth: 2)
  } else if purpose == "chapter_opener" {
    let chapter = page-data.at("chapter_opener_data", default: (:))
    let chapter-number = chapter.at("chapter_number", default: "1")
    let chapter-title = chapter.at("chapter_title", default: "")
    v(2.2cm)
    align(center)[
      #text(font: heading-font, size: 11pt, weight: "semibold", fill: accent-color, tracking: 1.5pt)[CHAPTER]
      #v(0.2cm)
      #text(font: heading-font, size: 44pt, weight: "bold", fill: heading-color)[#chapter-number]
    ]
    v(0.6cm)
    line(length: 100%, stroke: 2pt + accent-color)
    v(0.7cm)
    heading(level: 1)[#chapter-title]
    let objectives = chapter.at("learning_objectives", default: ())
    if objectives.len() > 0 {
      v(0.5cm)
      callout-box([
        #text(weight: "bold", fill: accent-color)[Learning objectives]
        #v(0.35em)
        #for objective in objectives [
          #text[• #objective]
          #v(0.2em)
        ]
      ], "tip")
    }
  } else if purpose == "back_cover" {
    let back-cover = page-data.at("back_cover_data", default: (:))
    set page(margin: 0pt, fill: rgb(back-cover.at("background_color", default: "#1d3557")))
    align(center + horizon)[
      #text(font: heading-font, size: 18pt, weight: "bold", fill: white)[#doc.title]
      #v(0.5cm)
      #text(size: 10pt, fill: rgb("#d9e2ec"))[#back-cover.at("text", default: "A practical field manual for disciplined land investment decisions.")]
    ]
  } else {
    render-blocks(page-data.at("blocks", default: ()))
  }

  if page-index < pages.len() - 1 { pagebreak() }
}
