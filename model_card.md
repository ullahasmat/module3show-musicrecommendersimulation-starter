# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

---

## 6. Limitations and Bias

### The main weakness: mood words are compared as strings, not as meanings

The biggest flaw I found is that the system checks whether two mood labels are the *same
word*, not whether they mean the same thing. When I asked it for intense rock at a low
valence — dark, heavy music — it returned *Gym Hero*, a bright major-key pop workout track,
at #2, and buried *Iron Verdict* at #5, even though *Iron Verdict* is the most intense song
in the catalog and almost exactly what I described. *Iron Verdict* lost because its mood is
labelled `angry` while I typed `intense`, so it scored zero on the mood term while *Gym Hero*
collected the full 1.5 points for matching the word. I then tried to fix this by re-tuning
the weights, and discovered that **no weight can fix it**: a zero multiplied by any number is
still zero, so I could set the mood weight to 100 and *Iron Verdict* would gain nothing. This
matters beyond one song, because the catalog's 14 mood labels really describe about four
underlying feelings — `angry`/`intense`/`tense`, `chill`/`relaxed`/`focused`,
`happy`/`euphoric`/`hopeful`, and `melancholy`/`moody`/`nostalgic` — and exact matching
splinters each cluster into unrelated pieces.

### Other biases I found

**Partial genre credit only works for genres spelled with a space.** I added a rule giving
half credit when two genres share a word, so a `pop` fan gets credit for `indie pop`. But it
splits labels on spaces, which means:

```
user "pop"      vs song "indie pop"  -> 0.5   credit given
user "hip hop"  vs song "hip-hop"    -> 0.0   no credit
user "r and b"  vs song "r&b"        -> 0.0   no credit
```

A hip-hop fan who types the genre the normal way gets nothing, purely because the dataset
happens to hyphenate it. The benefit of my own fairness rule is decided by punctuation, which
is not a musical property at all.

**15% of the catalog can never be recommended.** Across all six profiles I tested,
*Grandmother's Hands*, *Saltwater Vows*, and *Slow Burn Letter* never appeared in a single
top-5. Nothing is broken — no profile asked for folk or r&b, so their genre term never fired.
But a purely content-based system has no way to surface a song nobody explicitly asks for. It
cannot say "people who liked what you liked also liked this," so unrequested music is simply
invisible. At the scale of a real platform, this is the mechanism that buries the long tail.

**Most genres have only one song, so recommendations quietly become padding.** Nine of the
14 genres have exactly one track. A metal fan gets one real match and then four songs that
merely happened to score highest among the leftovers. The output looks identical either way —
score 5.45 and score 1.59 are printed in the same format, so **the system never signals when
it is reaching**, and a user cannot tell a confident recommendation from a desperate one.

**Listeners with middle-of-the-road taste get near-random results.** Because closeness is
symmetric, a target in the middle of the range is equidistant from both extremes and cannot
prefer either. A profile asking for energy 0.65 and valence 0.50 produced a top five spanning
0.30 points — effectively a five-way tie ordered by tie-break rules rather than by taste. The
system serves people with strong, edge-of-the-range preferences well and people with moderate
taste poorly.

**It is a filter bubble by construction.** Being purely content-based, it can only recommend
things resembling what the user already said they like. It has no mechanism for a pleasant
surprise, no notion of discovery, and no way to represent multi-modal taste — the same person
wanting intense rock at the gym and chill lofi while studying cannot be expressed. Asking for
the midpoint does not return both; it returns the mediocre middle.

### The most important fix

Give moods the same partial credit that genres already get, using synonym clusters rather
than exact strings. This is the one change with direct evidence behind it: it is the only fix
that would move *Iron Verdict* to where it belongs, and no amount of weight tuning can
substitute for it.

---

## 7. Evaluation

### Who I tested with

I made up six imaginary listeners. Three of them are ordinary music fans:

- **High-Energy Pop** — wants cheerful, upbeat pop
- **Chill Lofi** — wants quiet background music for studying
- **Deep Intense Rock** — wants loud, heavy, dark music

The other three were designed to trip the system up rather than to be served well:

- **Contradictory** — asks for classical music but also wants it very loud, which nothing in
  the collection actually is
- **Indecisive** — names no genre and no mood, and asks for everything in the middle
- **Unknown genre** — asks for k-pop, which isn't in the collection at all

The first thing I checked was simple: do these six people get different music? If everyone
gets roughly the same songs, the system isn't really listening to anyone. They didn't —
**all six got a different song in first place**, and 17 of the 20 songs turned up somewhere.

### Comparing the profiles, two at a time

**Pop vs Lofi — the clearest success.** These two lists have nothing in common. The pop fan
gets bright, fast, cheerful songs; the lofi fan gets quiet, slow, calm ones. That makes sense,
because the two listeners asked for opposite things on every single measure — different genre,
different mood, and energy of 0.80 versus 0.35. When two people describe opposite tastes and
get opposite music, the system is working. The lofi fan also got the only flawless result in
the whole experiment: *Library Rain* matched their request perfectly on every count.

**Pop vs Rock — same loudness, very different feel.** Both listeners want energetic music, so
you might expect similar results, and they do share one song. But the pop fan's list is
cheerful and the rock fan's is dark, and that difference comes almost entirely from one
number: how positive or negative a song sounds. The pop fan asked for 0.75 on that scale and
the rock fan asked for 0.40. That single number is what separates a gym anthem from a storm
track even when both are equally loud, and it's the main reason I added it to the system in
the first place.

**Lofi vs Rock — opposite ends of everything.** As expected, these two share no songs at all.
The interesting part is *how* they fail at the bottom. Both lists run out of genuinely good
matches after three or four songs, and then start including songs that fit only loosely. The
lofi fan ends up with a jazz track and the rock fan ends up with a synthwave one — neither is
wrong exactly, but neither was really asked for. Both listeners hit the same wall: the
collection is small, and once the right songs are used up, the system keeps going anyway.

**The three edge cases.** The contradictory listener asked for loud classical music and was
handed **metal**. I actually think that was the sensible choice — it went with the *sound*
they described rather than the *label* they typed — but it never mentioned that their request
was impossible. The indecisive listener got five songs whose scores were almost identical, so
the order was essentially arbitrary. And the k-pop listener got reasonable upbeat pop rather
than an error, which is the right way to fail.

### What surprised me

**The weights matter far less than I assumed.** I halved the importance of genre and doubled
the importance of energy, expecting the recommendations to change a lot. The exact same five
songs came back for every listener. Only their order shifted, and the top song never changed
once. Genre sorts songs into rough groups, and the other measures only shuffle songs within
those groups.

**A bad recommendation looked exactly like a good one.** The system scores its answers, and
those scores range from 5.50 (perfect) down to 1.59 (barely relevant). But it prints both the
same way, with the same confidence. It has the information needed to say "I'm not sure about
this one" and never does.

**Some songs are invisible.** Three songs never appeared for any of the six listeners. They
aren't bad songs — nobody happened to ask for folk or r&b, and this kind of system can only
offer you things you've already described.

### Why "Gym Hero" keeps turning up for people who want happy pop

*Gym Hero* is a workout song — the kind of thing you'd play while lifting weights. It is
filed under **pop**, it's very loud, and it sounds bright rather than gloomy. Someone asking
for happy pop is asking for three things: the pop label, a happy feeling, and reasonably
upbeat energy. *Gym Hero* clearly has two of those three.

The trouble is how the system adds up its points. A matching genre label is worth 2 points —
the largest single award — and a matching mood is worth only 1.5. *Gym Hero* is tagged
`intense`, not `happy`, so it earns nothing for mood. But it collects the full 2 points just
for being pop, plus nearly full marks for loudness and brightness, and that's enough to place
it third.

Meanwhile *Late Bus Freestyle*, which genuinely is a happy song, ranks below it — because it's
hip-hop rather than pop, and it loses the big 2-point genre award. **So a song with the right
label but the wrong feeling beat a song with the right feeling but the wrong label.**

To a person this looks silly. Nobody asks for happy music and means "anything filed under pop
will do." But the system has no idea what these words mean; it only knows that "pop" is worth
more points than "happy". When I later halved the genre award, the happy song moved above the
workout song — which tells me the ordering was never about the music. It was about which
label I decided was worth more.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
