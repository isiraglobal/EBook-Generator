"""Substantive replacement content for the field manual.

The generated manuscript carried a single template for every case study, every
worked example and every chapter opener: the same five sentences with the
chapter's own topic words dropped in. Fifty-six per cent of the book's text was
that template repeated, which is why the pages read as filler however well they
were set.

This module holds real content, keyed by the manuscript block id it replaces, so
applying it preserves the schema, the block ids, the chapter and section
numbering, and the order of the book. Nothing here changes the shape of a block.

Every case study is an *illustrative hypothetical*. It is built to teach one
decision, and it is labelled as hypothetical on the page. No scenario in this
module is presented as a documented transaction, and none carries an invented
price, yield, acreage, market result or legal conclusion. Where a step depends on
a fact the reader must look up -- a flood zone, a soil class, a water right, a
zoning designation -- the instruction is to go and look it up in the named
public record rather than to assume a number.

Named institutions here (county assessor and recorder, FEMA's Flood Insurance
Rate Maps, USDA NRCS Web Soil Survey, ALTA/NSPS survey standards, the Internal
Revenue Code) are real and are named so a reader knows where to verify. The
guidance about how to use them is instructional, not a citation of a specific
result.
"""

HYPOTHETICAL = "Illustrative hypothetical scenario, constructed for teaching. Not a documented transaction."

# ---------------------------------------------------------------------------
#  Case studies. Keys are manuscript block ids.
# ---------------------------------------------------------------------------

CASE_STUDIES = {
    # ---- Chapter 1: understanding the market and the land types ------------
    "cb_25f669a960_0008": {
        "title": "Sizing a market before spending a marketing dollar",
        "situation": "A buyer has picked a county on a map and written a first-year "
                     "acquisition target. The county is large, mostly rural, and has no "
                     "submarket breakdown the buyer has verified.",
        "analysis": "County-level area and price figures describe a market the buyer "
                    "cannot actually transact in. The question is not how many acres "
                    "changed hands but how many acres of the *kind the buyer wants* "
                    "changed hands, at a size the buyer can fund, inside a drive time "
                    "from a service point. That is a smaller number, and the gap between "
                    "the two is the marketing budget the buyer had not budgeted for.",
        "decision": "Rebuild the target from the county assessor's transfer records, "
                    "filtered by acreage band and use, and count parcels rather than "
                    "acres. Re-derive the acquisition target from that count before any "
                    "letter is mailed.",
        "lesson": "Size the submarket you can buy in, not the county you can name on a map.",
        "basis": HYPOTHETICAL,
    },
    "cb_f923c77dcd_0010": {
        "title": "Two parcels, two land classifications, two different businesses",
        "situation": "Two adjoining parcels are offered together at one price. The "
                     "listing describes both as 'rural land'. One is timberland under a "
                     "forest management plan; the other is cleared ground zoned for "
                     "residential use.",
        "analysis": "'Rural land' is not a classification, it is an absence of "
                    "information. The two parcels differ in what they may legally be "
                    "done with, what they can be financed as, and what a buyer is "
                    "actually acquiring: a standing asset with a management history, or "
                    "a building site with development potential. Buying them as one lot "
                    "averages two incompatible theses into something neither supports.",
        "decision": "Split the offering. Price the timbered parcel on its own basis and "
                    "the cleared parcel on its own basis, and decide which thesis the "
                    "buyer is actually underwriting before responding to the combined price.",
        "lesson": "Classify before you price. A use classification is a constraint on "
                  "every later decision, not a detail to note afterwards.",
        "basis": HYPOTHETICAL,
    },
    "cb_9586b55e63_0012": {
        "title": "Writing the thesis before the offer",
        "situation": "A buyer is excited about a parcel that 'could do a lot of things' "
                     "and is about to make an offer that expires in 48 hours.",
        "analysis": "A parcel that could do a lot of things has no thesis, and a buyer "
                    "without a thesis prices on the seller's expectation instead of "
                    "their own. The missing document is one page: the intended use, the "
                    "evidence that the use is permitted, the holding period, and the exit "
                    "that pays for the holding period. Without it, every number in the "
                    "deal is the seller's number.",
        "decision": "Write the one-page thesis before the offer is signed, and make the "
                    "offer contingent on the use being confirmed in the public zoning "
                    "record rather than on the listing agent's assurance.",
        "lesson": "A thesis is a sentence about what you will do, for how long, and how "
                  "you get paid back. Write it before you bid.",
        "basis": HYPOTHETICAL,
    },
    "cb_532ea66ca5_0014": {
        "title": "Two land uses, two demand cycles, one county",
        "situation": "A county contains both cropland and a growing exurban edge. An "
                     "investor's letter assumes the whole county moves with the exurban "
                     "cycle, because that cycle has been the visible one lately.",
        "analysis": "A county is not a market. Cropland demand is driven by the cost of "
                    "producing a crop and by the availability of water; exurban demand is "
                    "driven by where people want to live and by the interest rate they can "
                    "service. Those two can move in opposite directions in the same county "
                    "in the same year. Reading the visible cycle as the whole county's "
                    "cycle is how an investor ends up underwriting cropland at a "
                    "residential-land multiple.",
        "decision": "Identify which demand driver the parcel is actually exposed to, name "
                    "the observable indicator for that driver, and stop using county-wide "
                    "price direction as a proxy for the parcel.",
        "lesson": "Match the cycle you underwrite to the use of the land, not to the "
                  "headlines about the county.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 2: valuation frameworks ----------------------------------
    "cb_b8ed87528e_0023": {
        "title": "Three comps, three different things",
        "situation": "A buyer has three nearby sales and intends to average them into a "
                     "value for the subject parcel.",
        "analysis": "Averaging is only valid when the three sales are measuring the same "
                    "thing. If one sale is a smaller parcel with better road frontage, one "
                    "is larger with none, and one has different water access, the average "
                    "is a number that describes none of them. A comparable is not "
                    "comparable because it is near; it is comparable because the "
                    "differences can be named and priced.",
        "decision": "Rank the three by the variables that actually move price in this "
                    "submarket, discard any sale where a critical variable cannot be "
                    "verified, and adjust the survivors one variable at a time rather than "
                    "blending them.",
        "lesson": "A comp earns its place by being explicable. If you cannot say which "
                  "variable makes it different, it is not a comp yet.",
        "basis": HYPOTHETICAL,
    },
    "cb_4d24ae2949_0026": {
        "title": "Renting a field, and what the rent is actually paying for",
        "situation": "An agricultural parcel is being valued on an income approach. A "
                     "tenant is paying rent under a multi-year lease.",
        "analysis": "A lease rent is a number negotiated under specific conditions: a "
                    "specific tenant's skill, a specific crop rotation, specific weather, "
                    "and a specific start date. It is evidence about the land only once "
                    "those conditions are separated out. Capitalising the lease rent "
                    "directly treats a single season's weather and one operator's "
                    "efficiency as if they belonged to the parcel permanently.",
        "decision": "Establish whether the rent reflects the land or the operator, by "
                    "comparing it against the going rate for comparable ground in the same "
                    "county, and capitalise the going rate rather than the contract price.",
        "lesson": "Separate what the tenant paid for from what the land earns. The lease "
                  "is evidence, and evidence has to be tested.",
        "basis": HYPOTHETICAL,
    },
    "cb_985fd95437_0028": {
        "title": "A recreational parcel priced on a view",
        "situation": "A recreational parcel is offered at a premium per acre, on the "
                     "strength of its setting and a nearby access point.",
        "analysis": "Recreational land is valued by a buyer who will pay for access, "
                    "setting and a permitted use. None of those is guaranteed by "
                    "proximity to an access point: the access may be seasonal, the use may "
                    "be unpermitted, and the setting may be the reason the parcel is not "
                    "buildable. A premium justified only by a view is a premium a later "
                    "buyer may not pay, which means it may be a premium the current buyer "
                    "cannot refinance against.",
        "decision": "Verify the legal access and the permitted use before crediting the "
                    "setting premium, and test whether a secondary market exists for the "
                    "parcel at that price with the same access and use.",
        "lesson": "On recreational land, the premium is paid for access and permission. "
                  "Verify both, or do not pay it.",
        "basis": HYPOTHETICAL,
    },
    "cb_b04f834ab3_0030": {
        "title": "A credit worth more than the land",
        "situation": "A mitigation parcel sits in a jurisdiction with an established "
                     "credit programme. The buyer's adviser suggests the credits alone "
                     "justify the price.",
        "analysis": "A mitigation credit is a contractual claim on a future "
                    "environmental outcome, issued under programme rules that the seller "
                    "does not control and the buyer's adviser has not read. Credits can be "
                    "worth more than the land, and they can also be unissuable: the "
                    "baseline, the additionality finding and the monitoring obligation are "
                    "each conditions, and a programme can change its methodology between "
                    "the contract and the issuance.",
        "decision": "Obtain the programme's current methodology and confirm the parcel's "
                    "baseline qualifies, and price the credits at a discount for "
                    "methodology risk unless an issued credit can be assigned.",
        "lesson": "Price a credit for the conditions attached to it. A methodology you "
                  "have not read is not value you can bank.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 3: finding opportunities ----------------------------------
    "cb_c1e7a4b6ff_0039": {
        "title": "Reading a listing that is priced to move",
        "situation": "A listing has a discount to the county's recent transfers and a "
                     "short stated deadline.",
        "analysis": "Both signals are common and neither is reliable on its own. A "
                    "discount may reflect a condition the listing does not disclose; a "
                    "deadline may be a negotiating position or a real distress signal. "
                    "What distinguishes them is whether the seller has done anything "
                    "verifiable about the property's condition, and whether the price "
                    "movement is visible in the public record rather than only in the "
                    "listing.",
        "decision": "Check the property's own record for condition clues and the "
                    "assessment history for a change in ownership circumstance, and price "
                    "the offer against the condition evidence rather than against the "
                    "deadline.",
        "lesson": "A discount is a question, not an opportunity. Answer it with the "
                  "public record before you answer it with an offer.",
        "basis": HYPOTHETICAL,
    },
    "cb_8e4ca5ca57_0041": {
        "title": "A mailing list that produced nothing, and why",
        "situation": "A direct mail campaign to a list of county residents returned "
                     "almost no responses, and a second list from a different source "
                     "returned several.",
        "analysis": "The difference between the two lists is almost never the mail. It is "
                    "the selection criterion. A list built from an arbitrary geographic "
                    "cut reaches owners who have no reason to transact; a list built from "
                    "an observable circumstance reaches owners who already have one. The "
                    "second list worked because it was assembled from a criterion that "
                    "predicted action, not because the envelopes were better.",
        "decision": "Rebuild the list from an observable circumstance visible in public "
                    "records rather than from geography, and test one narrow segment before "
                    "committing a print budget.",
        "lesson": "Direct mail works when the list encodes a reason to act. A list "
                  "without a selection criterion is just postage.",
        "basis": HYPOTHETICAL,
    },
    "cb_fea6891248_0043": {
        "title": "The broker who knows the county",
        "situation": "An investor is building a relationship with a local broker in a "
                     "county they do not know.",
        "analysis": "A local broker's value is not access to listings; it is knowledge "
                    "that is not in any database. Which soils actually drain, where the "
                    "floodplain disputes are, which families have been selling for a "
                    "decade, which road is scheduled for paving. That knowledge is real "
                    "and it is also unverified, and it is offered freely by people whose "
                    "incentive is a transaction.",
        "decision": "Use the broker's knowledge to generate questions, then verify every "
                    "material claim in the public record before it reaches a model. Pay "
                    "the commission when a deal closes, not for the education.",
        "lesson": "Take the broker's knowledge as a lead list. Take the price from the "
                  "record.",
        "basis": HYPOTHETICAL,
    },
    "cb_174a980562_0045": {
        "title": "A tax delinquency is a signal, not a strategy",
        "situation": "A parcel appears in the county's delinquent tax list and the "
                     "investor is considering approaching the owner directly.",
        "analysis": "Delinquency has causes with very different meanings: a cash-flow "
                    "problem that resolves, a dispute that blocks payment, an owner in "
                    "poor health, or a parcel the owner no longer wants. The list does not "
                    "distinguish them, and the four lead to four different conversations. "
                    "Approaching on the assumption of distress, when the real problem is a "
                    "billing dispute, wastes the relationship permanently.",
        "decision": "Establish which cause applies before contacting anyone, using the "
                    "public record and a short, respectful conversation that does not "
                    "assume the seller's circumstances.",
        "lesson": "Read the delinquency for what it is before you use it. The same fact "
                  "supports four different approaches and only one of them is polite.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 4: seller research, outreach and structure ----------------
    "cb_bf96d88e52_0054": {
        "title": "Two sellers, two reasons to sell",
        "situation": "Two owners in the same county both have land on the market. One has "
                     "a life change; the other is a passive holder who bought years ago.",
        "analysis": "Motivation determines the negotiation, and the two are opposites. A "
                    "seller with a life change is solving a problem other than price and "
                    "will accept a lower number to close quickly. A passive holder is "
                    "solving a management problem, will accept a longer timeline, and will "
                    "not discount for speed they did not ask for. Treating both as 'willing "
                    "to negotiate' produces an offer that is simultaneously too aggressive "
                    "for one and insufficient for the other.",
        "decision": "Identify the reason for each sale before opening, and price the "
                    "timeline as a variable in each deal rather than applying one posture "
                    "to the market.",
        "lesson": "Find out why it is being sold before you decide how hard to press. The "
                  "reason for the sale is the negotiation.",
        "basis": HYPOTHETICAL,
    },
    "cb_6a1972715e_0059": {
        "title": "The first letter is a question",
        "situation": "An outreach letter is about to go to a large list of landowners in "
                     "a county the investor has never worked in.",
        "analysis": "The letter is the buyer's only evidence of competence, and the "
                    "recipient has no reason to believe the letter describes anything real. "
                    "A letter that leads with an offer invites a lowball reply and a "
                    "conversation about price. A letter that leads with a specific, "
                    "checkable observation about the parcel gets a reply about the parcel, "
                    "which is the only conversation worth having.",
        "decision": "Rewrite the first contact to lead with one verifiable observation "
                    "from the public record and one specific question, and send it to a "
                    "small list before it goes to a large one.",
        "lesson": "Earn the second letter by asking a real question in the first one.",
        "basis": HYPOTHETICAL,
    },
    "cb_12f0125c6e_0062": {
        "title": "Negotiating against a number the seller invented",
        "situation": "A seller is firm at a price well above every comparable in the "
                     "submarket, and explains that the land has been in the family for "
                     "generations.",
        "analysis": "A seller's price is usually an aspiration rather than a valuation, and "
                    "sentiment is the most common reason given for a number that no comp "
                    "supports. Treating the number as the opening position of a normal "
                    "negotiation is a mistake: if the price has no basis in the market, "
                    "conceding toward it transfers value for nothing. The question is not "
                    "how to close the gap but whether the gap exists at all.",
        "decision": "Anchor on the comparable evidence, state the position as a number "
                    "with a basis, and be prepared to end the conversation rather than to "
                    "close it at a price the evidence does not support.",
        "lesson": "A price without a basis is not a negotiation. It is a request, and you "
                  "are free to decline it.",
        "basis": HYPOTHETICAL,
    },
    "cb_ad897a8cd2_0071": {
        "title": "A structure that solves the seller's problem instead of the buyer's",
        "situation": "A seller wants full price and will not move. The buyer's cash is "
                     "constrained and the closing timeline is flexible.",
        "analysis": "A negotiation stalled on price is often stalled on the wrong variable. "
                    "Where the seller is not price-sensitive but is sensitive to certainty "
                    "and to avoiding a second transaction, a structure that transfers "
                    "those things can close a deal that a price reduction would not. This "
                    "is a genuine lever, and it is also a way to pay a full price and call "
                    "it a discount, which is why it must be evaluated on the total cost of "
                    "capital rather than on the headline rate.",
        "decision": "Compare the structure's true cost against the price concession it "
                    "replaces, over the full expected holding period, and pick the one with "
                    "the lower modelled return rather than the one that feels clever.",
        "lesson": "When price will not move, find the variable that will. Then check what "
                  "the trade actually cost you.",
        "basis": HYPOTHETICAL,
    },
    "cb_2c8b59292b_0057": {
        "title": "A sequence that assumes agreement at every step",
        "situation": "An outreach sequence is built so that each message assumes the "
                     "previous one landed.",
        "analysis": "Sequences fail when they are written as a single argument split into "
                    "envelopes. If the recipient has not answered, the second message now "
                    "argues past them, the third apologises for the second, and by the "
                    "fourth the sender is negotiating with someone who never raised an "
                    "objection. Each step is reasonable alone and collectively they are "
                    "incoherent, because the sequence assumes a state that only the "
                    "recipient can create.",
        "decision": "Rewrite the sequence so each message is a complete, standalone "
                    "question that would make sense as the first and only contact, and "
                    "branch on whether the recipient has engaged at all.",
        "lesson": "Write each contact as if it is the only one. Anything that depends on "
                  "the last one is a negotiation you are conducting alone.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 5: title, access and land use -----------------------------
    "cb_d45c729be4_0073": {
        "title": "The easement that is not where the survey says it is",
        "situation": "A title report shows an access easement benefiting the parcel. The "
                     "recorded plat appears to place it well away from the property.",
        "analysis": "An easement is a specific burden on a specific parcel, described by a "
                    "document that may be older than the current survey, drafted by a "
                    "different surveyor, and located by a monument that has since moved. "
                    "A discrepancy between the plat and the report is not a clerical "
                    "matter: it may mean the easement does not actually reach the land, or "
                    "that it reaches it by a route the current access does not use. Either "
                    "reading changes the value, and neither can be resolved from a desk.",
        "decision": "Order a boundary and easement survey locating the easement on the "
                    "ground before the purchase agreement makes access a closing "
                    "condition, and treat an unresolved location as a defect.",
        "lesson": "Access you have only read about is access you do not have. Pay for the "
                  "survey that puts it on the ground.",
        "basis": HYPOTHETICAL,
    },
    "cb_5e9912a633_0075": {
        "title": "Zoned for a use the county will not permit",
        "situation": "A parcel's zoning designation appears to permit the buyer's "
                     "intended use. The county planning office says the designation has "
                     "not been applied to that parcel in practice.",
        "analysis": "A zoning map is a general statement about a district, and the "
                    "district is not always what the parcel is in: easements, "
                    "nonconforming status, overlay districts, and parcel-specific "
                    "conditions all intervene. The designation on the map is the starting "
                    "point for the question, not its answer, and a buyer's entitlement runs "
                    "against the current owner of the land, not against the map.",
        "decision": "Request a written zoning verification or determination from the "
                    "planning jurisdiction for this specific parcel and use, and make the "
                    "purchase contingent on it rather than on the map's legend.",
        "lesson": "Zoning tells you where to ask the question. The written determination "
                  "is the answer.",
        "basis": HYPOTHETICAL,
    },
    "cb_a421b0d356_0078": {
        "title": "A lien search that found the obvious liens",
        "situation": "A title search comes back clear of the liens anyone expected, and "
                     "the buyer is ready to close.",
        "analysis": "A clean search for recorded liens is a statement about the recording "
                    "system, not about the parcel. Liens that were never recorded, taxes "
                    "that have not yet been assessed against a new owner, and claims held "
                    "by a party with an interest that has not been recorded all survive a "
                    "clear report. The report answers the question it was asked, and the "
                    "question asked was narrow.",
        "decision": "Widen the search beyond recorded liens — assess for taxes that will "
                    "transfer, identify unrecorded parties with an interest, and confirm "
                    "the ownership chain back far enough to catch a defect.",
        "lesson": "'Clear of record' is a real and useful finding. It is not the same "
                  "finding as 'free of claims', and the gap is where the disputes live.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 6: water, soil, flood and environmental risk --------------
    "cb_f5101f5d46_0087": {
        "title": "A well that exists and a water right that does not",
        "situation": "A rural parcel has a functioning well. The buyer's adviser has not "
                     "established what the well draws on or who controls it.",
        "analysis": "Physical availability and legal availability are different things. In "
                    "most Western states groundwater is regulated by a statutory scheme "
                    "administered at the state or groundwater district level, and a well "
                    "may be permissible, may require a permit, or may be in violation of a "
                    "priority right held by a neighbour. A working well is evidence of "
                    "water in the ground; it says nothing about the right to draw it, and "
                    "the neighbour's claim is the part that ends a closing.",
        "decision": "Establish which water scheme governs the parcel and what the well's "
                    "status is under it, from the administering agency, before treating "
                    "the water as an asset in the model.",
        "lesson": "Ask what the law says about the well, not whether the pump works. The "
                  "first question is cheaper than the second kind of answer.",
        "basis": HYPOTHETICAL,
    },
    "cb_2d8b745644_0089": {
        "title": "A soil report that answers a different question",
        "situation": "A perc test has been run on the parcel and the result is a single "
                     "number, presented as proof the site will take a septic system.",
        "analysis": "A perc rate is one observation on one day at one location. What a "
                    "septic design needs is a soil interpretation over the drainfield area, "
                    "including depth to a limiting layer, seasonal high water table and "
                    "slope, and the USDA Natural Resources Conservation Service Web Soil "
                    "Survey is a starting point that must be checked against field "
                    "conditions. A favourable number in the wrong place is worse than no "
                    "number, because it stops the investigation.",
        "decision": "Commission a soil interpretation for the actual drainfield location "
                    "and require the county health department's approval of the system as a "
                    "closing condition where a septic system is part of the use.",
        "lesson": "One measurement is not a soil report. Ask what was measured, where, and "
                  "what decision it is supposed to support.",
        "basis": HYPOTHETICAL,
    },
    "cb_499e551cca_0091": {
        "title": "Outside the flood zone, inside the flood problem",
        "situation": "A parcel is not in a mapped special flood hazard area, and the "
                     "buyer is treating that as the end of flood diligence.",
        "analysis": "The FEMA Flood Insurance Rate Map is the national reference and it "
                    "is also a snapshot with stated limitations: it is not a parcel-level "
                    "flood study, it does not capture every drainage problem, and the "
                    "map's effective date matters. Being outside a mapped zone is a real "
                    "and favourable finding, and it is not the same as being outside a "
                    "floodplain. Unmapped drainage, local floodplain ordinances and "
                    "proximity to a watercourse each carry their own risk.",
        "decision": "Check the effective FEMA map for the parcel, then check the county's "
                    "own floodplain ordinance, which is frequently stricter than the "
                    "federal map and controls locally.",
        "lesson": "The national map is where you start. The local ordinance is what "
                  "controls. Read both before you price the risk.",
        "basis": HYPOTHETICAL,
    },
    "cb_228639c65a_0094": {
        "title": "A Phase I that finds nothing and answers nothing",
        "situation": "A standard environmental site assessment has been commissioned and "
                     "returned with no recognised environmental conditions identified.",
        "analysis": "The assessment covers its scope, and its scope is a defined set of "
                    "conditions for a defined use. A property used for agriculture or "
                    "industry carries use-related conditions — tanks, solvents, fill "
                    "history — that a general scope may not reach, and 'no conditions "
                    "identified' is a statement about what was looked for, not a warranty "
                    "that nothing is there. The distinction matters most where the intended "
                    "use is more demanding than the current one.",
        "decision": "Read the assessment's scope against the property's actual and intended "
                    "use, and where the use is changing, commission the assessment that "
                    "matches the new use rather than relying on the old one.",
        "lesson": "'Nothing found' is a statement about scope. Check the scope against what "
                  "you intend to do with the land.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 7: valuation, costs and underwriting ----------------------
    "cb_409be7dd9a_0103": {
        "title": "Adjusting a comp by a percentage the adviser chose",
        "situation": "A comparable is adjusted by a single percentage for a difference in "
                     "road frontage, and that percentage comes from the adviser's own "
                     "judgement.",
        "analysis": "A percentage adjustment is a claim about how much that variable is "
                    "worth, and it has to be supported by something other than the "
                    "adviser's confidence. The supporting evidence is the local spread "
                    "between transactions that differ mainly in that one variable. An "
                    "unsupported adjustment is indistinguishable from an invented number, "
                    "and because it sits inside a model where everything looks "
                    "arithmetic, it is very hard to see.",
        "decision": "Derive each adjustment from the local evidence for that specific "
                    "variable, show the derivation beside the number, and carry the "
                    "adjustments into a range rather than a point.",
        "lesson": "An adjustment is an argument, not a coefficient. Show the evidence "
                  "behind it or the model is only arithmetic.",
        "basis": HYPOTHETICAL,
    },
    "cb_3a2d797ded_0105": {
        "title": "The acquisition cost that did not include the closing",
        "situation": "An acquisition model compares two offers and concludes the lower "
                     "price is the better deal.",
        "analysis": "The price is one line in the cost of acquisition. Closing costs, "
                    "survey and examination work, title insurance, recording, and the "
                    "cost of fixing whatever diligence finds are all part of what it takes "
                    "to own the parcel, and on a lower-priced parcel they are frequently a "
                    "larger share of the total. A model that compares prices instead of "
                    "total cost will reliably prefer the deal that is cheapest to agree "
                    "and most expensive to close.",
        "decision": "Add every cost required to take possession, including the ones that "
                    "arrive after closing, and compare the two offers on the total.",
        "lesson": "Compare what it costs to own, not what it costs to win. The second "
                  "number is smaller and it is a trap.",
        "basis": HYPOTHETICAL,
    },
    "cb_2506ac96d7_0107": {
        "title": "A carrying cost model with no vacancy",
        "situation": "A projected return is built on a property that has never been "
                     "leased, and the model assumes full occupancy from day one.",
        "analysis": "Vacancy is not a discount to a good year; it is a structural cost of "
                    "being a landlord, and it arrives as a time series — lease-up on "
                    "turnover, downtime between tenants, and the months required to find a "
                    "tenant at all. A model that starts at full occupancy has quietly "
                    "assumed the hardest part of the investment is free, and the resulting "
                    "return is not optimistic so much as arithmetically fictional.",
        "decision": "Build the vacancy assumption into the first year explicitly, set it "
                    "from what comparable properties in the area actually experience, and "
                    "carry it as a recurring cost rather than a one-off.",
        "lesson": "A property that has never been leased has not yet been tested. The "
                  "first lease is a project, and it should be in the model.",
        "basis": HYPOTHETICAL,
    },
    "cb_e87c9a489f_0109": {
        "title": "A return that only works at the base case",
        "situation": "The underwriting shows an acceptable return, and the sponsor asks "
                     "what happens if the exit is delayed by a year.",
        "analysis": "A single-point return is an assertion that every assumption is "
                    "correct at once, which is the least likely outcome available. The "
                    "assumptions are not independent: a delayed exit usually arrives with "
                    "higher carrying costs and a softer market at the same time, so varying "
                    "them one at a time systematically understates the downside. The "
                    "useful question is not what happens if one thing goes wrong but what "
                    "has to be true for the deal to work at all.",
        "decision": "Test the return against the variables together, identify which single "
                    "assumption the deal depends on most, and set the monitoring threshold "
                    "for that variable before closing.",
        "lesson": "Stress the variables that move together. A downside that assumes only "
                  "one thing goes wrong is not a downside.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 8: transaction structures ---------------------------------
    "cb_b1c3569ce9_0119": {
        "title": "A note at a rate the buyer cannot refinance away",
        "situation": "A seller is financing part of the purchase. The note is at a rate "
                     "the buyer cannot match, and the buyer's model assumes refinancing "
                     "at a future date.",
        "analysis": "A seller-financed note is a real cost of capital for as long as it "
                    "runs, and the rate is often below what the buyer could obtain — which "
                    "is exactly why sellers offer them. The buyer's model must carry that "
                    "rate to maturity, not to the refinancing date, and must treat the "
                    "refinancing as an assumption rather than a plan. If the note is "
                    "balloon, the model is a bet on the future capital markets dressed as "
                    "an investment.",
        "decision": "Underwrite the deal at the note rate through the full term, and "
                    "model the refinancing separately as a discrete event with its own "
                    "failure case.",
        "lesson": "Price the financing you actually have. The cheaper rate you might get "
                  "later is a separate bet, and it belongs in a separate line.",
        "basis": HYPOTHETICAL,
    },
    "cb_4e314f0c77_0121": {
        "title": "An option that does not say what happens if it lapses",
        "situation": "An option agreement gives a buyer time to complete diligence, and "
                     "the agreement is silent on what the buyer recovers if the property "
                     "fails the review.",
        "analysis": "An option's whole purpose is to convert diligence time into "
                    "something, and the most common drafting failure is silence on the "
                    "failure case. Without a stated recovery, the buyer's remedy for a "
                    "property that turns out to be unusable is whatever the default rules "
                    "give, which is rarely the earnest money. Silence is not neutral here: "
                    "it defaults to the position that happened to be drafted, not the one "
                    "the buyer assumed.",
        "decision": "State the recovery for a failed diligence explicitly, and make the "
                    "earnest money returnable on a defined list of findings rather than at "
                    "the buyer's discretion.",
        "lesson": "The clause you did not write is the one that decides what happens when "
                  "the property fails. Write it.",
        "basis": HYPOTHETICAL,
    },
    "cb_cfd8d6141c_0123": {
        "title": "A partnership where nobody controls the exit",
        "situation": "Two parties have formed a joint venture to acquire and hold a parcel, "
                     "and neither has a defined right to force a sale.",
        "analysis": "Holding land is a decision nobody wants to make alone. When two "
                    "owners have no mechanism to resolve a disagreement, the parcel becomes "
                    "permanent by default, and both parties are locked into a position they "
                    "would not have chosen — one paying carrying costs on an asset they "
                    "want out of, the other unable to sell. The deadlock is usually not "
                    "about price; it is about the absence of a process.",
        "decision": "Agree the exit mechanics at formation: how a sale is triggered, how "
                    "price disagreements are resolved, and what a party may do if the other "
                    "will not sell.",
        "lesson": "Write the exit before the entry. Two owners with no exit is not a "
                  "partnership, it is a shared problem.",
        "basis": HYPOTHETICAL,
    },
    "cb_f4a73a83e1_0125": {
        "title": "An exchange assumed to be a tax strategy",
        "situation": "A buyer is considering a like-kind exchange under IRC Section 1031 and "
                     "is treating the identification of replacement property as the last "
                     "step.",
        "analysis": "The statutory requirements are narrow, and two of them are "
                    "hard-failing: the property must be held for the required period, and "
                    "the replacement property must be identified before the deadline. A "
                    "transaction structured so that the identification is awkward is not a "
                    "strategy, it is an outcome decided by a date, and the deferral is lost "
                    "if the deadline passes without a compliant identification. The "
                    "treatment also depends on facts that have to be established rather "
                    "than assumed.",
        "decision": "Confirm the specific requirements that apply to the transaction with a "
                    "tax adviser before the structure is chosen, and treat the deadlines as "
                    "conditions of the deal rather than as administrative steps.",
        "lesson": "Deferral is a set of conditions with dates attached. Find out what they "
                  "are before the structure, not after.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 9: stabilisation and value-add -----------------------------
    "cb_c7d9f6fb83_0134": {
        "title": "The improvement that was not needed",
        "situation": "A recently acquired parcel needs 'stabilisation' work, and a "
                     "contractor has recommended a substantial programme.",
        "analysis": "Stabilisation is whatever prevents value from leaking, and a "
                    "contractor's programme is built to be worth spending, not to be "
                    "necessary. The distinction is testable: a stabilisation item either "
                    "removes a risk to the asset, or it is an improvement, and the two "
                    "carry different return expectations. Bundling them means the "
                    "necessary work is no longer separable from the discretionary work, so "
                    "neither can be evaluated.",
        "decision": "Split the programme into items that prevent loss and items that add "
                    "value, fund the first from the reserve, and require the second to be "
                    "underwritten as a project with its own return.",
        "lesson": "Ask of every line on a stabilisation list: does this stop a loss, or does "
                  "it add value? They are funded differently.",
        "basis": HYPOTHETICAL,
    },
    "cb_2d8c31a8aa_0136": {
        "title": "A medium-term project with no permitting path",
        "situation": "An improvement plan schedules a use change for year two, and the "
                     "parcel's current zoning does not permit it.",
        "analysis": "Improvement plans are usually written in the certainty of the use they "
                    "assume, and the permitting path is assumed rather than examined. A use "
                    "that requires a rezoning, a conditional use permit, or an approval "
                    "from an agency has a duration and a failure mode, and a plan that "
                    "schedules the benefit without the timeline is a plan whose benefit "
                    "date is unknown. Capital spent before the approval is capital spent "
                    "against an option the buyer does not control.",
        "decision": "Establish the approval path, its realistic timeline and its cost "
                    "before committing to the improvement, and stage the capital so that "
                    "none of it is at risk before the approval is in hand.",
        "lesson": "Value that depends on a permit is a permit, not a value. Price the "
                  "approval before you spend against it.",
        "basis": HYPOTHETICAL,
    },
    "cb_0f76391b59_0138": {
        "title": "Ongoing management that nobody owns",
        "situation": "A portfolio of land has no assigned management responsibility, and "
                     "obligations are being met reactively as they come due.",
        "analysis": "Land obligations are mostly small, dated and unforgiving — a report, a "
                    "tax payment, an inspection, a renewal — and a set of small dated "
                    "obligations with no owner fails at the first one, because nothing is "
                    "late until it is. Reactive management is not cheaper; it converts a "
                    "planned cost into an emergency cost and loses the institutional "
                    "knowledge of why each obligation exists.",
        "decision": "Build a dated obligations register with a named owner per item, and "
                    "review it on a schedule that is set by the obligation rather than by "
                    "the quarter.",
        "lesson": "Assign an owner and a date to every obligation. The failures are "
                  "administrative, and they are entirely preventable.",
        "basis": HYPOTHETICAL,
    },
    "cb_85f3d1a5a9_0140": {
        "title": "Cheaper to do once, and worth doing once",
        "situation": "A recurring cost has been optimised by a change that saves a modest "
                     "amount each year and introduces a new obligation.",
        "analysis": "Cost optimisation on land is unusually easy to get wrong in the "
                    "optimistic direction, because the new obligation is usually free to "
                    "adopt and quietly expensive to carry. A saving that adds an annual "
                    "task, a renewal or a compliance item is not a saving; it is a trade "
                    "whose second leg is not yet being counted. The comparison has to be "
                    "lifetime to lifetime, including the cost of the thing that has to be "
                    "remembered.",
        "decision": "Compare the change on total lifetime cost including the new "
                    "obligation, and reject any saving that depends on something being "
                    "remembered reliably for longer than it will be.",
        "lesson": "Count the cost of the thing you now have to remember. That is where the "
                  "saving goes.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 10: exit and portfolio ------------------------------------
    "cb_941fe33a53_0149": {
        "title": "Knowing the exit before the entry",
        "situation": "A buyer is underwriting an acquisition and has not specified how "
                     "they would exit it.",
        "analysis": "The exit is the only part of the return that is completely outside "
                    "the buyer's control, and it is routinely the largest single term. An "
                    "investment whose exit is unstated is not underwritten; it is hoped. "
                    "The absence also propagates: without a named exit, the entry cannot be "
                    "judged against the holding period that the exit implies, and the "
                    "improvement plan cannot be sequenced against anything.",
        "decision": "Write the exit — who the buyer is, at what price, in what market "
                    "condition — before the entry, and let it discipline the entry price "
                    "and the holding period.",
        "lesson": "An unstated exit is the largest untested assumption in the deal. Name it "
                  "first.",
        "basis": HYPOTHETICAL,
    },
    "cb_d71fcd70d7_0151": {
        "title": "A buyer who appeared in a better market",
        "situation": "A sale process produced an offer in a strong market, and the seller "
                     "is deciding whether to wait for a better one.",
        "analysis": "The decision to wait is a bet that the market will improve, and it is "
                    "priced as though the current offer is guaranteed to be available "
                    "later. It is not: the buyer who made it may not make another, and the "
                    "market that produced it may have been the reason it was available. "
                    "Holding out also carries its own cost — carrying costs continue, and "
                    "they continue whether or not the market improves.",
        "decision": "Compare the current offer against the modelled return from waiting, "
                    "including the carrying cost of waiting, and be explicit that the "
                    "current offer is not a floor under the next one.",
        "lesson": "Holding out is a new deal with a new buyer. Underwrite it as one, "
                  "carrying costs included.",
        "basis": HYPOTHETICAL,
    },
    "cb_c99a7a7dc0_0153": {
        "title": "Marketing a property for the use it is permitted, not the one it is",
        "situation": "A property is being marketed with photographs and a brochure "
                     "emphasising an aspect of it that the current zoning does not permit "
                     "to be developed.",
        "analysis": "Marketing copy is a representation, and a representation that leads "
                    "with a use the buyer cannot obtain creates a buyer who is disappointed "
                    "at the closing rather than at the showing — which is where the "
                    "dispute, the withdrawn deposit and the professional-claim risk live. "
                    "It also narrows the pool, because the buyers who understand the "
                    "restriction are not the ones the copy attracts.",
        "decision": "Market the permitted use, and put the zoning constraint in the "
                    "material where a buyer will see it, so the right buyers self-select in.",
        "lesson": "Market what the buyer can build. The disappointment you avoid is worth "
                  "more than the interest the copy attracts.",
        "basis": HYPOTHETICAL,
    },
    "cb_a00df13def_0156": {
        "title": "The last week of a transaction",
        "situation": "A purchase is weeks from closing with diligence complete, and the "
                     "team is treating the remaining time as administrative.",
        "analysis": "The final period of a land transaction is where the items that were "
                    "deferred reappear: the survey comes back with an exception, the "
                    "insurance company asks a question, a required notice was not given, or "
                    "a party needed a signature that could not be obtained. Each is "
                    "individually small, routine, and capable of delaying a closing that "
                    "the model has already banked. They are also the ones that cannot be "
                    "solved in the final week.",
        "decision": "Run the closing from a dated checklist with each item owned, and "
                    "identify every signature and approval needed in the first week rather "
                    "than the last.",
        "lesson": "A closing is a project with dependencies. The items that stop it are "
                  "all known in advance, and all of them are known too late if you wait.",
        "basis": HYPOTHETICAL,
    },

    # ---- Chapter 11: checklist and deal review -----------------------------
    "cb_d8f599394d_0165": {
        "title": "A checklist that had never been used on a real deal",
        "situation": "A due diligence checklist exists, is comprehensive, and has not been "
                     "run against a transaction with anything difficult in it.",
        "analysis": "A checklist is only as good as the last time it was tested against "
                    "something awkward. Checklists written from a model transaction contain "
                    "the questions that transaction raised and omit the ones it did not, "
                    "which is why a comprehensive-looking checklist can still be silent on "
                    "the item that ends the deal. The items that matter are the ones found "
                    "in practice, not the ones anticipated in design.",
        "decision": "Add every item that surfaced on a real transaction, however "
                    "inconvenient it seemed at the time, and mark which items have actually "
                    "been cleared on a past deal.",
        "lesson": "A checklist grows from surprises. Mark the items you have never actually "
                  "cleared, and treat those as the risky ones.",
        "basis": HYPOTHETICAL,
    },
    "cb_c1dbaf7466_0167": {
        "title": "Scoring a deal on the criteria that were available",
        "situation": "A deal-scoring model is being applied, and two criteria are marked "
                     "'unknown' because the diligence has not been done.",
        "analysis": "Scoring systems are built to make a judgement comparable across "
                    "deals, and that only works if every score means the same thing. A "
                    "missing score is not a neutral score: it is usually scored as zero, "
                    "which makes an uninvestigated deal look worse than a bad one, and "
                    "sometimes scored as neutral, which makes it look better than a "
                    "resolved one. Both distort the comparison the score exists to provide.",
        "decision": "Distinguish 'not yet investigated' from 'investigated and weak', and "
                    "refuse to rank a deal on a score that still contains either.",
        "lesson": "Never score what you did not look at. A missing score is a missing "
                  "score, not a zero and not a neutral.",
        "basis": HYPOTHETICAL,
    },
    "cb_ea4c57af7c_0169": {
        "title": "The memo that argued for the deal",
        "situation": "An investment memo has been written to recommend a transaction, and "
                     "the reasons not to do it are summarised in one sentence at the end.",
        "analysis": "A recommendation document written by the party recommending it has a "
                    "structural bias that no amount of good intent removes: the case is "
                    "assembled, the risks are summarised, and the reader is left to notice "
                    "the imbalance. The risk section is the part a committee will actually "
                    "rely on, and it is the part written last and shortest, which means the "
                    "two things most worth interrupting the meeting for are the two things "
                    "least likely to be read carefully.",
        "decision": "Write the strongest case against the deal first, before the case for "
                    "it, and give each risk an owner, a probability and a cost rather than "
                    "a paragraph.",
        "lesson": "Write the case against first. A memo that cannot state the best argument "
                  "against itself has not been reviewed.",
        "basis": HYPOTHETICAL,
    },
    "cb_fda87bfa2a_0171": {
        "title": "Monitoring that produces reports and not decisions",
        "situation": "A portfolio produces quarterly reports. Nothing in them has ever "
                     "triggered an action.",
        "analysis": "Monitoring exists to trigger a decision, and a report that never does "
                    "is measuring activity rather than performance. The usual cause is that "
                    "the report tracks what is easy to count — occupancy, rent collected, "
                    "arrears — and not the variables the investment thesis said would decide "
                    "the outcome. Reports of that kind stay reassuring precisely because "
                    "they are not connected to the reason for owning the land.",
        "decision": "Derive the monitoring indicators from the thesis, set a threshold for "
                    "each, and name in advance the action each threshold triggers.",
        "lesson": "A report that cannot change a decision is an expense. Set the thresholds "
                  "and the actions before you need them.",
        "basis": HYPOTHETICAL,
    },
}


# ---------------------------------------------------------------------------
#  Worked examples. Keys are manuscript block ids. Each carries a numbered
#  procedure, which is what the worked-example page family needs in order to
#  draw a calculation rather than a paragraph.
# ---------------------------------------------------------------------------

WORKED_EXAMPLES = {
    "cb_3482b2e416_0024": {
        "title": "Comparable sales analysis on a mixed-use edge parcel",
        "steps": [
            "List the transfers in the target submarket from the county recorder, and keep "
            "only those that closed within the period over which the land type has been "
            "stable.",
            "From that set, keep the sales that match the subject on the two variables that "
            "move price most in this submarket: the intended use and the size band.",
            "For each surviving sale, record the variables that differ from the subject "
            "and name each one, so that every difference is visible before any number is "
            "applied.",
            "Derive an adjustment for each named variable from the local evidence for that "
            "variable, rather than from a percentage the adviser is comfortable with.",
            "Apply the adjustments one at a time and carry the result as a range, so the "
            "conclusion states what the evidence supports rather than a single figure it "
            "does not.",
        ],
        "result": "A value stated as a range, with the local evidence for each adjustment "
                  "shown beside it and the two sales that were discarded recorded with the "
                  "reason. The range is the deliverable; the midpoint is a convenience.",
        "basis": HYPOTHETICAL,
    },
    "cb_0385aa8f5c_0055": {
        "title": "Reading seller motivation from the public record",
        "steps": [
            "Assemble what the record shows about the seller's circumstances: length of "
            "ownership, the pattern of prior transactions, and whether the property has "
            "changed hands before.",
            "Separate the observable from the inferred. The ownership history is "
            "observable; the reason for selling is not, and the difference decides how the "
            "conversation should open.",
            "Form the two or three most likely explanations, ranked, and write the evidence "
            "that would distinguish between them.",
            "Choose an opening question that is answerable under any of the explanations, "
            "so the first exchange cannot be a dead end.",
        ],
        "result": "A ranked hypothesis about the reason for sale, the test that would "
                  "confirm each, and an opening that does not presume the most likely one.",
        "basis": HYPOTHETICAL,
    },
    "cb_beb0a68a6d_0060": {
        "title": "Negotiating when the seller's price has no basis",
        "steps": [
            "Establish the value position from the comparable evidence, and write down the "
            "basis for it before the next conversation.",
            "Identify which part of the seller's ask is price and which part is a condition "
            "— timing, certainty, form of payment — because they respond to different levers.",
            "Open at a number the evidence supports and state the basis for it, rather than "
            "discounting from the ask, which concedes the ask's authority.",
            "Decide before the conversation what you will do at your limit, and what you "
            "will walk away with if the seller will not move.",
        ],
        "result": "An opening anchored on evidence, a known limit, and a prepared exit — "
                  "so the negotiation has an outcome the buyer chose rather than one the "
                  "seller chose.",
        "basis": HYPOTHETICAL,
    },
    "cb_121c5c5102_0076": {
        "title": "Testing a zoning designation against an intended use",
        "steps": [
            "Identify the specific use the buyer intends, in the precise terms the "
            "jurisdiction uses, rather than a general description of it.",
            "Locate the parcel's actual designation, including any overlay district, and "
            "note the map's own stated limitations.",
            "Request a written determination from the planning jurisdiction for this parcel "
            "and this use, and treat the map as a prompt for the request rather than an "
            "answer to it.",
            "Identify the approval path, its dependencies and its realistic duration, and "
            "price that duration into the holding period.",
        ],
        "result": "A written determination for the specific parcel and use, an approval "
                  "path with a duration, and a holding period that accounts for it.",
        "basis": HYPOTHETICAL,
    },
    "cb_08f7757fed_0092": {
        "title": "Establishing flood risk to a standard the lender will accept",
        "steps": [
            "Retrieve the current FEMA Flood Insurance Rate Map for the parcel and record "
            "the map's effective date and the parcel's actual designation.",
            "Read the local floodplain ordinance, which is frequently stricter than the "
            "federal map and controls locally, and check whether the parcel is addressed by "
            "a provision the map does not show.",
            "Identify what the intended use and the intended lender will require beyond the "
            "map — an elevation certificate, a specific zone, or a study — and establish who "
            "pays for it and how long it takes.",
            "Treat any of these as unknown until documented, and make the unknowns a "
            "condition rather than a risk to note later.",
        ],
        "result": "A documented flood position at the standard the lender will actually "
                  "apply, with the remaining unknowns listed as conditions rather than as "
                  "accepted risk.",
        "basis": HYPOTHETICAL,
    },
    "cb_ff8aa7df74_0110": {
        "title": "Sensitivity analysis on a holding that depends on an exit",
        "steps": [
            "List the assumptions the return actually depends on, and for each one record "
            "whether it is observable, estimated or assumed.",
            "Group the assumptions by whether they move together — a delayed exit usually "
            "arrives with higher carrying costs — so that the downside is tested as a "
            "combination rather than one variable at a time.",
            "Vary each group across a plausible range, and record the return at each "
            "combination.",
            "Identify the single assumption the deal is most sensitive to, and set the "
            "monitoring threshold for that assumption before the transaction closes.",
        ],
        "result": "A return expressed across combinations rather than a single number, and "
                  "one named assumption with a threshold attached to it.",
        "basis": HYPOTHETICAL,
    },
    "cb_a101a24440_0154": {
        "title": "Marketing copy that discloses the constraint",
        "steps": [
            "List the uses the property is currently permitted to have, in the "
            "jurisdiction's own terms, and identify which of them the marketing will lead "
            "with.",
            "Check that the lead use is permitted, and that any permission relied on is "
            "documented rather than assumed from a map.",
            "Place the zoning constraint in the material itself, where a buyer reads it "
            "before viewing, so the buyers who proceed are the buyers for whom the property "
            "is suitable.",
            "Review the imagery and description against the permitted use, and remove any "
            "element that suggests a development not currently allowed.",
        ],
        "result": "Marketing that leads with a permitted use, discloses the constraint in "
                  "the material, and attracts buyers the property actually suits.",
        "basis": HYPOTHETICAL,
    },
    "cb_f24ef0e632_0180": {
        "title": "Setting up a hypothetical transaction and fixing its assumptions",
        "steps": [
            "State the property in terms that can be verified later: use, size band, "
            "access, and the jurisdictions whose records would be consulted. A worked "
            "example is only useful if the reader can substitute real numbers for the "
            "structure.",
            "List every assumption the analysis depends on, and mark each as observable, "
            "estimated or assumed — the classification determines how much weight it can "
            "carry.",
            "Name the record that would confirm or refute each assumption, so the worked "
            "example doubles as a diligence plan.",
            "State explicitly that the figures are illustrative and that no market, yield or "
            "price in this example describes any actual transaction or parcel.",
        ],
        "result": "A fixed set of assumptions, each tied to a source that could confirm it, "
                  "and an explicit statement that the example is hypothetical.",
        "basis": HYPOTHETICAL,
    },
    "cb_298a8916bd_0182": {
        "title": "Underwriting the hypothetical transaction step by step",
        "steps": [
            "Build the acquisition cost from the total required to take possession, not "
            "from the agreed price alone, so the closing and post-closing items are inside "
            "the comparison.",
            "Model the income or the intended use on the assumption the verification step "
            "identified, and record which assumption the result depends on most.",
            "Carry the holding period costs — the ones that continue whether or not the "
            "market cooperates — across the full period rather than to an assumed exit.",
            "State the return across a range for the assumption identified as most "
            "sensitive, rather than at a single point.",
        ],
        "result": "A total-cost acquisition figure, a return stated as a range, and a "
                  "record of the assumption the result turns on.",
        "basis": HYPOTHETICAL,
    },
    "cb_7f4dabbc2a_0184": {
        "title": "Testing the hypothetical transaction against what could go wrong",
        "steps": [
            "Choose the two or three assumptions the result is most sensitive to, and vary "
            "them together rather than singly.",
            "For each combination, record the return and whether the transaction would "
            "still clear the buyer's own threshold.",
            "Identify the combination that fails first, since that is the one that will "
            "decide the outcome in practice.",
            "Decide, before the transaction, what evidence would be watched for that "
            "combination, and who is responsible for watching it.",
        ],
        "result": "A named failure combination, the evidence that would signal it, and a "
                  "responsibility assigned in advance — so the downside has an owner before "
                  "it happens.",
        "basis": HYPOTHETICAL,
    },
    "cb_ab16c744fd_0185": {
        "title": "Where the hypothetical transaction would actually fail",
        "steps": [
            "Take the worked transaction and change one assumption at a time to a value the "
            "supporting record could plausibly support, starting with the assumption the "
            "result is most sensitive to.",
            "For each change, recompute the return and note whether it still clears the "
            "threshold set for the transaction.",
            "Where a single change is not enough to break the deal, combine the two changes "
            "most likely to occur together — a slower exit and a higher carrying cost are a "
            "pair, not two independent events.",
            "Record the first combination that fails, and write the sentence describing the "
            "circumstances under which a buyer would walk away.",
        ],
        "result": "A named failure combination and a written walk-away condition, so the "
                  "point at which the transaction stops making sense is defined before it "
                  "is reached.",
        "basis": HYPOTHETICAL,
    },
    "cb_d1e9fdb1bf_0187": {
        "title": "What the worked example is for",
        "steps": [
            "Note which steps in the worked example were assumptions and which were "
            "verifications, because the two carry different weight in a real transaction.",
            "Identify the single step where a different real-world answer would change the "
            "conclusion, and treat that step as the one to perform first on any real deal.",
            "Record the diligence items the example implies but does not perform, so they "
            "become a checklist rather than an omission.",
            "State plainly which parts of the example are structural and which would change "
            "with real data, so a reader knows what transfers to a real transaction.",
        ],
        "result": "A short list of the verifications that carry the result, and a "
                  "prioritised first step for applying the example to a real parcel.",
        "basis": HYPOTHETICAL,
    },
}


# ---------------------------------------------------------------------------
#  Chapter openers and summaries, keyed by block id. Each is written to its own
#  chapter's scope; none of them recycles a sentence.
# ---------------------------------------------------------------------------

CHAPTER_INTROS = {
    "cb_f1ccbe24b1_0005":
        "Land is not one asset class. Before anything can be priced, bought, improved or "
        "sold, the thing being transacted has to be described in terms that a county "
        "records, a lender underwrites and a court would enforce. This chapter establishes "
        "the vocabulary for doing that: what a market actually is when it is smaller than a "
        "county, how land classifications constrain every decision that follows, how to "
        "state an investment thesis in a sentence, and which demand drivers move which "
        "kinds of land. The examples are constructed to be checked against a public record "
        "rather than believed, because a description that cannot be verified is not a "
        "description, it is a preference.",
    "cb_86ceec87d4_0020":
        "Each category of land is valued by a different question. Agricultural land asks "
        "what it earns; recreational land asks who will pay for access and setting; land "
        "with mitigation value asks what a programme will recognise and a buyer will fund. "
        "This chapter works through the three frameworks and shows where each fails when "
        "applied to the others. Comparable sales, income capitalisation and credit analysis "
        "are presented as arguments that have to be supported, not formulas that produce an "
        "answer. The worked example in this chapter is hypothetical throughout, and its "
        "figures are illustrative of a method rather than of any market.",
    "cb_eb7429c969_0036":
        "Most land never reaches a listing. The practical question in sourcing is not where "
        "to look but which observable circumstance indicates that an owner is more likely "
        "than the general population to transact, and this chapter treats public records as "
        "the raw material for that judgement. On-market channels, direct outreach, local "
        "relationships and the delinquency record are each assessed on what they can "
        "actually establish. The recurring theme is that every channel produces leads, and "
        "that a lead becomes a deal only after the seller's reason for selling is "
        "understood and verified against the record.",
    "cb_069145ac06_0051":
        "Approaching an owner is the start of a negotiation whose shape was already set by "
        "the circumstances of the sale. This chapter treats seller research, first contact, "
        "sequencing, negotiation and structure as one continuous process, on the view that "
        "a structure chosen in the last week is usually a structure forced in the last week. "
        "The worked examples apply the chapter's frameworks to a single hypothetical "
        "situation and show what each step changes. Throughout, the instruction is to derive "
        "position from evidence rather than from the other party's ask, because an ask that "
        "has been tested is a negotiation and one that has not is simply a request.",
    "cb_c1c12b0c03_0068":
        "A contract conveys whatever the record permits it to convey, and the record is "
        "made of documents that disagree with one another. This chapter covers title, "
        "ownership, easements, legal access, zoning and encumbrances as a single sequence of "
        "verification rather than a set of separate searches, because a clear title opinion "
        "on a parcel that cannot legally be reached is not a comfort. Each finding here is "
        "tied to the document or the public office that establishes it. The worked example "
        "applies the sequence to a hypothetical parcel, and the worked answers are worked "
        "because the underlying records were actually consulted, not because the steps are "
        "hard.",
    "cb_ae2be291c6_0084":
        "Some risks are visible on a map, some in a soil survey, and some only after a "
        "question is asked of the right agency. This chapter works through water, soil, flood "
        "and environmental risk in that order, because that is roughly the order in which "
        "they are discovered and the order in which a late one is most expensive. The point "
        "of the chapter is not the individual risks but the habit of establishing which "
        "jurisdiction governs each one, since most of these questions have different answers "
        "in different counties. The worked example is hypothetical and the guidance is to "
        "consult the named source rather than to assume a result.",
    "cb_cb34ec6a74_0100":
        "A valuation becomes an investment decision when costs and time are added to it, and "
        "almost every land model is wrong in the same direction: it omits the things that "
        "happen after the price is agreed. This chapter builds from comparable selection "
        "through total acquisition cost, carrying costs and return, with the emphasis on "
        "making each assumption visible and identifying which one the result depends on. The "
        "worked example in this chapter is constructed so that its numbers can be replaced "
        "with a reader's own, and its structure is the structure of the real thing: a range "
        "rather than a point, and a named sensitivity rather than an average.",
    "cb_4254c1b25f_0116":
        "Structure is how a transaction is made to fit the parties, and the fit is often "
        "where the value is created or quietly transferred. This chapter covers owner "
        "financing, options, joint ventures and like-kind exchange considerations as "
        "negotiated instruments, each assessed on what it costs the party that accepts it. "
        "The recurring failure is a structure that solves a present problem by creating a "
        "future obligation nobody priced. Where a statutory provision is involved, the "
        "chapter's instruction is to establish the applicable requirements with an adviser "
        "before the structure is chosen, because the requirements are conditions with dates "
        "attached and they do not bend to fit a closing calendar.",
    "cb_6ec26589dd_0131":
        "Land does not deteriorate on a schedule; it leaks, one obligation at a time, and "
        "the leaks are administrative. This chapter separates the work that prevents loss "
        "from the work that adds value, because the two are funded differently and are "
        "judged by different returns. Immediate stabilisation, medium-term improvement, "
        "ongoing management and cost control are treated as a sequence in which each step "
        "depends on the one before it. The recurring instruction is to ask of every proposed "
        "expenditure whether it stops a loss or adds value, and to stage capital so that "
        "none of it is committed against an approval the buyer does not yet hold.",
    "cb_0e04e87096_0146":
        "The exit is the largest term in a land investment and the one the buyer controls "
        "least, which is why it belongs at the front of the analysis rather than at the end "
        "of the plan. This chapter works backward from exit to entry: who the buyer is, at "
        "what price, in what market, and what that implies for the holding period and the "
        "improvements that should precede it. Marketing, timing and execution are treated as "
        "consequences of a stated exit thesis. The worked example applies the chapter to a "
        "hypothetical sale, and its disclosures are the point: marketing copy that leads "
        "with a use the property is not permitted to have creates a dispute at closing "
        "rather than at the showing.",
    "cb_f4d83569c7_0162":
        "A disciplined process is mostly a written one, and the documents in this chapter "
        "are that process made explicit. The master checklist, the scoring model, the "
        "committee memo and the monitoring schedule are presented as instruments with known "
        "failure modes, not as templates to be filled in. The chapter's argument is that "
        "each of them fails in a characteristic way — the checklist omits what the last deal "
        "surprised by, the score fills unknowns with zeros, the memo is written by the party "
        "recommending, and the monitoring never triggers an action — and that each failure is "
        "avoidable only if it is named in advance.",
    "cb_0e8e694874_0177":
        "This chapter carries a complete hypothetical transaction from setup to conclusion "
        "so that the frameworks in the preceding eleven chapters can be seen working "
        "together on one property. The scenario is constructed, the figures are illustrative, "
        "and nothing in it describes an actual parcel, price, yield or outcome. What the "
        "example is for is the structure: assumptions fixed and labelled by type, each tied "
        "to the record that would confirm it, the return stated as a range, and a named "
        "sensitivity with a monitoring threshold attached. A reader applying this to a real "
        "parcel should expect the structure to transfer and every number to change.",
}


CHAPTER_SUMMARIES = {
    "cb_70c4cf9d02_0015":
        "A market is smaller than a county and specific to a use, and a thesis is a sentence "
        "naming the use, the period and the exit. The practical residue is a target built "
        "from the count of comparable parcels rather than from the area of the county, and a "
        "written thesis that predates the offer.",
    "cb_2c913fe368_0031":
        "The three valuation frameworks answer different questions and are not "
        "interchangeable. Comparable sales earn their place by being explicable, income "
        "capitalisation must separate the operator's performance from the land's, and a "
        "recreational or mitigation premium is paid for access, permission and programme "
        "conditions that have to be verified before they are priced.",
    "cb_0b15800579_0046":
        "Every sourcing channel produces leads and none produces certainty. The channels "
        "differ in what they can establish: the public record can show circumstance, a local "
        "relationship can generate questions, and a listing can state a deadline. The "
        "durable advantage is a list built from a criterion that predicts action, and a habit "
        "of verifying the seller's reason for selling before it is used in negotiation.",
    "cb_4cd4e55317_0063":
        "Motivation sets the negotiation, price is only one of the variables, and a structure "
        "that transfers certainty can close a deal that a price reduction would not. The "
        "discipline is to establish the reason for the sale first, open from a position the "
        "evidence supports, and evaluate any structure on its total cost over the full "
        "holding period rather than on its apparent concession.",
    "cb_88bf7aae8c_0079":
        "Title, access, zoning and encumbrances are one sequence of verification, not four "
        "searches, and each finding must be tied to the document or public office that "
        "establishes it. A zoning map is a prompt for a written determination rather than an "
        "answer, an easement is not located until a survey puts it on the ground, and a "
        "report clear of recorded liens is not a report clear of claims.",
    "cb_784fb0e1bb_0095":
        "Water, soil, flood and environmental risk each have a governing jurisdiction, and "
        "the questions differ by county. The habit worth building is establishing which "
        "authority answers which question before relying on any answer, and treating what a "
        "consultation did not cover as unknown rather than as clear.",
    "cb_5247e3daa9_0111":
        "A return is a range with a named sensitivity, not a point estimate. Total cost of "
        "acquisition, the vacancy and other structural costs of ownership, and the holding "
        "period costs that continue regardless of the market all belong inside the model, "
        "and the assumption the result depends on most should be identified and monitored "
        "before the transaction rather than discovered during it.",
    "cb_86cdd5c1e5_0126":
        "Structure fits the parties and transfers something real. A seller note is a cost of "
        "capital to maturity rather than to the refinancing date, an option must state what "
        "happens when diligence fails, a joint venture must have exit mechanics agreed at "
        "formation, and any statutory treatment must be established with an adviser before "
        "the structure is chosen.",
    "cb_34d4ee2ecc_0141":
        "Every proposed expenditure is either preventing a loss or adding value, and the two "
        "are funded and judged differently. Improvement work that depends on a permission "
        "not yet held is capital at risk against an option, recurring obligations fail "
        "administratively rather than dramatically, and a saving that adds an obligation is "
        "not a saving once the obligation is counted.",
    "cb_d57ac2162f_0157":
        "The exit should be named before the entry, because it sets the holding period, "
        "constrains what improvements are worth doing first, and determines whether the "
        "acquisition was ever a good idea. Marketing must lead with a permitted use, holding "
        "out is a new deal with a new buyer, and the closing is a project with dependencies "
        "that are all knowable in advance if they are identified early.",
    "cb_1a94772341_0172":
        "The instruments in this chapter each fail in a characteristic and avoidable way: a "
        "checklist omits what the last deal surprised by, a score converts an uninvestigated "
        "question into a value, a memo written by the recommending party understates the case "
        "against, and monitoring that never triggers an action is measuring the wrong things. "
        "Naming each failure in advance is most of the work.",
    "cb_b0082e44ac_0188":
        "A complete transaction is a sequence in which each step supplies an input the next "
        "one depends on, and the example is worth reading for that structure rather than for "
        "its figures. Assumptions are fixed and labelled by type and tied to a record that "
        "would confirm them; the acquisition is costed as a total rather than a price; the "
        "return is carried as a range; and the sensitivity that decides the outcome is "
        "identified and given a monitoring threshold in advance. The numbers are "
        "illustrative and describe no actual parcel, price or market. What transfers to a "
        "real transaction is the order of the work and the discipline of the labelled "
        "assumption — a reader should expect every figure to change and the structure to "
        "survive.",
}

