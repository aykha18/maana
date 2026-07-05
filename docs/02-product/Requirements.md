# Requirements

## Product Pillars

Maana has two product pillars:

1. Reading and discovery: help readers find poems through questions, experiences,
   themes, symbols, and relationships.
2. Reader formation: help readers build the inner vocabulary needed to understand
   demanding literature.

The second pillar is not a side feature. It is part of the product core.

## Core Requirement Areas

### 1. Foundations for Understanding

Before a user reads a poem, the product may surface a small set of prerequisite
ideas that materially improve comprehension.

Examples:

- longing
- impermanence
- the nature of desire
- Sufi symbolism
- Persian literary tradition

Requirements:

- Every poem may declare zero or more foundations.
- Foundations must be editorially selected, not automatically guessed in MVP.
- Foundations must be clickable and open a concept or experience page.
- Foundations must explain why the idea matters for reading this poem.
- The UI must support lightweight pre-reading without blocking access to the poem.

### 2. Reading Prerequisites

The system should be able to say:

- "To fully appreciate this work, familiarity with these ideas will help."
- "You are already well prepared for this poem."
- "You may want to explore these foundations first."

Requirements:

- Prerequisites must be framed as help, not gatekeeping.
- The system must distinguish required context from optional enrichment.
- Estimated pre-reading time should be visible where appropriate.

### 3. Human Experience Academy

Maana should include short learning units that develop familiarity with core human
experiences, concepts, and literary ideas.

Examples:

- What is longing?
- What is irony?
- Why do humans grieve?
- What is transcendence?
- What is beauty?

Requirements:

- Lessons should be short, ideally 3-7 minutes.
- Lessons should combine multiple modes of understanding, such as story, poetry,
  philosophy, psychology, and religious or civilizational context.
- Lessons must aim for understanding, not testing.

### 4. Reflection Instead of Quizzing

The learning model should privilege reflection over quiz mechanics.

Requirements:

- Reflection prompts should connect literature to lived experience.
- Reflection answers may be private by default.
- Multiple-choice quizzes must not be the primary learning mechanic.
- The system should track completion of reflection activities without turning them
  into academic grading.

### 5. Readiness and Familiarity

Maana should distinguish between knowledge and readiness.

Definitions:

- Knowledge: the user has encountered a concept definition or explanation.
- Readiness: the user has built enough familiarity to receive a poem more deeply.

Requirements:

- The product should track explored concepts, poems, lessons, and reflections.
- Readiness should be expressed gently, such as "well prepared" or "lightly explored,"
  not as certification.
- Progress language should emphasize sensitivity and familiarity, not mastery in the
  gamified sense.

### 6. Human Experience Map

Each user may have a personal map of explored questions, experiences, concepts, and
 poems.

Requirements:

- The map should show exploration breadth and depth.
- The map should connect explored poems back to concepts and experiences.
- The map should support recommendations for next readings or lessons.
- The map must not imply that human understanding is linear or complete.

## Editorial Requirements

- Foundations, lessons, and readiness recommendations must remain citation-friendly
  and editorially explainable.
- Where claims involve psychology, religion, or philosophy, the system should support
  evidence-backed explanations rather than loose inspirational writing.
- Contradictory interpretations must remain possible.

## MVP Requirement Cuts

The MVP should include:

- foundations on poem pages
- clickable concept and experience pages
- at least one lesson format for the Human Experience Academy
- reflection prompts
- simple readiness states based on editorial rules and completed exploration

The MVP does not need:

- adaptive AI tutoring
- social learning
- advanced mastery systems
- complex scoring

