
# Maana
## Detailed Product Requirements Document (v1.0)

> Product name: Maana
> Derived from `ma'na` (معنى), meaning significance or what lies behind words
> Former working title: World Poetry Explorer
> Product philosophy: "Explore humanity through poetry."

---

# 1. Executive Summary

Maana is a knowledge-first digital library that enables readers to discover classical poetry through universal human experiences rather than language or chronology.

Unlike traditional poetry apps, every poem is enriched with structured knowledge:
- word meanings
- historical context
- symbolism
- mystical interpretation
- psychological interpretation
- literary commentary
- thematic relationships

The MVP intentionally avoids AI-generated explanations. All content is curated and stored as structured data to minimize operating costs.

---

# 2. Problem Statement

Today's poetry apps have major limitations:
- Collections without explanation
- Poor discovery
- Limited cross-cultural exploration
- Weak search
- No concept graph
- Expensive AI-first approaches

Users frequently abandon classical poetry because they understand the words but miss the deeper meanings.

---

# 3. Product Vision

Create the world's richest interconnected knowledge graph of poetry.

A reader should be able to begin with one Ghalib couplet and naturally discover:
- Rumi
- Hafez
- Al-Mutanabbi
- Shakespeare
- Bashō
- Li Bai

through shared ideas instead of shared languages.

---

# 4. Design Principles

1. Reading-first UX
2. Minimal distractions
3. Human-curated knowledge
4. Explain, don't simplify
5. Fast (<300ms common navigation)
6. Beautiful typography
7. Progressive disclosure
8. AI is optional, not foundational
9. Reader formation is part of the product, not an add-on

---

# 5. Personas

## Curious Reader
Wants beautiful explanations.

## Literature Student
Needs reliable references.

## Researcher
Needs relationships and metadata.

## Spiritual Explorer
Interested in mystical and philosophical readings.

---

# 6. Information Architecture

Home
├── Explore
│   ├── Experiences
│   ├── Symbols
│   ├── Poets
│   ├── Languages
│   └── Collections
├── Search
├── Daily Poem
├── Saved
└── Settings

---

# 7. Core Features

## Explore by Experience

Examples:
Love, Longing, Mortality, Hope, Faith, Exile, Beauty,
Silence, Time, Freedom, Ego, Suffering, Patience.

Each page contains:
- introduction
- featured poems
- related experiences
- related symbols
- featured poets

---

## Explore by Symbol

Examples:
Wine
Rose
Mirror
Ocean
Beloved
Desert
Candle
Moth
Dust
Garden

Every symbol page includes:
- literal meaning
- literary evolution
- Persian usage
- Urdu usage
- Arabic usage
- mystical significance
- poems containing symbol

---

## Poem Page

Sections:

1 Original
2 Transliteration
3 Literary Translation
4 Word-by-word meanings
5 Grammar notes (optional)
6 Historical background
7 Symbolism
8 Mystical interpretation
9 Psychological interpretation
10 Literary commentary
11 Related poems
12 References

---

## Foundations for Understanding

Before selected poems, the product may surface a small set of prerequisite ideas
that help readers approach the work more deeply.

Examples:
- longing
- impermanence
- alienation
- Sufi symbolism
- Persian literary tradition

Each foundation should be clickable and open a short, editorially grounded explainer.

---

## Human Experience Academy

The product should include short learning units that cultivate familiarity with
core human experiences, concepts, and questions.

Examples:
- What is longing?
- Why do humans grieve?
- What is irony?
- What is transcendence?

Each lesson may combine:
- story
- poetry
- philosophy
- psychology
- neuroscience
- religious or civilizational framing

The goal is not testing. The goal is readiness for reading.

---

## Readiness and Reflection

The product should distinguish:

- knowledge
- readiness

A reader may know a definition but still not be ready to encounter a poem deeply.

Instead of quizzes, the platform should favor reflective prompts and gentle readiness
states such as:

- new to this idea
- lightly explored
- well prepared

---

## Search

Support:
- full text
- autocomplete
- fuzzy search
- first line
- poet
- experience
- symbol
- era
- language

---

# 8. Database Model

Entities

Poet
Poem
Verse
Word
Theme
Symbol
Language
Era
Collection
Reference
Source
Translator
Commentary

Many-to-many relations:
Poem<->Theme
Poem<->Symbol
Poem<->Collection
Poet<->Influence
Poem<->Reference

---

# 9. Editorial Workflow

Draft
↓
Editor Review
↓
Scholar Review
↓
Published
↓
Versioned Updates

All edits stored with history.

---

# 10. Search Strategy

Phase 1
- PostgreSQL Full Text Search
- Trigram similarity

Phase 2
- OpenSearch/Meilisearch

Filters:
language
era
theme
symbol
poet

---

# 11. Tech Stack

Frontend
- Next.js
- React
- Tailwind CSS
- TypeScript

Backend
- FastAPI
- SQLAlchemy
- Pydantic

Database
- PostgreSQL

Cache
- Redis

Storage
- Cloudflare R2

Auth
- Clerk or Auth.js

Deployment
- Railway (MVP)

---

# 12. REST APIs (examples)

GET /poems
GET /poems/{id}
GET /poets
GET /themes
GET /symbols
GET /search?q=
GET /daily

---

# 13. Content Schema

Every poem should include:

- Original script
- Transliteration
- Elegant translation
- Literal translation
- Word annotations
- Context
- Commentary
- References
- Themes
- Symbols
- Related works

---

# 14. Future AI Architecture

AI is invoked ONLY for:
- Ask about this poem
- Compare poets
- Explain difficult metaphors
- Personalized learning

All AI responses cached after editorial approval.

---

# 15. Monetization

Free
- Reading
- Search
- Daily poem

Premium
- Learning paths
- Audio
- Scholar essays
- AI conversations
- Offline mode

---

# 16. Roadmap

Phase 1
- 100 poets
- 1000 poems

Phase 2
- Mobile apps
- Audio
- Collections

Phase 3
- Community annotations
- Scholar portal
- AI assistant

---

# 17. Success Metrics

- DAU
- Weekly retention
- Poems/session
- Average reading time
- Theme exploration depth
- Saved poems

---

# 18. Coding Standards

- Clean Architecture
- Repository pattern
- OpenAPI
- Unit tests
- 90% API coverage
- Responsive design
- WCAG accessibility

---

# 19. Future Knowledge Graph

Nodes:
Poets
Poems
Verses
Words
Symbols
Themes
Concepts
Historical Events
Places
Schools
Books

Edges:
influenced_by
mentions
shares_theme
shares_symbol
responds_to
same_meter
same_era

This graph becomes the application's primary intellectual asset.

---

# 20. Long-term Vision

Build the definitive digital atlas of world poetry where readers explore the shared emotional, philosophical, and mystical heritage of humanity.

The competitive advantage is not AI but a deeply curated, structured, interconnected corpus of literary knowledge and a product that cultivates the reader's capacity to receive it.
