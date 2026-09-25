// Editorial Layout Library — Fixed for Typst 0.15 compatibility
// All functions use correct code-mode syntax (no # prefixes inside function bodies)
// FIXED: No nested blocks inside for loops (Typst limitation)

// ── Layout Family: COVER ────────────────────────────────────────────────────────
#let layout-cover(doc, p) = {
  set page(paper: p.paper, margin: 0)
  set text(font: p.heading_font)

  if p.cover_bg_image != "" {
    place(
      image(p.cover_bg_image, width: 100%, height: 100%, fit: "cover")
    )
  } else {
    set page(fill: p.cover_bg_color)
  }

  align(center + horizon)[
    v(p.cover_title_top_margin)
    if p.cover_ornament != "" {
      image(p.cover_ornament, width: p.cover_ornament_width)
      v(1.5em)
    }
    text(size: p.cover_title_size, weight: "bold", fill: p.cover_title_color, tracking: p.cover_title_tracking)[doc.title]
    v(0.8em)
    if doc.subtitle != "" {
      text(size: p.cover_subtitle_size, fill: p.cover_subtitle_color, style: "italic")[doc.subtitle]
      v(1.5em)
    }
    if p.cover_accent_line {
      line(length: p.cover_accent_line_width, stroke: 2pt + p.accent_color)
      v(1.5em)
    }
    if doc.author != "" {
      text(size: p.cover_author_size, fill: p.cover_author_color, style: "italic")[doc.author]
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
    if p.cover_bottom_text != "" {
      text(size: 10pt, fill: luma(120))[p.cover_bottom_text]
    }
  ]
}

// ── Layout Family: TITLE PAGE ───────────────────────────────────────────────────
#let layout-title-page(doc, p) = {
  set page(paper: p.paper, margin: (top: 4cm, bottom: 4cm, left: 3cm, right: 3cm))
  align(center + horizon)[
    v(3cm)
    line(length: 8cm, stroke: 1.5pt + p.accent_color)
    v(1.2em)
    text(size: p.title_page_title_size, weight: "bold", fill: p.heading_color, tracking: -0.5pt)[doc.title]
    v(1em)
    if doc.subtitle != "" {
      text(size: p.title_page_subtitle_size, fill: p.muted_color, style: "italic")[doc.subtitle]
      v(1.5em)
    }
    line(length: 8cm, stroke: 1.5pt + p.accent_color)
    v(2.5em)
    if doc.author != "" {
      text(size: p.title_page_author_size, fill: p.muted_color, style: "italic")[doc.author]
      v(1em)
    }
    if p.publisher != "" {
      v(2.5em)
      line(length: 6cm, stroke: 1pt + luma(180))
      v(1em)
      text(size: 14pt, fill: p.muted_color)[p.publisher]
      v(0.5em)
      text(size: 11pt, fill: luma(120))[p.publisher_location]
    }
    v(3cm)
    if p.title_page_bottom_text != "" {
      text(size: 10pt, fill: luma(120))[p.title_page_bottom_text]
    }
  ]
}

// ── Layout Family: COPYRIGHT ────────────────────────────────────────────────────
#let layout-copyright(doc, p) = {
  set page(paper: p.paper, margin: (top: 5cm, bottom: 3cm, left: 3cm, right: 3cm))
  set text(font: p.body_font, size: 9.5pt, fill: p.body_color, lang: doc.language)

  [
    set par(justify: false, leading: 1.5em, spacing: 0.5em)

    text(weight: "bold", size: 11pt)[Copyright]
    v(0.8em)

    p.copyright_notice
    v(0.5em)

    p.isbn_line
    v(0.5em)

    p.edition_line
    v(0.5em)

    p.publisher_line
    v(0.5em)

    p.credits_line
    v(1em)

    p.disclaimer
    v(1.5em)

    p.printed_in
  ]
}

// ── Layout Family: TOC ──────────────────────────────────────────────────────────
#let layout-toc(doc, p) = {
  set page(paper: p.paper, margin: (top: 3cm, bottom: 3cm, left: 3cm, right: 3cm))
  set text(font: p.heading_font, fill: p.heading_color)

  align(center)[
    text(size: 16pt, weight: "bold")[Table of Contents]
    v(0.5em)
    line(length: 6cm, stroke: 1.5pt + p.accent_color)
    v(1.5em)
  ]

  set text(font: p.body_font, fill: p.body_color, size: 10.5pt)
  set par(justify: true, leading: 1.4em, spacing: 0.4em)

  outline(title: none, indent: 1.5em, depth: 3)
  v(2cm)

  align(center)[
    text(size: 9pt, fill: luma(100))[counter(page).display("i")]
  ]
}

// ── Layout Family: CHAPTER OPENER ───────────────────────────────────────────────
#let layout-chapter-opener(doc, p, chapter_num, chapter_title, epigraph, learning_objectives) = {
  set page(paper: p.paper, margin: (inside: p.margin_inner, outside: p.margin_outer, top: p.margin_top, bottom: p.margin_bottom))

  v(3cm)
  align(center)[
    text(size: 13pt, weight: "semibold", fill: p.accent_color, tracking: 2pt)[CHAPTER]
    v(0.2em)
    text(size: 48pt, weight: "bold", fill: p.heading_color, tracking: -1pt)[chapter_num]
  ]
  v(1em)
  align(center)[
    line(length: 8cm, stroke: 2pt + p.accent_color)
  ]
  v(1.5em)

  align(center)[
    text(size: 28pt, weight: "bold", fill: p.heading_color, tracking: -1pt)[chapter_title]
  ]
  v(1.5em)

  if epigraph != "" {
    v(2em)
    align(center + horizon)[
      block(width: 70%)[
        set text(size: 12pt, style: "italic", fill: p.muted_color)
        set par(justify: false, leading: 1.5em)
        epigraph
        v(0.8em)
        align(right)[text(size: 10pt, fill: luma(100))["— " + epigraph_author]]
      ]
    ]
    v(2em)
  }

  if learning_objectives.length() > 0 {
    v(2em)
    block(fill: p.sidebar_bg, inset: 16pt, radius: 4pt, width: 100%)[
      text(size: 11pt, weight: "semibold", fill: p.accent_color)[Learning Objectives]
      v(0.6em)
      for obj in learning_objectives {
        v(0.3em)
        text(size: 10.5pt)[• obj]
      }
    ]
  }
  v(3cm)
}

// ── Layout Family: READING ──────────────────────────────────────────────────────
#let layout-reading(doc, p, content) = {
  content
}

// ── Layout Family: IMAGE LED ────────────────────────────────────────────────────
#let layout-image-led(doc, p, image_data, content) = {
  if p.image_led_layout == "top" {
    v(1em)
    figure(
      image(image_data.path, width: 100%),
      caption: [image_data.caption],
      supplement: none
    )
    v(1.5em)
    content
  } else {
    v(1em)
    figure(
      image(image_data.path, width: 85%),
      caption: [image_data.caption],
      supplement: none
    )
    v(1.5em)
    content
  }
}

// ── Layout Family: CASE STUDY ───────────────────────────────────────────────────
#let layout-case-study(doc, p, case_data) = {
  v(1.5em)
  block(fill: p.sidebar_bg, inset: 20pt, radius: 6pt, width: 100%)[
    text(size: 16pt, weight: "bold", fill: p.heading_color)[case_data.title]
    v(0.4em)
    if case_data.company != "" {
      text(size: 11pt, fill: p.muted_color)[case_data.company + " • " + case_data.industry + " • " + case_data.year]
    }
    v(1em)

    text(weight: "semibold", fill: p.accent_color)[Background]
    v(0.4em)
    case_data.background
    v(1em)

    text(weight: "semibold", fill: p.accent_color)[Challenge]
    v(0.4em)
    case_data.challenge
    v(1em)

    text(weight: "semibold", fill: p.accent_color)[Solution]
    v(0.4em)
    case_data.solution
    v(1em)

    text(weight: "semibold", fill: p.accent_color)[Results]
    v(0.4em)
    if case_data.metrics.length() > 0 {
      for metric in case_data.metrics {
        v(0.3em)
        // Use text with line breaks instead of nested block
        text(weight: "semibold", size: 12pt, fill: p.accent_color)[metric.label]
        v(0.2em)
        text(size: 10pt, fill: p.muted_color)[metric.value]
        if metric.description != "" {
          v(0.2em)
          text(size: 9pt, fill: luma(100))[metric.description]
        }
        v(0.4em)
      }
    } else {
      case_data.results
    }
    v(1em)

    block(fill: p.accent_color + luma(5), inset: 12pt, radius: 4pt, width: 100%)[
      text(weight: "semibold", fill: p.accent_color)[Key Takeaway]
      v(0.3em)
      case_data.key_takeaway
    ]
    v(1em)

    if case_data.quote != "" {
      v(0.5em)
      block(fill: white, inset: (left: 14pt, right: 12pt, top: 10pt, bottom: 10pt), stroke: (left: 3pt + p.accent_color), width: 100%)[
        set text(size: 10.5pt, style: "italic", fill: p.body_color)
        set par(justify: false)
        "“" + case_data.quote + "”"
        v(0.5em)
        align(right)[text(size: 9.5pt, fill: p.muted_color)["— " + case_data.quote_author + ", " + case_data.quote_title]]
      ]
    }
  ]
  v(1.5em)
}

// ── Layout Family: WORKED EXAMPLE ───────────────────────────────────────────────
#let layout-worked-example(doc, p, example_data) = {
  v(1em)
  block(fill: p.sidebar_bg, inset: 16pt, radius: 4pt, width: 100%)[
    text(size: 13pt, weight: "bold", fill: p.accent_color)[Worked Example]
    if example_data.title != "" {
      v(0.2em)
      text(size: 11pt, fill: p.muted_color)[example_data.title]
    }
    v(1em)

    if example_data.problem != "" {
      text(weight: "semibold", fill: p.accent_color)[Problem]
      v(0.4em)
      example_data.problem
      v(1em)
    }

    if example_data.given.length() > 0 {
      text(weight: "semibold", fill: p.accent_color)[Given]
      v(0.4em)
      for item in example_data.given {
        v(0.3em)
        text(size: 10.5pt)[• item]
      }
      v(1em)
    }

    text(weight: "semibold", fill: p.accent_color)[Solution]
    v(0.4em)

    if example_data.steps.length() > 0 {
      for step in example_data.steps {
        v(0.5em)
        // No nested block - use text and v() for spacing
        text(weight: "semibold", fill: p.accent_color)[Step step.number]
        v(0.3em)
        step.description
        if step.calculation != "" {
          v(0.4em)
          block(fill: luma(245), inset: 10pt, radius: 3pt, width: 100%)[
            set text(font: p.mono_font, size: 9.5pt)
            step.calculation
          ]
        }
        if step.explanation != "" {
          v(0.3em)
          text(size: 9.5pt, fill: p.muted_color, style: "italic")[step.explanation]
        }
      }
    } else {
      example_data.solution
    }
    v(1em)

    if example_data.answer != "" {
      block(fill: p.accent_color + luma(5), inset: 12pt, radius: 4pt, width: 100%)[
        text(weight: "semibold", fill: p.accent_color)[Answer: ]
        text(fill: p.accent_color)[example_data.answer]
      ]
    }
  ]
  v(1em)
}

// ── Layout Family: CHECKLIST ────────────────────────────────────────────────────
#let layout-checklist(doc, p, checklist_data) = {
  v(1em)
  block(fill: p.sidebar_bg, inset: 16pt, radius: 4pt, width: 100%)[
    if checklist_data.title != "" {
      text(size: 14pt, weight: "bold", fill: p.accent_color)[checklist_data.title]
      v(0.6em)
    }
    for section in checklist_data.sections {
      if section.title != "" {
        v(0.5em)
        text(size: 11pt, weight: "semibold", fill: p.heading_color)[section.title]
        v(0.4em)
      }
      for item in section.items {
        v(0.3em)
        align(left + horizon)[
          box(width: 18pt, height: 18pt, inset: 0, stroke: 1pt + p.accent_color, radius: 2pt)[]
          h(8pt)
          text(size: 10.5pt)[item.text]
          if item.detail != "" {
            h(4pt)
            text(size: 9pt, fill: p.muted_color, style: "italic")[item.detail]
          }
        ]
      }
    }
  ]
  v(1em)
}

// ── Layout Family: PROCESS DIAGRAM ──────────────────────────────────────────────
#let layout-process-diagram(doc, p, diagram_data) = {
  v(1em)
  block(fill: p.sidebar_bg, inset: 16pt, radius: 4pt, width: 100%)[
    if diagram_data.title != "" {
      text(size: 14pt, weight: "bold", fill: p.accent_color)[diagram_data.title]
      v(0.8em)
    }

    if diagram_data.steps.length() > 0 {
      for i, step in enumerate(diagram_data.steps) {
        if i > 0 {
          align(center)[
            v(0.3em)
            text(size: 20pt, fill: p.accent_color)[↓]
            v(0.3em)
          ]
        }
        // No nested block - use text with spacing
        text(weight: "bold", size: 12pt, fill: p.heading_color)[step.title]
        if step.type == "decision" {
          h(6pt)
          text(size: 9pt, fill: p.muted_color, style: "italic")[Decision Point]
        } else if step.type == "start" {
          h(6pt)
          text(size: 9pt, fill: p.muted_color, style: "italic")[Start]
        } else if step.type == "end" {
          h(6pt)
          text(size: 9pt, fill: p.muted_color, style: "italic")[End]
        }
        if step.description != "" {
          v(0.5em)
          text(size: 10pt, fill: p.body_color)[step.description]
        }
      }
    }
  ]
  v(1em)
}

// ── Layout Family: WORKED EXAMPLE FULL ──────────────────────────────────────────
#let layout-worked-example-full(doc, p, example) = {
  v(1.5em)
  block(fill: p.sidebar_bg, inset: 20pt, radius: 6pt, width: 100%)[
    text(size: 15pt, weight: "bold", fill: p.accent_color)[Worked Example]
    if example.title != "" {
      v(0.3em)
      text(size: 12pt, fill: p.muted_color, style: "italic")[example.title]
    }
    v(1em)

    if example.problem != "" {
      text(weight: "semibold", fill: p.accent_color)[Problem]
      v(0.4em)
      example.problem
      v(1em)
    }

    if example.given.length() > 0 {
      text(weight: "semibold", fill: p.accent_color)[Given]
      v(0.4em)
      for item in example.given {
        v(0.3em)
        text(size: 10.5pt)[• item]
      }
      v(1em)
    }

    text(weight: "semibold", fill: p.accent_color)[Solution]
    v(0.4em)

    for i, step in enumerate(example.steps) {
      v(0.6em)
      // No nested block
      text(weight: "bold", fill: p.accent_color)[Step step.number]
      v(0.4em)
      step.description
      if step.calculation != "" {
        v(0.5em)
        block(fill: luma(245), inset: 12pt, radius: 3pt, width: 100%)[
          set text(font: p.mono_font, size: 9.5pt)
          step.calculation
        ]
      }
      if step.explanation != "" {
        v(0.3em)
        text(size: 9.5pt, fill: p.muted_color, style: "italic")[step.explanation]
      }
    }
    v(1em)

    if example.answer != "" {
      block(fill: p.accent_color + luma(5), inset: 14pt, radius: 4pt, width: 100%)[
        text(weight: "bold", fill: p.accent_color)[Answer: ]
        text(fill: p.accent_color)[example.answer]
      ]
    }

    if example.verification != "" {
      v(0.8em)
      block(fill: luma(245), inset: 12pt, radius: 3pt, width: 100%)[
        text(weight: "semibold", fill: p.accent_color)[Verification]
        v(0.4em)
        example.verification
      ]
    }
  ]
  v(1.5em)
}

// ── Layout Family: EXERCISE ─────────────────────────────────────────────────────
#let layout-exercise(doc, p, exercise) = {
  v(1em)
  block(fill: p.sidebar_bg, inset: 16pt, radius: 4pt, width: 100%)[
    if exercise.title != "" {
      text(size: 13pt, weight: "bold", fill: p.accent_color)[exercise.title]
    } else {
      text(size: 13pt, weight: "bold", fill: p.accent_color)[Exercise]
    }
    v(0.6em)

    if exercise.instructions != "" {
      text(size: 10pt, fill: p.muted_color, style: "italic")[exercise.instructions]
      v(0.6em)
    }

    exercise.question
    v(1em)

    if exercise.hints.length() > 0 {
      // No nested block - use text with box
      block(fill: luma(255, 245, 230), inset: 12pt, radius: 3pt, width: 100%, stroke: (left: 3pt + p.accent_color))[
        text(weight: "semibold", fill: p.accent_color)[💡 Hint]
        v(0.3em)
        for hint in exercise.hints {
          v(0.2em)
          text(size: 10pt)[hint]
        }
      ]
      v(0.8em)
    }

    if exercise.response_type == "lines" {
      for i in range(exercise.response_lines) {
        v(0.8em)
        line(length: 100%, stroke: 0.5pt + luma(200))
      }
    } else if exercise.response_type == "box" {
      block(height: exercise.response_height, width: 100%, fill: white, stroke: 0.5pt + luma(200), inset: 10pt)[
      ]
    }
  ]
  v(1em)
}

// ── Layout Family: RECAP ────────────────────────────────────────────────────────
#let layout-recap(doc, p, recap_data) = {
  v(1.5em)
  align(center)[
    text(size: 18pt, weight: "bold", fill: p.accent_color)[Chapter Recap]
    v(0.3em)
    line(length: 6cm, stroke: 1.5pt + p.accent_color)
  ]
  v(2em)

  if recap_data.key_points.length() > 0 {
    text(weight: "semibold", fill: p.accent_color)[Key Points]
    v(0.6em)
    for point in recap_data.key_points {
      v(0.4em)
      align(left + horizon)[
        box(width: 6pt, height: 6pt, fill: p.accent_color)
        h(8pt)
        text(size: 10.5pt)[point]
      ]
    }
    v(1.5em)
  }

  if recap_data.takeaways.length() > 0 {
    text(weight: "semibold", fill: p.accent_color)[Key Takeaways]
    v(0.6em)
    for takeaway in recap_data.takeaways {
      v(0.5em)
      block(fill: p.accent_color + luma(5), inset: 14pt, radius: 4pt, width: 100%)[
        text(size: 10.5pt)[takeaway]
      ]
      v(0.5em)
    }
    v(1.5em)
  }

  if recap_data.review_questions.length() > 0 {
    text(weight: "semibold", fill: p.accent_color)[Review Questions]
    v(0.6em)
    for (i, q) in enumerate(recap_data.review_questions) {
      v(0.5em)
      text(size: 10.5pt)[i + 1 + ". " + q]
    }
    v(1.5em)
  }

  if recap_data.next_chapter_preview != "" {
    v(1em)
    block(fill: p.accent_color + luma(5), inset: 14pt, radius: 4pt, width: 100%)[
      text(weight: "semibold", fill: p.accent_color)[Next Chapter Preview]
      v(0.4em)
      recap_data.next_chapter_preview
    ]
  }
  v(2em)
}

// ── Export all layout functions ─────────────────────────────────────────────────
#let layout-functions = (
  cover: layout-cover,
  title-page: layout-title-page,
  copyright: layout-copyright,
  toc: layout-toc,
  chapter-opener: layout-chapter-opener,
  reading: layout-reading,
  image-led: layout-image-led,
  case-study: layout-case-study,
  worked-example: layout-worked-example,
  worked-example-full: layout-worked-example-full,
  checklist: layout-checklist,
  process-diagram: layout-process-diagram,
  exercise: layout-exercise,
  recap: layout-recap,
)