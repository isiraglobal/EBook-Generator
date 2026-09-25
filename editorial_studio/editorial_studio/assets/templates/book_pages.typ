// Book Pages Template — Page-based rendering matching original book.typ structure
#import "helpers.typ": callout-box, render-table, render-code, render-gallery

#let doc = json("assets/content.json")
#let p = doc.at("preset", default: ())
#let pages = doc.at("pages", default: ())

// ── Preset helpers ─────────────────────────────────────────────────────────────
#let body-font    = p.at("body_font",    default: "PT Serif")
#let heading-font = p.at("heading_font", default: "PT Sans")
#let mono-font    = p.at("mono_font",    default: "PT Mono")
#let accent-color = rgb(p.at("accent_color",  default: "8b0000"))
#let head-color   = rgb(p.at("heading_color", default: "1a1a1a"))
#let muted-color  = rgb(p.at("muted_color",   default: "888888"))
#let body-color   = rgb(p.at("body_color",    default: "1a1a1a"))
#let text-size    = eval(p.at("text_size", default: "10pt"),  mode: "code")
#let h1-size      = eval(p.at("h1_size",   default: "18pt"),  mode: "code")
#let h2-size      = eval(p.at("h2_size",   default: "13pt"),  mode: "code")
#let h3-size      = eval(p.at("h3_size",   default: "11pt"),  mode: "code")
#let do-number    = p.at("numbered_headings", default: false)
#let show-toc     = p.at("show_toc", default: true)
#let indent-str   = p.at("indent", default: "1.5em")
// Running header & page numbers
#let show-hf  = p.at("show_header_footer", default: true)
#let hdr-rule = p.at("header_rule", default: true)
#let pn-pos   = p.at("page_num_position", default: "auto")

// ── Global Page Setup ──────────────────────────────────────────────────────────
#set page(
  paper: p.at("paper", default: "a5"),
  margin: (inside: eval(p.at("margin_left", default: "2.0cm"), mode: "code"), 
           outside: eval(p.at("margin_right", default: "3.5cm"), mode: "code"), 
           top: eval(p.at("margin_top", default: "2.5cm"), mode: "code"), 
           bottom: eval(p.at("margin_bottom", default: "4.0cm"), mode: "code")),
  header: context {
    let pg = here().page()
    if show-hf and pg > 2 [
      set text(font: heading-font, size: 7.5pt, fill: muted-color)
      if pn-pos == "auto" [
        if calc.odd(pg) [#doc.title #h(1fr) #counter(page).display("1")] else [#counter(page).display("1") #h(1fr) #doc.title]
      ] else if pn-pos == "top-left" [
        #counter(page).display("1") #h(1fr) #doc.title
      ] else if pn-pos == "top-center" [
        #grid(columns: (1fr, auto, 1fr), align(left)[#doc.title], counter(page).display("1"), [])
      ] else if pn-pos == "top-right" [
        #doc.title #h(1fr) #counter(page).display("1")
      ] else [
        #doc.title #h(1fr) #doc.title
      ]
      #v(-3pt)
      #if hdr-rule { line(length: 100%, stroke: 0.4pt + luma(210)) }
    ]
  },
  footer: context {
    let pg = here().page()
    if show-hf and pg > 2 and pn-pos.starts-with("bottom") [
      set text(font: heading-font, size: 7.5pt, fill: muted-color)
      align(
        if pn-pos == "bottom-left" { left }
        else if pn-pos == "bottom-center" { center }
        else { right }
      )[counter(page).display("1")]
    ]
  },
)

// ── Typography ────────────────────────────────────────────────────────────────
#set text(
  font: body-font,
  size: text-size,
  fill: body-color,
  lang: doc.language,
  hyphenate: true,
  costs: (hyphenation: 5%, runt: 100%, widow: 100%, orphan: 100%),
)
#set par(
  justify: true,
  leading: eval(p.at("leading", default: "0.65em"), mode: "code"),
  spacing: 0.75em,
  first-line-indent: eval(indent-str, mode: "code"),
)
#show raw: set text(font: mono-font, size: 0.88em)
#show figure.caption: it => [
  set text(font: heading-font, size: 0.8em, style: "italic", fill: muted-color)
  set par(justify: false)
  align(center)[it.body]
]

// ── Heading styles ────────────────────────────────────────────────────────────
#show heading.where(level: 1): it => [
  pagebreak(weak: true)
  v(1.2cm)
  align(center)[
    set text(font: heading-font, size: h1-size, weight: "bold", fill: head-color, tracking: -0.5pt)
    it.body
  ]
  v(0.3cm)
  align(center)[
    line(length: 3cm, stroke: 1pt + accent-color)
  ]
  v(1cm)
]
#show heading.where(level: 2): it => [
  v(1.3em)
  set text(font: heading-font, size: h2-size, weight: "semibold", fill: head-color)
  it
  v(0.4em)
]
#show heading.where(level: 3): it => [
  v(0.9em)
  set text(font: heading-font, size: h3-size, weight: "semibold", style: "italic", fill: head-color)
  it
  v(0.25em)
]

// ── Helper functions ───────────────────────────────────────────────────────────
#let render-table(tbl) = {
  v(0.7em)
  let aligns = tbl.at("align", default: ())
  let h-align = tbl.at("h_align", default: ())
  table(
    columns: tbl.headers.len(),
    fill: (x, y) => if y == 0 { p.at("table_header", default: rgb("f1f1f1")) } else if calc.odd(y) { p.at("table_row_alt", default: rgb("fafafa")) } else { white },
    stroke: (x, y) => if y == 0 { 0.8pt + p.at("accent_color", default: rgb("1d3557")) } else { 0.4pt + luma(220) },
    align: if aligns.len() > 0 { aligns } else { (y, x) => if x == 0 { left } else { center } },
    h-align: if h-align.len() > 0 { h-align } else { (y, x) => if x == 0 { left } else { center } },
    inset: 6pt,
    ..tbl.headers.map(h => [text(weight: "bold", size: 9pt)[h]]),
    ..tbl.rows.flatten().map(cell => [text(size: 9pt)[cell]]),
  )
  v(0.7em)
}

#let render-code(cb, mono-font) = {
  v(0.5em)
  block(fill: luma(245), inset: 10pt, radius: 3pt, width: 100%)[
    set text(font: mono-font, size: 9pt)
    cb.code
  ]
  v(0.5em)
}

#let render-gallery(gal) = {
  v(1em)
  let cols = gal.at("columns", default: 3)
  let imgs = gal.images
  grid(
    columns: cols,
    gutter: 0.5em,
    ..imgs.map(img => [
      figure(
        image(img.path, width: 100%),
        caption: [#img.caption],
      )
    ]),
  )
  v(1em)
}

#let callout-colors = (
  info:    (bg: rgb("e8f4fd"), border: rgb("2980b9"), icon: "ℹ"),
  warning: (bg: rgb("fef9e7"), border: rgb("e67e22"), icon: "⚠"),
  tip:     (bg: rgb("eafaf1"), border: rgb("27ae60"), icon: "✓"),
  danger:  (bg: rgb("fdf2f2"), border: rgb("c0392b"), icon: "✗"),
  quote:   (bg: rgb("faf6ef"), border: rgb("c8b48a"), icon: "❝"),
)

#let callout-box(body, kind) = {
  let colors = callout-colors.at(kind, default: callout-colors.info)
  v(0.6em)
  block(
    width: 100%,
    fill: colors.bg,
    stroke: (left: 3pt + colors.border),
    inset: (left: 11pt, right: 9pt, top: 8pt, bottom: 8pt),
    radius: (right: 3pt),
  )[
    #set text(size: 0.92em)
    body
  ]
  v(0.6em)
}

// ── MAIN CONTENT: Page rendering loop ─────────────────────────────────────────
{
  for pg in pages {
    let pg_num = pg.at("page_number", default: 0)
    let purpose = pg.at("purpose", default: "content")
    let layout_family = pg.at("layout_family", default: "reading")
    
    // Page setup for this specific page
    let pg_width = pg.at("width_mm", default: 148) * 1mm
    let pg_height = pg.at("height_mm", default: 210) * 1mm
    let pg_margins = pg.at("margins")
    if pg_margins == none { pg_margins = () }
    
    set page(
      width: pg_width,
      height: pg_height,
      margin: (top: (pg_margins.at("top_mm", default: 25) * 1mm),
               bottom: (pg_margins.at("bottom_mm", default: 25) * 1mm),
               inside: (pg_margins.at("left_mm", default: 25) * 1mm),
               outside: (pg_margins.at("right_mm", default: 25) * 1mm)),
    )
    
    // Render page based on purpose
    if pg.purpose == "cover" {
      let cover_data = pg.at("cover_data", default: ())
      let cover_bg_image = cover_data.at("cover_bg_image", default: "")
      let cover_bg_color_str = cover_data.at("cover_bg_color", default: "ffffff")
      let cover_bg_color = rgb(cover_bg_color_str)
      let cover_title_top_margin = cover_data.at("cover_title_top_margin", default: 3cm)
      let cover_ornament = cover_data.at("cover_ornament", default: "")
      let cover_ornament_width = cover_data.at("cover_ornament_width", default: 3cm)
      let cover_title_size = cover_data.at("cover_title_size", default: 36pt)
      let cover_title_color = rgb(cover_data.at("cover_title_color", default: "1a1a1a"))
      let cover_title_tracking = cover_data.at("cover_title_tracking", default: 0pt)
      let cover_subtitle_size = cover_data.at("cover_subtitle_size", default: 18pt)
      let cover_subtitle_color = rgb(cover_data.at("cover_subtitle_color", default: "666666"))
      let cover_accent_line = cover_data.at("cover_accent_line", default: true)
      let cover_accent_line_width = cover_data.at("cover_accent_line_width", default: 8cm)
      let cover_author_size = cover_data.at("cover_author_size", default: 14pt)
      let cover_author_color = rgb(cover_data.at("cover_author_color", default: "666666"))
      let cover_bottom_text = cover_data.at("cover_bottom_text", default: "")
      
      set page(margin: (top: 0pt, bottom: 0pt, left: 0pt, right: 0pt))
      set text(font: p.heading_font)

      if cover_bg_image != "" {
        place(
          image(cover_bg_image, width: 100%, height: 100%, fit: "cover")
        )
      } else {
        set page(fill: cover_bg_color)
      }

      align(center + horizon)[
        v(cover_title_top_margin)
        if cover_ornament != "" {
          image(cover_ornament, width: cover_ornament_width)
          v(1.5em)
        }
        text(size: cover_title_size, weight: "bold", fill: cover_title_color, tracking: cover_title_tracking)[doc.title]
        v(0.8em)
        if doc.subtitle != "" {
          text(size: cover_subtitle_size, fill: cover_subtitle_color, style: "italic")[doc.subtitle]
          v(1.5em)
        }
        if cover_accent_line {
          line(length: cover_accent_line_width, stroke: 2pt + accent-color)
          v(1.5em)
        }
        if doc.author != "" {
          text(size: cover_author_size, fill: cover_author_color, style: "italic")[doc.author]
          v(1em)
        }
        if p.publisher != "" {
          v(3cm)
          text(size: 12pt, fill: luma(100))[p.publisher]
          if p.publisher_logo != "" {
            v(0.5em)
            image(p.publisher_logo, width: 3cm)
          }
        }
        v(2cm)
        if cover_bottom_text != "" {
          text(size: 10pt, fill: luma(120))[cover_bottom_text]
        }
      ]
    } else if pg.purpose == "title_page" {
      let title_data = pg.at("title_data", default: ())
      let title_page_title_size = title_data.at("title_page_title_size", default: 28pt)
      let title_page_subtitle_size = title_data.at("title_page_subtitle_size", default: 14pt)
      let title_page_author_size = title_data.at("title_page_author_size", default: 13pt)
      let title_page_bottom_text = title_data.at("title_page_bottom_text", default: "")
      
      set page(paper: p.paper, margin: (top: 4cm, bottom: 4cm, left: 3cm, right: 3cm))
      align(center + horizon)[
        v(3cm)
        line(length: 8cm, stroke: 1.5pt + accent-color)
        v(1.2em)
        text(size: title_page_title_size, weight: "bold", fill: head-color, tracking: -0.5pt)[doc.title]
        v(1em)
        if doc.subtitle != "" {
          text(size: title_page_subtitle_size, fill: muted-color, style: "italic")[doc.subtitle]
          v(1.5em)
        }
        line(length: 8cm, stroke: 1.5pt + accent-color)
        v(2.5em)
        if doc.author != "" {
          text(size: title_page_author_size, fill: muted-color, style: "italic")[doc.author]
          v(1em)
        }
        if p.publisher != "" {
          v(2.5em)
          line(length: 6cm, stroke: 1pt + luma(180))
          v(1em)
          text(size: 14pt, fill: muted-color)[p.publisher]
          v(0.5em)
          text(size: 11pt, fill: luma(120))[p.publisher_location]
        }
        v(3cm)
        if title_page_bottom_text != "" {
          text(size: 10pt, fill: luma(120))[title_page_bottom_text]
        }
      ]
    } else if pg.purpose == "copyright" {
      let copyright_data = pg.at("copyright_data", default: ())
      set page(paper: p.paper, margin: (top: 5cm, bottom: 3cm, left: 3cm, right: 3cm))
      set text(font: p.body_font, size: 9.5pt, fill: body-color, lang: doc.language)

      [
        set par(justify: false, leading: 1.5em, spacing: 0.5em)

        text(weight: "bold", size: 11pt)[Copyright]
        v(0.8em)

        copyright_data.at("copyright_notice", default: "")
        v(0.5em)

        copyright_data.at("isbn_line", default: "")
        v(0.5em)

        copyright_data.at("edition_line", default: "")
        v(0.5em)

        copyright_data.at("publisher_line", default: "")
        v(0.5em)

        copyright_data.at("credits_line", default: "")
        v(1em)

        copyright_data.at("disclaimer", default: "")
        v(1.5em)

        copyright_data.at("printed_in", default: "")
      ]
    } else if pg.purpose == "toc" {
      set page(paper: p.paper, margin: (top: 3cm, bottom: 3cm, left: 3cm, right: 3cm))
      set text(font: p.heading_font, fill: head-color)

      align(center)[
        text(size: 16pt, weight: "bold")[Table of Contents]
        v(0.5em)
        line(length: 6cm, stroke: 1.5pt + accent-color)
        v(1.5em)
      ]

      set text(font: p.body_font, fill: body-color, size: 10.5pt)
      set par(justify: true, leading: 1.4em, spacing: 0.4em)

      outline(title: none, indent: 1.5em, depth: 3)
      v(2cm)

      align(center)[
        text(size: 9pt, fill: luma(100))[counter(page).display("i")]
      ]
    } else if pg.purpose == "chapter_opener" {
      let chapter_opener_data = pg.at("chapter_opener_data", default: ())
      let chapter_number = chapter_opener_data.at("chapter_number", default: "1")
      let chapter_title = chapter_opener_data.at("chapter_title", default: "")
      let epigraph = chapter_opener_data.at("epigraph", default: "")
      let epigraph_author = chapter_opener_data.at("epigraph_author", default: "")
      let learning_objectives = chapter_opener_data.at("learning_objectives", default: ())
      
      set page(paper: p.paper, margin: (inside: eval(p.margin_inner, mode: "code"), outside: eval(p.margin_outer, mode: "code"), top: eval(p.margin_top, mode: "code"), bottom: eval(p.margin_bottom, mode: "code")))

      v(3cm)
      align(center)[
        text(size: 13pt, weight: "semibold", fill: accent-color, tracking: 2pt)[CHAPTER]
        v(0.2em)
        text(size: 48pt, weight: "bold", fill: head-color, tracking: -1pt)[chapter_number]
      ]
      v(1em)
      align(center)[
        line(length: 8cm, stroke: 2pt + accent-color)
      ]
      v(1.5em)

      align(center)[
        text(size: 28pt, weight: "bold", fill: head-color, tracking: -1pt)[chapter_title]
      ]
      v(1.5em)

      if epigraph != "" {
        v(2em)
        align(center + horizon)[
          block(width: 70%)[
            set text(size: 12pt, style: "italic", fill: muted-color)
            set par(justify: false, leading: 1.5em)
            epigraph
            v(0.8em)
            align(right)[text(size: 10pt, fill: luma(100))["— " + epigraph_author]]
          ]
        ]
        v(2em)
      }

      if learning_objectives.len() > 0 {
        v(2em)
        block(fill: p.sidebar_bg, inset: 16pt, radius: 4pt, width: 100%)[
          text(size: 11pt, weight: "semibold", fill: accent-color)[Learning Objectives]
          v(0.6em)
          for obj in learning_objectives {
            v(0.3em)
            text(size: 10.5pt)[• obj]
          }
        ]
      }
      v(3cm)
    } else if pg.purpose == "glossary" {
      let glossary_data = pg.at("glossary_data", default: (entries: ()))
      set page(paper: p.paper, margin: (top: 3cm, bottom: 3cm, left: 3cm, right: 3cm))
      set text(font: p.body_font, fill: body-color, size: 10.5pt)
      set par(justify: true, leading: 1.4em, spacing: 0.4em)

      align(center)[
        text(size: 16pt, weight: "bold")[Glossary]
        v(0.5em)
        line(length: 6cm, stroke: 1.5pt + accent-color)
        v(1.5em)
      ]

      for entry in glossary_data.entries {
        v(0.5em)
        text(weight: "bold")[entry.term]
        v(0.2em)
        text[entry.definition]
      }
    } else if pg.purpose == "references" {
      let references_data = pg.at("references_data", default: (entries: ()))
      set page(paper: p.paper, margin: (top: 3cm, bottom: 3cm, left: 3cm, right: 3cm))
      set text(font: p.body_font, fill: body-color, size: 10.5pt)
      set par(justify: true, leading: 1.4em, spacing: 0.4em)

      align(center)[
        text(size: 16pt, weight: "bold")[References]
        v(0.5em)
        line(length: 6cm, stroke: 1.5pt + accent-color)
        v(1.5em)
      ]

      for ref in references_data.entries {
        v(0.5em)
        text[ref]
      }
    } else if pg.purpose == "back_cover" {
      let cover_bg_image = pg.at("cover_bg_image", default: "")
      let cover_bg_color_str = pg.at("cover_bg_color", default: "ffffff")
      let cover_bg_color = rgb(cover_bg_color_str)
      let back_cover_text = pg.at("back_cover_text", default: "")
      
      set page(margin: (top: 0pt, bottom: 0pt, left: 0pt, right: 0pt))
      set text(font: p.heading_font)

      if cover_bg_image != "" {
        place(
          image(cover_bg_image, width: 100%, height: 100%, fit: "cover")
        )
      } else {
        set page(fill: cover_bg_color)
      }

      align(center + horizon)[
        v(2cm)
        if back_cover_text != "" {
          text(size: 14pt, fill: luma(100))[back_cover_text]
        }
      ]
    } else {
      // Content, exercise, recap pages - render blocks
      for blk in pg.blocks {
        render-block(blk)
      }
    }
    
    if pg_num < pages.len() {
      pagebreak()
    }
  }
}

// ── Helper functions ───────────────────────────────────────────────────────────
#let render-table(tbl) = {
  v(0.7em)
  let aligns = tbl.at("align", default: ())
  let h-align = tbl.at("h_align", default: ())
  table(
    columns: tbl.headers.len(),
    fill: (x, y) => if y == 0 { p.at("table_header", default: rgb("f1f1f1")) } else if calc.odd(y) { p.at("table_row_alt", default: rgb("fafafa")) } else { white },
    stroke: (x, y) => if y == 0 { 0.8pt + p.at("accent_color", default: rgb("1d3557")) } else { 0.4pt + luma(220) },
    align: if aligns.len() > 0 { aligns } else { (y, x) => if x == 0 { left } else { center } },
    h-align: if h-align.len() > 0 { h-align } else { (y, x) => if x == 0 { left } else { center } },
    inset: 6pt,
    ..tbl.headers.map(h => [text(weight: "bold", size: 9pt)[h]]),
    ..tbl.rows.flatten().map(cell => [text(size: 9pt)[cell]]),
  )
  v(0.7em)
}

#let render-code(cb, mono-font) = {
  v(0.5em)
  block(fill: luma(245), inset: 10pt, radius: 3pt, width: 100%)[
    set text(font: mono-font, size: 9pt)
    cb.code
  ]
  v(0.5em)
}

#let render-gallery(gal) = {
  v(1em)
  let cols = gal.at("columns", default: 3)
  let imgs = gal.images
  grid(
    columns: cols,
    gutter: 0.5em,
    ..imgs.map(img => [
      figure(
        image(img.path, width: 100%),
        caption: [#img.caption],
      )
    ]),
  )
  v(1em)
}

#let callout-colors = (
  info:    (bg: rgb("e8f4fd"), border: rgb("2980b9"), icon: "ℹ"),
  warning: (bg: rgb("fef9e7"), border: rgb("e67e22"), icon: "⚠"),
  tip:     (bg: rgb("eafaf1"), border: rgb("27ae60"), icon: "✓"),
  danger:  (bg: rgb("fdf2f2"), border: rgb("c0392b"), icon: "✗"),
  quote:   (bg: rgb("faf6ef"), border: rgb("c8b48a"), icon: "❝"),
)

#let callout-box(body, kind) = {
  let colors = callout-colors.at(kind, default: callout-colors.info)
  v(0.6em)
  block(
    width: 100%,
    fill: colors.bg,
    stroke: (left: 3pt + colors.border),
    inset: (left: 11pt, right: 9pt, top: 8pt, bottom: 8pt),
    radius: (right: 3pt),
  )[
    #set text(size: 0.92em)
    body
  ]
  v(0.6em)
}

// ── Render a single block ─────────────────────────────────────────────────────
#let render-block(blk) = {
  let type = blk.at("type", default: "paragraph")
  let content = blk.at("content", default: "")
  
  if type == "heading" {
    let level = blk.at("level", default: 1)
    heading(level: level)[content]
  } else if type == "paragraph" {
    eval(content, mode: "markup")
  } else if type == "definition" {
    let def = blk.at("definition", default: (:))
    callout-box(def.at("definition", default: content), "info")
  } else if type == "table" {
    let tbl = blk.at("table", default: (:))
    render-table(tbl)
  } else if type == "code" {
    let cb = blk.at("code", default: (:))
    render-code(cb, mono-font)
  } else if type == "image_instruction" {
    let img = blk.at("image", default: (:))
    let w = img.at("width", default: "85%")
    if w == "full" { w = "100%" }
    let cap = img.at("caption", default: "")
    let caption_content = if cap != "" { cap } else { none }
    v(0.9em, weak: true)
    figure(
      image(img.at("path", default: ""), width: eval(w, mode: "code")),
      caption: caption_content,
      supplement: none,
    )
    v(0.9em, weak: true)
  } else if type == "exercise" {
    let ex = blk.at("exercise", default: (:))
    callout-box([
      set text(weight: "bold", fill: accent-color)
      ex.at("title", default: "Exercise")
      v(0.5em)
      if ex.at("instructions", default: "") != "" [
        set text(size: 9pt, style: "italic", fill: muted-color)
        ex.instructions
        v(0.5em)
      ]
      content
      v(1em)
      if ex.at("hints", default: ()).len() > 0 [
        block(fill: luma(255, 245, 230), inset: 12pt, radius: 3pt, width: 100%, stroke: (left: 3pt + accent-color))[
          set text(weight: "semibold", fill: accent-color)
          "💡 Hint"
          v(0.3em)
          for hint in ex.hints {
            v(0.2em)
            text(size: 10pt)[hint]
          }
        ]
        v(0.8em)
      ]
      if ex.at("response_type", default: "lines") == "lines" {
        for i in range(ex.at("response_lines", default: 5)) {
          v(0.8em)
          line(length: 100%, stroke: 0.5pt + luma(200))
        }
      }
    ], "exercise")
  } else if type == "worked_example" {
    let we = blk.at("worked_example", default: (:))
    v(1em)
    block(fill: p.sidebar_bg, inset: 16pt, radius: 4pt, width: 100%)[
      text(size: 13pt, weight: "bold", fill: accent-color)[Worked Example]
      if we.at("title", default: "") != "" [
        v(0.2em)
        text(size: 11pt, fill: muted-color)[we.title]
      ]
      v(1em)
      if we.at("problem", default: "") != "" [
        text(weight: "semibold", fill: accent-color)[Problem]
        v(0.4em)
        we.problem
        v(1em)
      ]
      if we.at("given", default: ()).len() > 0 [
        text(weight: "semibold", fill: accent-color)[Given]
        v(0.4em)
        for item in we.given {
          v(0.3em)
          text(size: 10.5pt)[• item]
        ]
        v(1em)
      ]
      text(weight: "semibold", fill: accent-color)[Solution]
      v(0.4em)
      if we.at("steps", default: ()).len() > 0 {
        for step in we.steps {
          v(0.5em)
          text(weight: "semibold", fill: accent-color)[Step step.number]
          v(0.3em)
          step.description
          if step.calculation != "" {
            v(0.4em)
            block(fill: luma(245), inset: 10pt, radius: 3pt, width: 100%)[
              set text(font: mono-font, size: 9.5pt)
              step.calculation
            ]
          }
          if step.explanation != "" {
            v(0.3em)
            text(size: 9.5pt, fill: muted-color, style: "italic")[step.explanation]
          }
        }
      } else {
        we.solution
      }
      v(1em)
      if we.at("answer", default: "") != "" {
        block(fill: accent-color + luma(5), inset: 12pt, radius: 4pt, width: 100%)[
          text(weight: "semibold", fill: accent-color)[Answer: ]
          text(fill: accent-color)[we.answer]
        ]
      }
    ]
    v(1em)
  } else if type == "warning" or type == "callout" {
    let co = blk.at("callout", default: (:))
    callout-box(co.at("text", default: content), co.at("kind", default: "info"))
  } else if type == "quotation" {
    let pq = blk.at("pull_quote", default: (:))
    v(1em)
    align(center)[
      block(width: 80%)[
        set text(style: "italic", size: 1.1em, fill: body-color)
        set par(justify: false, leading: 1.3em)
        "“pq.text”"
        if pq.author != "" {
          v(0.5em)
          align(right)[text(size: 0.9em, fill: muted-color)["— " + pq.author]]
        }
      ]
    ]
    v(1em)
  } else if type == "footnote" {
    footnote[content]
  } else {
    eval(content, mode: "markup")
  }
}