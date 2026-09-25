// Times each typst component so the flow planner can predict page fill.
// Rendered by scripts/measure_components.py, which prints the per-kind chrome
// values that typst_renderer.BLOCK_CHROME_LINES must carry. Keep the two in
// step: the planner's accuracy is only as good as these measurements.
//
//     typst compile --root / scripts/probe_components.typ /tmp/probe.pdf
//     python3 scripts/measure_components.py /tmp/probe.pdf
//
// Each case is fenced by TOPMARKER and ENDMARKER so the measured height is the
// component's whole box, card insets included, not just its inked text.

#let D = "/Users/lakshitsinghvi/Documents/Repos/EBook-Generator/editorial_studio/editorial_studio/assets/templates"
#import D + "/helpers.typ": *
#set page(width: 210mm, height: 297mm, margin: (top: 25mm, bottom: 25mm, left: 28mm, right: 22mm))

// A four-line body of the average word length in this manuscript, so every
// component is timed holding the same amount of text.
#let BODY = "Recreational land valuation is a fundamental component of market, recreational, agricultural, and mitigation land valuation frameworks. It encompasses several key aspects that every beginner and intermediate American land investor should understand and act on with care over a full year of diligence."

#let th = theme((
  palette: (:),
  text_size: "10.5pt",
  leading_extra_ratio: 0.75,
  par_space_ratio: 0.7,
))
#set text(size: th.text-size, font: th.body-font, fill: th.ink)
#let prose = text(BODY)

#let top = text(size: 4pt, fill: red)[TOPMARKER]
#let bot = text(size: 4pt, fill: green)[ENDMARKER]

// Two exercise cases so the height of a single ruled answer line can be
// differenced out; typst_renderer.EXERCISE_LINE_LINES carries it.
#let exercise(rules) = top + v(4pt) + exercise-card((
  kicker: "Worksheet",
  title: "Land classification systems assessment",
  response_type: "lines",
  response_lines: rules,
), prose, th) + bot

#let cases = (
  top + v(4pt) + text(BODY) + bot,
  top + v(4pt) + case-study-card((title: "Recreational land valuation",), prose, th) + bot,
  top + v(4pt) + worked-example-card((title: "Scenario setup"), prose, th) + bot,
  exercise(0),
  exercise(5),
  top + v(4pt) + callout-box(prose, "learning_objective", th) + bot,
  top + v(4pt) + text(font: th.heading-font, size: th.h2-size, weight: "bold")[Understanding the U.S. land market and types of land] + v(6pt) + text(BODY) + bot,
)

#for c in cases [ #c #pagebreak() ]
