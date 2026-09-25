// Advanced Book Template — Complete Editorial Layout Library Integration
// This template implements the full editorial layout library for professional book production

#import "helpers.typ": callout-box, render-table, render-code, render-gallery
#import "layout_library.typ": *

#let doc = json("assets/content.json")
#let p = doc.at("preset", default: ( : ))

// ── Preset helpers ─────────────────────────────────────────────────────────────
#let body-font    = p.at("body_font",    default: "PT Serif")
#let heading-font = p.at("heading_font", default: "PT Sans")
#let mono-font    = p.at("mono_font",    default: "PT Mono")
#let accent-color = rgb(p.at("accent_color",  default: "#1d3557"))
#let head-color   = rgb(p.at("heading_color", default: "#1d3557"))
#let muted-color  = rgb(p.at("muted_color",   default: "#64748b"))
#let body-color   = rgb(p.at("body_color",    default: "#1a1a1a"))
#let text-size    = eval(p.at("text_size", default: "10.5pt"), mode: "code")
#let h1-size      = eval(p.at("h1_size",   default: "22pt"),  mode: "code")
#let h2-size      = eval(p.at("h2_size",   default: "15pt"),  mode: "code")
#let h3-size      = eval(p.at("h3_size",   default: "12pt"),  mode: "code")
#let do-number    = p.at("numbered_headings", default: true)
#let show-toc     = p.at("show_toc", default: true)
#let indent-str   = p.at("indent", default: "1.5em")
#let show-hf      = p.at("show_header_footer", default: true)
#let hdr-rule     = p.at("header_rule", default: true)
#let pn-pos       = p.at("page_num_position", default: "auto")

// Cover and front matter settings
#let cover-title-size      = eval(p.at("cover_title_size",      default: "36pt"), mode: "code")
#let cover-subtitle-size   = eval(p.at("cover_subtitle_size",   default: "18pt"), mode: "code")
#let cover-author-size     = eval(p.at("cover_author_size",     default: "14pt"), mode: "code")
#let cover-title-top-margin = eval(p.at("cover_title_top_margin", default: "4cm"), mode: "code")
#let cover-title-color      = rgb(p.at("cover_title_color",      default: "#ffffff"))
#let cover-subtitle-color   = rgb(p.at("cover_subtitle_color",   default: "#c4a35a"))
#let cover-author-color     = rgb(p.at("cover_author_color",     default: "#e2e8f0"))
#let cover-title-tracking   = eval(p.at("cover_title_tracking",   default: "-0.5pt"), mode: "code")
#let cover-bg-color         = rgb(p.at("cover_bg_color",          default: "#0f172a"))
#let cover-bg-image         = p.at("cover_bg_image",              default: "")
#let cover-ornament         = p.at("cover_ornament",              default: "")
#let cover-ornament-width   = eval(p.at("cover_ornament_width",   default: "6cm"), mode: "code")
#let cover-accent-line      = p.at("cover_accent_line",           default: true)
#let cover-accent-line-width = eval(p.at("cover_accent_line_width", default: "8cm"), mode: "code")
#let cover-title-top-margin  = eval(p.at("cover_title_top_margin", default: "4cm"), mode: "code")
#let cover-accent-line-color = rgb(p.at("cover_accent_line_color", default: "#c4a35a"))

// Title page
#let title-page-title-size   = eval(p.at("title_page_title_size",   default: "28pt"), mode: "code")
#let title-page-subtitle-size = eval(p.at("title_page_subtitle_size", default: "14pt"), mode: "code")
#let title-page-author-size   = eval(p.at("title_page_author_size",   default: "13pt"), mode: "code")

// ── Page setup (A4, professional margins) ──────────────────────────────────────
// Inner margin wider for binding, outer margin narrower
// Top/bottom margins balanced for comfortable reading
#let page-width  = p.at("paper", default: "a4")
#let margin-inner = eval(p.at("margin_inner",  default: "2.5cm"), mode: "code")
#let margin-outer = eval(p.at("margin_outer",  default: "2.0cm"), mode: "code")
#let margin-top   = eval(p.at("margin_top",    default: "2.5cm"), mode: "code")
#let margin-bottom = eval(p.at("margin_bottom", default: "2.5cm"), mode: "code")

// Watermark background
#let watermark-bg = {
  if watermark.enabled and watermark.layer == "under" {
    if watermark.pages == "all" or (watermark.pages == "front_matter" and here().page() <= 3) or (watermark.pages == "main_matter" and here().page() > 3) {
      if watermark.text != "" {
        // Text watermark - centered, rotated
        place(
          rotate(watermark.rotation,
            text(
              size: 72pt,
              fill: rgb(watermark.color),
              opacity: watermark.opacity,
              weight: "bold",
            )[#watermark.text]
          ),
          dx: 0, dy: 0
        )
      } else if watermark.image_path != "" {
        // Image watermark
        place(
          rotate(watermark.rotation,
            image(watermark.image_path, width: 40%, opacity: watermark.opacity)
          ),
          dx: 0, dy: 0
        )
      }
    }
  }
}

#set page(
  paper: page-width,
  margin: (inside: margin-inner, outside: margin-outer, top: margin-top, bottom: margin-bottom),
  background: watermark-bg,
  header: context {
    let pg = here().page()
    if show-hf and pg > 2 [
      #set text(font: heading-font, size: 7.5pt, fill: muted-color)
      #let num = counter(page).display("1")
      #if pn-pos == "auto" [
        // Classic mirrored book furniture: number rides the OUTER edge.
        #if calc.odd(pg) [#doc.title #h(1fr) #num] else [#num #h(1fr) #doc.title]
      ] else if pn-pos == "top-left" [
        #num #h(1fr) #doc.title
      ] else if pn-pos == "top-center" [
        #grid(columns: (1fr, auto, 1fr), align(left)[#doc.title], num, [])
      ] else if pn-pos == "top-right" [
        #doc.title #h(1fr) #num
      ] else [
        // bottom-* or none: header keeps only the title
        #doc.title #h(1fr)
      ]
      #v(-3pt)
      #if hdr-rule { line(length: 100%, stroke: 0.4pt + luma(210)) }
    ]
  },
  footer: context {
    let pg = here().page()
    if show-hf and pg > 2 and pn-pos.starts-with("bottom") [
      #set text(font: heading-font, size: 7.5pt, fill: muted-color)
      #align(
        if pn-pos == "bottom-left" { left }
        else if pn-pos == "bottom-center" { center }
        else { right }
      )[#counter(page).display("1")]
    ]
  },
)

// ── Typography ────────────────────────────────────────────────────────────────
#set text(
  font: body-font,
  size: text-size,
  fill: body-color,
  lang: doc.language,
  hyphenate: p.at("hyphenate", default: true),
  // Cheap hyphenation cost → justified lines pack tight instead of opening into
  // rivers (large gaps between words on sparse lines).
  costs: (hyphenation: 5%, runt: 100%, widow: 100%, orphan: 100%),
)
// 145% leading for comfortable reading
#set par(
  justify: p.at("justify", default: true),
  leading: eval(p.at("leading", default: "0.65em"), mode: "code"),
  spacing: 1.1em,
  first-line-indent: eval(indent-str, mode: "code"),
)
#show raw: set text(font: mono-font, size: 0.88em)
#show figure.caption: it => [
  #set text(font: heading-font, size: 0.78em, style: "italic", fill: muted-color)
  #set par(justify: false)
  #align(center)[#it.body]
]

// ── Heading styles ────────────────────────────────────────────────────────────
#show heading.where(level: 1): it => [
  #pagebreak(weak: true)
  #v(1.5cm)
  #align(center)[
    #set text(font: heading-font, size: h1-size, weight: "bold", fill: head-color, tracking: -0.5pt)
    #it.body
  ]
  #v(0.4cm)
  #align(center)[
    #line(length: 4cm, stroke: 1.5pt + accent-color)
  ]
  #v(1.2cm)
]
#show heading.where(level: 2): it => [
  #v(1.5em)
  #set text(font: heading-font, size: h2-size, weight: "semibold", fill: head-color)
  #it
  #v(0.5em)
]
#show heading.where(level: 3): it => [
  #v(1em)
  #set text(font: heading-font, size: h3-size, weight: "semibold", style: "italic", fill: head-color)
  #it
  #v(0.3em)
]

// ── Watermark helper ──────────────────────────────────────────────────────────
#let add-watermark(watermark) = {
  if watermark.enabled {
    // Watermark is applied via page background in the page setup
    // This is handled in the page setup below
  }
}

// Add watermark to page setup
#let watermark-bg(watermark) = {
  if watermark.enabled {
    if watermark.text != "" {
      // Text watermark
      place(
        rotate(watermark.rotation,
          text(
            size: 72pt,
            fill: rgb(watermark.color),
            opacity: watermark.opacity,
            weight: "bold",
          )[#watermark.text]
        ),
        dx: 0, dy: 0
      )
    } else if watermark.image_path != "" {
      // Image watermark
      place(
        rotate(watermark.rotation,
          image(watermark.image_path, width: 40%, opacity: watermark.opacity)
        ),
        dx: 0, dy: 0
      )
    }
  }
}

#let doc = json("assets/content.json")
#let p = doc.at("preset", default: ( : ))
#let watermark = doc.at("watermark", default: (enabled: false))

// ── Cover ─────────────────────────────────────────────────────────────────────
#set page(numbering: none, margin: 0)
#layout-functions.cover(doc, p)

#pagebreak()

// ── Title Page ────────────────────────────────────────────────────────────────
#set page(margin: (top: 5cm, bottom: 4cm, left: 3cm, right: 3cm))
#layout-functions.title-page(doc, p)

#pagebreak()

// ── Copyright Page ────────────────────────────────────────────────────────────
#layout-functions.copyright(doc, p)

#pagebreak()

// ── Table of Contents ────────────────────────────────────────────────────────
#layout-functions.toc(doc, p)

#pagebreak()

// ── Body ──────────────────────────────────────────────────────────────────────
#set page(numbering: "1")
#counter(page).update(1)

#if do-number {
  set heading(numbering: "1.1")
}

#for (si, section) in doc.sections.enumerate() {
  let lvl = section.level
  if lvl == 1 {
    // Chapter opener
    let chapter_num = si + 1
    let epigraph = section.at("epigraph", default: "")
    let epigraph_author = section.at("epigraph_author", default: "")
    let learning_objectives = section.at("learning_objectives", default: ())

    #layout-functions.chapter-opener(doc, p, chapter_num, section.title, epigraph, learning_objectives)
  }
  else if lvl == 2 { heading(level: 2)[#section.title] }
  else { heading(level: 3)[#section.title] }

  // Render section content
  let safe-content = section.content.replace("#", "\\#").replace("\\#link(", "#link(").replace("\\#footnote[", "#footnote[")

  // Books never wrap text around side floats — illustrations sit CENTERED in the
  // column (optionally captioned), and the text simply resumes underneath, the
  // way a printed book is set. Each illustration is interleaved INTO the chapter
  // (not appended after it): if it doesn't fit on the current page it moves to
  // the top of the next one and the remaining prose follows right below it, so a
  // picture is never stranded alone on a near-empty sheet.
  let book-fig(img) = {
    let w = img.at("width", default: "85%")
    if w == "full" { w = "100%" }
    v(0.9em, weak: true)
    figure(
      image(img.at("_local", default: img.path), width: eval(w, mode: "code")),
      caption: if img.at("caption", default: "") != "" { [#img.caption] } else { none },
      supplement: none,
    )
    v(0.9em, weak: true)
  }

  // position "top" → the illustration opens the chapter, BEFORE any text
  // (frontispiece, the way picture books start). The rest interleave evenly.
  let top-imgs  = section.images.filter(im => im.at("position", default: "auto") == "top")
  let flow-imgs = section.images.filter(im => im.at("position", default: "auto") != "top")

  for im in top-imgs { book-fig(im) }

  // Render section content directly (simplified for Typst 0.15 compat)
  eval(safe-content, mode: "markup")

  // Render flow images sequentially (simplified - no paragraph interleaving)
  for im in flow-imgs { book-fig(im) }

  for gal in section.at("galleries", default: ()) { render-gallery(gal) }
  for tbl in section.tables { render-table(tbl) }
  for cb in section.code_blocks { render-code(cb, mono-font) }
  for co in section.callouts { callout-box(co.at("text"), co.kind) }
}

// ── Back Cover ────────────────────────────────────────────────────────────────
#set page(margin: 0)
#layout-functions.cover(doc, p)