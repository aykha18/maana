# LiteraryKnowledgeGraph

The Literary Knowledge Graph is the graph layer that connects literary entities
and their relationships across the platform.

It is intentionally named more narrowly than `KnowledgeGraph` because the architecture
will likely grow into multiple graph layers over time, including:

- Literary Knowledge Graph
- Human Experience Graph
- Question Graph

## Purpose

Connect poems, poets, verses, words, themes, symbols, concepts, human experiences,
human questions, languages, civilizations, translations, and commentary through explicit,
meaningful relationships.

## Core Node Types

- human question
- human experience
- theme
- symbol
- concept
- poet
- poem
- verse
- word
- translation
- commentary
- language
- civilization

## Example Relationship Chain

Human question
-> human experience
-> theme
-> symbol
-> poem
-> verse
-> word

## Sample Relationships

- human question gives rise to human experience
- human experience contains theme
- poem responds to human question
- poem evokes human experience
- poem expresses theme
- poem uses symbol
- symbol relates to concept
- poet wrote poem
- poem contains verse
- translation renders poem
- commentary interprets poem

## Design Rule

The graph should be treated as intellectual architecture first.
Database tables and APIs should implement this graph, not define it.
