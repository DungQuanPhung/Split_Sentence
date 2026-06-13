UOS_LINGUISTIC_PROMPT = """You split hotel review sentences into Unit Opinion Sentences (UOS).

A UOS = exactly ONE opinion about ONE target, written as a complete standalone sentence.
Return a JSON array of strings only. No explanation, no extra text.


## GOAL
Separate every distinct (target, opinion) pair into its own sentence.
Rewrite fragments into full sentences: add "The"/"A", a copula (is/was/are/were),
and keep the original adjectives. Never invent aspects, sentiments, or details.

## HARD CONSTRAINTS
- Do NOT add a sentiment or adjective that is not in the input.
- Do NOT turn factual context into an opinion.
- Do NOT split nouns that only appear inside a prepositional phrase, location phrase,
  reason phrase, example list, or amenities list.
- Split only when the target has its own explicit opinion/predicate, or when one
  explicit shared opinion clearly applies to multiple real targets.


## SPLIT  — produce one UOS per distinct (target, opinion) pair

1) Different targets, each with its own explicit opinion or predicate.
   "The room was clean but breakfast was cold."
   -> ["The room was clean.", "The breakfast was cold."]
   "The beds were incredibly comfortable and the room was spacious and nice."
   -> ["The beds were incredibly comfortable.", "The room was spacious and nice."]
   "Environment is comfortable, space is very large, the swimming pool is clean."
   -> ["Environment is comfortable.", "Space is very large.", "The swimming pool is clean."]

2) "and"/comma joins DIFFERENT targets, each with its OWN attribute.
   "Wonderful location with a fantastic swimming pool with views of the rock formations"
   -> ["Wonderful location.", "with a fantastic swimming pool with views of the rock formations."]
   "A beautiful sandy beach and crystal-clear seawater"
   -> ["A beautiful sandy beach.", "crystal-clear seawater."]
   "Beautiful room and pool"
   -> ["The room was beautiful.", "The pool was beautiful."]

3) DISTRIBUTE a shared opinion to DISTINCT targets from DIFFERENT functional domains.
   When ONE adjective/predicate applies to multiple targets joined by "and"/comma,
   repeat that opinion for each target — but ONLY when the targets are from clearly
   different functional categories (e.g. room ≠ pool, room ≠ toilet, bed ≠ sofa).
   "Very comfortable room and bed"   -> ["Very comfortable room.", "Very comfortable bed."]
   "The room and toilet are dirty"   -> ["The room is dirty.", "The toilet is dirty."]
   "Stunning rooftop pool and bar"   -> ["The rooftop pool was stunning.", "The bar was stunning."]
   "Bed and sofa both very comfortable"  -> ["The bed was very comfortable.", "The sofa was very comfortable."]
   "The room and bathroom were both spacious and clean"
   -> ["The room was spacious and clean.", "The bathroom was spacious and clean."]
   "The mattress and pillows are comfortable" 
   -> ["The mattress was comfortable.", "The pillows were comfortable."]
   "The sheets and towels were very old" 
   -> ["The sheets were very old.", "The towels were very old."]
   "The pool and beach are the hero of this property"
   -> ["The pool was the hero of this property.", "The beach was the hero of this property."]
    "Rooftop pool and view was awesome"  
    -> ["The rooftop pool was awesome.", "The view was awesome."]

4) One target with CONTRASTING or CLEARLY INDEPENDENT opinions.
   "The breakfast was delicious but expensive."
   -> ["The breakfast was delicious.", "The breakfast was expensive."]
   "The pool is beautifully maintained and gorgeous both day and night."
   -> ["The pool is beautifully maintained.", "The pool is gorgeous both day and night."]

5) Comma-separated or space-separated opinion fragments about distinct targets.
   "Lovely hotel room, good beds, nice staff"
   -> ["Lovely hotel room.", "Good beds.", "Nice staff."]
   "Nice bungalow and clean beach Good food in the restaurant Beautiful sunset"
   -> ["Nice bungalow.", "Clean beach.", "Good food in the restaurant.", "Beautiful sunset."]

6) "with" introducing a SEPARATE PHYSICAL SPACE or DIFFERENT-DOMAIN entity
   that carries its own explicit adjective or opinion.
   Split when "with" leads to a named separate space (bathroom, bathtub, balcony,
   garden, bar) OR to a clearly different-domain entity (location feature alongside
   a food opinion), and that entity has its own explicit adjective:
   "Very spacious room with a huge bathroom"
   -> ["Very spacious room.", "with a huge bathroom."]
   "The room was lovely with a beautiful view and a large balcony"
   -> ["The room was lovely.", "beautiful view.", "The balcony was large."]
   "Delicious breakfast with lovely views overlooking the beach"
   -> ["Delicious breakfast.", "with lovely views overlooking the beach."]
   "The room is comfortable, quiet, with a very large bed and a renovated bathroom"
   -> ["The room is comfortable and quiet.", "The room has a very large bed.", "The bathroom was renovated."]

   DO NOT split "with" when it introduces accessories, amenities, or a quality/
   feature that describes the main target (its view, its design, its style):
   "Nice swimming pool with sun loungers"              -> keep as one UOS
   "The pool was relaxing with colourful lights"       -> keep as one UOS
   "The rooftop pool had a great view"                 -> keep as one UOS
   "Beautiful room with a breathtaking view"           -> keep as one UOS
   "Beautiful 2 bathrooms with walk-in showers and a sauna" -> keep as one UOS


## DO NOT SPLIT

1) ONE target with multiple adjectives forming a single coherent opinion.
   "The room was spacious, comfortable and clean."
   -> ["The room was spacious, comfortable and clean."]
   "The hotel is very clean and nice and safe and spacious and fresh and very quiet."
   -> ["The hotel is very clean, nice, safe, spacious, fresh and very quiet."]
   "The beach is dirty and small."   -> ["The beach is dirty and small."]
   "The bathroom was modern and also very clean."  -> ["The bathroom was modern and also very clean."]

2) A single holistic opinion about "everything / the whole experience",
   even if it lists examples.
   "Loved the whole experience, from the gorgeous decor and attractions to the fountain to the food to the hotel room."
   -> ["Loved the whole experience, from the gorgeous decor and attractions to the fountain to the food to the hotel room."]
   "The room is absolutely perfect: spacious, bright, decorated with great taste and, most importantly, very clean."
   -> ["The room is absolutely perfect: spacious, bright, decorated with great taste and, most importantly, very clean."]

3) Logistics/context joined to a single opinion.
   "We arrived at 3pm but the room was dirty."
   -> ["We arrived at 3pm but the room was dirty."]

4) Purely factual statements (no opinion word or evaluative adjective).
   "There are two elevators."  -> ["There are two elevators."]

5) One usability complaint with causal/layout details.
   Keep the reason with the complaint — nouns inside cause/location phrases are
   context, not separate targets.
   "We couldn't shower because the shower head was above the toilet and the sink, there was physically no space."
   -> ["We couldn't shower because the shower head was above the toilet and the sink, and there was physically no space."]

6) View/location/context phrases and "as was" comparisons.
   Nouns inside "view of/over X and Y", "as was X", "particularly X" are context.
   Do not split them unless they carry their own independent opinion.
   "Fantastic view over the river and promenade"
   -> ["The view over the river and promenade was fantastic."]
   "The rooftop pool was outstanding as was the view of the Dragon Bridge and river."
   -> ["The rooftop pool was outstanding as was the view of the Dragon Bridge and river."]
   "There was a rooftop pool with a great view, particularly watching the sun set over the water."
   -> ["There was a rooftop pool with a great view, particularly watching the sun set over the water."]
   "Beautiful room with a breathtaking view"
   -> ["Beautiful room with a breathtaking view."]

7) Amenities, inventory, and "with [accessories]" of the main target.
   Items after "with", "including", "such as", ":" that are ACCESSORIES or FEATURES
   of the main entity stay with it. Do not assign the main adjective to each item.
   "The bathroom was clean with the basics: shampoo, shower gel, hand soap."
   -> ["The bathroom was clean with the basics: shampoo, shower gel, hand soap."]
   "A large, clean swimming pool with sun loungers."
   -> ["A large, clean swimming pool with sun loungers."]
   "Outside there is a nice swimming pool with sun loungers and a breakfast area."
   -> ["Outside there is a nice swimming pool with sun loungers and a breakfast area."]

   EXCEPTION — if one item in the list has its OWN explicit adjective while the
   rest do not, extract only that opinionated item:
   "Large bed, sofa, kitchenette, bathroom and most importantly a washing machine."
   -> ["Large bed.", "The room had a sofa, kitchenette, bathroom and washing machine."]

8) Booking/logistics context plus one opinion.
   Never create a positive opinion from a factual mention ("available" ≠ "good").
   "We booked the sea view room and the view was breathtaking."
   -> ["We booked the sea view room and the view was breathtaking."]  (keep as context)
   "Although we had booked for 2 adults and 2 children, there was only 1 (though a huge) bed."
   -> ["Although we had booked for 2 adults and 2 children, there was only 1 bed, though it was huge."]


## DECIDE — quick reference

| What "and" / comma / "with" connects      | Action                                     |
|-------------------------------------------|--------------------------------------------|
| Different targets, each with own opinion  | SPLIT into separate UOS (rule 1)           |
| Two targets from different domains, shared adj | SPLIT and distribute adj (rule 3)     |
| Two targets forming a natural paired set  | KEEP as one UOS (rule 3 exception)         |
| Multiple adjectives on ONE noun           | KEEP as one UOS (DO NOT SPLIT rule 1)      |
| "with" + separate physical space with adj | SPLIT (rule 6)                             |
| "with" + accessory / feature / style      | KEEP with main target (rule 6, DO NOT SPLIT 7) |
| Location/context nouns in "view of X, Y"  | KEEP (DO NOT SPLIT rule 6)                 |
| Causal/layout nouns after "because/so"    | KEEP with complaint (DO NOT SPLIT rule 5)  |

**Key question**: Does each item have its own standalone review-worthy identity
AND an explicit adjective/opinion? If yes → SPLIT. If it describes HOW the main
target looks/feels/comes-with → KEEP.


## FINAL RULES
- Preserve original wording and adjectives; never invent new ones.
- Keep causal/contrast words ("because", "but", "although", "only", "no", "not")
  when they change the meaning.
- Keep modifiers attached to their target ("pool with views of the rock formations").
- Do not classify aspect or sentiment.
- Do not over-split a coherent multi-adjective opinion on one target.

Input:
{sentence}

Output:"""
