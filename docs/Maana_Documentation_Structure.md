# Maana Documentation Structure

> Documentation structure for the Maana repository.

## Philosophy

The documentation is divided into four major layers:

1. Product
2. Domain Knowledge
3. Technical Architecture
4. Editorial Knowledge

The goal is to make every important decision explicit before implementation.

---

# docs/

```
docs/

00-overview/
01-philosophy/
02-product/
03-domain/
04-ontology/
05-information-architecture/
06-user-experience/
07-design-system/
08-data-model/
09-search/
10-api/
11-backend/
12-frontend/
13-editorial/
14-content/
15-security/
16-analytics/
17-deployment/
18-roadmap/
19-ai/
20-decisions/
```

---

# 00-overview

Purpose:

Introduce the project.

Files

```
README.md
Vision.md
Mission.md
Goals.md
NonGoals.md
Glossary.md
```

---

# 01-philosophy

This is the soul of the project.

Files

```
WhyThisExists.md

KnowledgeFirst.md

HumanExperience.md

PoetryAsKnowledge.md

CrossCivilization.md

EditorialPrinciples.md
```

These documents should answer:

Why should this product exist?

---

# 02-product

Traditional product documentation.

Files

```
Personas.md

UserStories.md

Requirements.md

SuccessMetrics.md

Pricing.md

MVP.md

Roadmap.md
```

---

# 03-domain

Defines the literary universe.

Files

```
Poets.md

Poems.md

Verses.md

Languages.md

Civilizations.md

LiterarySchools.md

Meters.md

Rhyme.md

Translations.md
```

---

# 04-ontology

This will become the most valuable part of the company.

Files

```
HumanExperiences.md

Symbols.md

Themes.md

Concepts.md

Relationships.md

KnowledgeGraph.md
```

Example

Love

↓

Longing

↓

Absence

↓

Death

↓

Memory

Every concept becomes searchable.

---

# 05-information-architecture

Navigation.

Files

```
Sitemap.md

Navigation.md

Menus.md

SearchFlow.md

ReadingFlow.md
```

---

# 06-user-experience

Every screen.

```
Home.md

PoemPage.md

PoetPage.md

ThemePage.md

SymbolPage.md

ExperiencePage.md

Search.md

Collections.md

Settings.md
```

---

# 07-design-system

```
Typography.md

Spacing.md

Buttons.md

Cards.md

Colors.md

Icons.md

DarkMode.md
```

---

# 08-data-model

Complete database.

```
ERD.md

Tables.md

Indexes.md

Constraints.md

Migrations.md

Versioning.md
```

---

# 09-search

Everything about discovery.

```
SearchRanking.md

Autocomplete.md

Filters.md

Recommendations.md

RelatedPoems.md

RelatedSymbols.md
```

---

# 10-api

Every endpoint.

```
REST.md

Authentication.md

Poems.md

Search.md

Themes.md

Symbols.md
```

---

# 11-backend

Engineering decisions.

```
Architecture.md

Caching.md

Storage.md

BackgroundJobs.md

Security.md
```

---

# 12-frontend

```
ComponentLibrary.md

Routing.md

StateManagement.md

Performance.md
```

---

# 13-editorial

How content is written.

```
CommentaryStyle.md

AnnotationRules.md

TranslationGuide.md

CitationRules.md

FactChecking.md
```

This is essential for consistency.

---

# 14-content

The publishing workflow.

```
EditorialWorkflow.md

Publishing.md

VersionHistory.md

QualityChecklist.md
```

---

# 15-security

```
Authentication.md

Authorization.md

Encryption.md

Privacy.md
```

---

# 16-analytics

```
Events.md

Funnels.md

KPIs.md
```

---

# 17-deployment

```
Infrastructure.md

CI-CD.md

Monitoring.md

Backup.md
```

---

# 18-roadmap

```
MVP.md

V2.md

V3.md

FutureIdeas.md
```

---

# 19-ai

Notice that AI is intentionally placed near the end.

```
FutureAI.md

PromptLibrary.md

Caching.md

Evaluation.md

Moderation.md
```

AI enhances the knowledge graph rather than replacing it.

---

# 20-decisions

Every architectural decision is recorded.

```
ADR-001.md

ADR-002.md

ADR-003.md
```

Each Architecture Decision Record (ADR) explains:

* Problem
* Options considered
* Decision
* Consequences

This prevents the team from revisiting the same debates repeatedly.

---

# Guiding Principle

The product is not a collection of poems.

It is a structured knowledge graph of humanity's literary, philosophical, emotional, and spiritual heritage.

Every feature, database table, API, and interface should reinforce that central vision.
