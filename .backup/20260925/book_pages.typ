// ============================================================================
//  Land Investor's Field Manual — document template
// ----------------------------------------------------------------------------
//  Two constraints govern this file:
//
//  1. Every binding used by `set page` is declared ABOVE the `set page` call.
//     Typst resolves `set` arguments at the point they are written, so a later
//     binding reads as an unknown variable.
//  2. The running head and footer are produced by functions. The earlier
//     `#if cond [..] else if cond [..]` chain written inside `context` was
//     parsed as markup, so the literal `else if page-number-position == ...`
//     source was typeset into the header of every page. A function body is a
//     code expression, where the braced `if/else` chain parses correctly.
// ============================================================================

#import "helpers.typ": *
#import "layout_library.typ": resolve-layout

#let doc = json("assets/content.json")
#let preset = doc.at("preset", default: (:))
#let pages = doc.at("pages", default: ())
#let th = theme(preset)

#let book-title = str(doc.at("title", default: ""))
#let show-running = preset.at("show_header_footer", default: true)
#let header-rule = preset.at("header_rule", default: true)
#let page-number-position = str(preset.at("page_num_position", default: "bottom-center"))
#let page-w = dim(preset.at("page_width", default: "210mm"), 210mm)
#let page-h = dim(preset.at("page_height", default: "297mm"), 297mm)
#let m-top = dim(preset.at("margin_top", default: "25mm"), 25mm)
#let m-bottom = dim(preset.at("margin_bottom", default: "24mm"), 24mm)
#let m-inner = dim(preset.at("margin_inner", default: "26mm"), 26mm)
#let m-outer = dim(preset.at("margin_outer", default: "22mm"), 22mm)
#let skip-head = 4
#let skip-foot = 4

// ── Running head / foot ─────────────────────────────────────────────────────
#let running-head() = context {
  if show-running and here().page() > skip-head {
    let running-title = text(
      upper(book-title),
      font: th.heading-font,
      size: 7.5pt,
      fill: th.slate,
      tracking: 0.9pt,
    )
    let folio = text(counter(page).display("1"), font: th.heading-font, size: 7.5pt, weight: "bold", fill: th.brass)
    set text(font: th.heading-font, size: 7.5pt, fill: th.slate, tracking: 0.9pt)
    if page-number-position in ("top-left", "top-center", "top-right") {
      box(width: 100%)[
        #set par(justify: false, first-line-indent: 0em)
        #if page-number-position == "top-left" {
          grid(columns: (auto, 1fr), folio, align(right)[#running-title])
        } else if page-number-position == "top-center" {
          grid(columns: (1fr, auto, 1fr), align(center)[#running-title], folio, [])
        } else {
          grid(columns: (1fr, auto), align(left)[#running-title], folio)
        }
      ]
      if header-rule {
        v(0.35em)
        line(length: 100%, stroke: 0.4pt + th.rule)
      }
      v(0.6em)
    }
  }
}

#let running-foot() = context {
  if show-running and here().page() > skip-foot and not page-number-position.starts-with("top") {
    let n = text(counter(page).display("1"), font: th.heading-font, size: 7.5pt, weight: "bold", fill: th.slate, tracking: 1pt)
    set text(font: th.heading-font, size: 7.5pt, fill: th.slate, tracking: 0.9pt)
    box(width: 100%)[
      #set par(justify: false, first-line-indent: 0em)
      #line(length: 100%, stroke: 0.4pt + th.rule)
      #v(0.45em)
      #if page-number-position == "bottom-left" {
        grid(columns: (auto, 1fr), n, align(right)[#upper(book-title)])
      } else if page-number-position == "bottom-right" {
        grid(columns: (1fr, auto), align(left)[#upper(book-title)], n)
      } else {
        align(center)[#n]
      }
    ]
  }
}

// ── Page geometry ───────────────────────────────────────────────────────────
#set page(
  width: page-w,
  height: page-h,
  margin: (top: m-top, bottom: m-bottom, inside: m-inner, outside: m-outer),
  header: running-head(),
  footer: running-foot(),
)

// ── Base typography ─────────────────────────────────────────────────────────
#set text(
  font: th.body-font,
  size: th.text-size,
  fill: th.ink,
  lang: str(doc.at("language", default: "en")),
  hyphenate: preset.at("hyphenate", default: true),
)

#set par(
  justify: preset.at("justify", default: true),
  leading: th.lead,
  spacing: th.par-space,
  first-line-indent: 0em,
)

#show raw: set text(font: th.mono-font, size: th.text-size * 0.84)
#show link: set text(fill: th.terracotta)

// Chapter titles are the only level-1 headings in this book, so the display
// treatment belongs to every level-1 heading.
#show heading.where(level: 1): it => block(
  width: 100%,
  breakable: false,
  below: 0.9em,
  above: 0.7em,
)[
  #set par(justify: false, first-line-indent: 0em, leading: 1.06em)
  #text(font: th.heading-font, size: th.h1-size + 5pt, weight: "bold", fill: th.ink, tracking: -0.3pt)[#it.body]
]

#show heading.where(level: 2): it => block(
  width: 100%,
  breakable: false,
  below: 0.45em,
  above: 1.25em,
)[
  #set par(justify: false, first-line-indent: 0em, leading: 1.15em)
  #text(font: th.heading-font, size: th.h2-size, weight: "bold", fill: th.ink)[#it.element.body]
  #v(0.35em)
  #line(length: 1.3cm, stroke: 0.9pt + th.brass)
]

#show heading.where(level: 3): it => block(
  width: 100%,
  breakable: false,
  below: 0.3em,
  above: 0.95em,
)[
  #set par(justify: false, first-line-indent: 0em, leading: 1.15em)
  #text(font: th.heading-font, size: th.h3-size, weight: "bold", fill: th.slate, tracking: 0.2pt)[#it.body]
]

// Outline entries inherit the editorial voice. `outline.entry` carries only
// `level`, `element` and `fill`; `it.body()` / `it.page()` / `it.indented()`
// are contextual helpers, and they must be called, not accessed as fields.
#show outline.entry.where(level: 1): it => block(breakable: false, below: 0.6em)[
  #set par(justify: false, first-line-indent: 0em)
  #v(0.55em)
  #it.indented(it.prefix(), [
    #text(font: th.heading-font, size: th.label-size + 1.5pt, weight: "bold", fill: th.ink)[#it.body()]
    #h(0.6em)
    #text(font: th.heading-font, size: th.micro-size, weight: "bold", fill: th.brass)[#it.page()]
  ])
]

#show outline.entry.where(level: 2): it => block(breakable: false, below: 0.26em)[
  #set par(justify: false, first-line-indent: 0em)
  #it.indented(it.prefix(), [
    #text(font: th.body-font, size: th.text-size * 0.88, fill: th.slate)[#it.body()]
    #h(0.35em)
    #box(width: 1fr, it.fill)
    #h(0.35em)
    #text(font: th.heading-font, size: th.micro-size, fill: th.slate)[#it.page()]
  ])
]

// ── Emit the book ───────────────────────────────────────────────────────────
#for pg in pages {
  resolve-layout(pg.at("layout_function", default: "reading"))(pg, doc, th)
  if pg != pages.last() { pagebreak() }
}
