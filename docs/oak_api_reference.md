# Oak National Academy Open API Reference

## Overview

| Item | Detail |
|------|--------|
| Base URL | `https://open-api.thenational.academy/api/v0` |
| Authentication | `Authorization: Bearer {OAK_API_KEY}` |
| Rate Limit | 1000 requests/hour |
| Versioning | Semantic versioning (currently v0) |
| License | Open Government Licence v3.0 (compatible with CC-BY 4.0) |

### Changelog

```
GET /changelog          # full changelog
GET /changelog/latest   # latest changes only
```

---

## Key Stage / Year Mapping

| Key Stage | Years | Age Range |
|-----------|-------|-----------|
| KS1 | Year 1-2 | 5-7 |
| KS2 | Year 3-6 | 7-11 |
| KS3 | Year 7-9 | 11-14 |
| KS4 | Year 10-11 | 14-16 |

## Available Subjects

science, maths, english, history, geography, computing, spanish, french, german, latin, art, citizenship, cooking-nutrition, design-technology, drama, financial-education, music, physical-education, religious-education, rshe-pshe

---

## 1. Lists Endpoints

### 1.1 GET /subjects

All subjects with sequences, key stages, years.

### 1.2 GET /subjects/{subject}

Single subject details.

### 1.3 GET /subjects/{subject}/sequences

Sequence objects for a subject.

### 1.4 GET /subjects/{subject}/key-stages

Key stages for a subject.

### 1.5 GET /subjects/{subject}/years

Available years for a subject.

### 1.6 GET /key-stages

All key stages.

```json
[
  {"slug": "ks1", "title": "Key Stage 1"},
  {"slug": "ks2", "title": "Key Stage 2"},
  {"slug": "ks3", "title": "Key Stage 3"},
  {"slug": "ks4", "title": "Key Stage 4"}
]
```

### 1.7 GET /key-stages/{keyStage}/subject/{subject}/lessons

Lessons grouped by unit.

| Parameter | Required | Description |
|-----------|----------|-------------|
| unit | No | Filter by unit slug |
| offset | No | Pagination offset |
| limit | No | Number of results |

```json
[
  {
    "unitSlug": "unit-slug",
    "unitTitle": "Unit Title",
    "lessons": [
      {"lessonSlug": "lesson-slug", "lessonTitle": "Lesson Title"}
    ]
  }
]
```

### 1.8 GET /key-stages/{keyStage}/subject/{subject}/units

Units grouped by year.

```json
[
  {
    "yearSlug": "year-7",
    "yearTitle": "Year 7",
    "units": [
      {"unitSlug": "unit-slug", "unitTitle": "Unit Title"}
    ]
  }
]
```

### 1.9 GET /threads

All threads across subjects.

### 1.10 GET /threads/{threadSlug}/units

Units in a thread.

---

## 2. Lesson Data Endpoints

### 2.1 GET /lessons/{lesson}/transcript

```json
{
  "transcript": "full text string",
  "vtt": "WebVTT caption format"
}
```

### 2.2 GET /lessons/{lesson}/assets

| Parameter | Required | Description |
|-----------|----------|-------------|
| type | No | Filter by asset type |

```json
{
  "attribution": [],
  "assets": [
    {"type": "slideDeck", "label": "Slide Deck", "url": "https://..."}
  ]
}
```

### 2.3 GET /lessons/{lesson}/assets/{type}

Binary file stream download.

### 2.4 GET /lessons/{lesson}/summary

```json
{
  "lessonTitle": "Lesson Title",
  "unitSlug": "unit-slug",
  "unitTitle": "Unit Title",
  "subjectSlug": "maths",
  "subjectTitle": "Maths",
  "keyStageSlug": "ks2",
  "keyStageTitle": "Key Stage 2",
  "lessonKeywords": [
    {"keyword": "fraction", "description": "A part of a whole"}
  ],
  "keyLearningPoints": [
    {"keyLearningPoint": "Understand fractions as parts of a whole"}
  ],
  "misconceptionsAndCommonMistakes": [
    {"misconception": "...", "response": "..."}
  ],
  "pupilLessonOutcome": "...",
  "teacherTips": "...",
  "contentGuidance": "...",
  "supervisionLevel": "...",
  "downloadsAvailable": true
}
```

---

## 3. Unit and Curriculum Data Endpoints

### 3.1 GET /sequences/{sequence}/units

Units in a sequence.

| Parameter | Required | Description |
|-----------|----------|-------------|
| year | No | Filter by year |

Response includes: year, unitTitle, unitOrder, unitSlug, categories, threads.

### 3.2 GET /sequences/{sequence}/assets

Lesson assets in a sequence.

| Parameter | Required | Description |
|-----------|----------|-------------|
| year | Yes | Year filter |
| type | No | Asset type filter |

**Asset types:** slideDeck, exitQuiz, exitQuizAnswers, starterQuiz, starterQuizAnswers, supplementaryResource, video, worksheet, worksheetAnswers

### 3.3 GET /sequences/{sequence}/questions

Quiz questions in a sequence.

| Parameter | Required | Description |
|-----------|----------|-------------|
| year | Yes | Year filter |
| offset | No | Pagination offset |
| limit | No | Number of results |

### 3.4 GET /units/{unit}/summary

```json
{
  "unitSlug": "unit-slug",
  "unitTitle": "Unit Title",
  "year": "year-7",
  "phaseSlug": "secondary",
  "subjectSlug": "maths",
  "keyStageSlug": "ks3",
  "priorKnowledgeRequirements": ["..."],
  "nationalCurriculumContent": ["..."],
  "threads": [],
  "categories": [],
  "unitLessons": []
}
```

---

## 4. Quiz Questions Endpoints

### 4.1 GET /lessons/{lesson}/quiz

Each quiz contains 6 questions.

```json
{
  "starterQuiz": [],
  "exitQuiz": []
}
```

**Question structure:**

```json
{
  "question": "What is 2 + 2?",
  "questionType": "multiple-choice",
  "answers": [
    {"content": "4", "type": "text", "distractor": false, "matchOption": null, "correctChoice": null, "order": null}
  ]
}
```

**Question types:**

| Type | How to identify correct answer |
|------|-------------------------------|
| `multiple-choice` | `distractor: false` = correct answer |
| `short-answer` | All answers are acceptable variations (all `distractor: false`) |
| `match` | `matchOption` = prompt, `correctChoice` = answer |
| `ordering` | `order` field indicates correct sequence position |

### 4.2 GET /sequences/{sequence}/questions

All quiz questions for a sequence.

### 4.3 GET /key-stages/{keyStage}/subject/{subject}/questions

Quiz questions by subject and key stage.

| Parameter | Required | Description |
|-----------|----------|-------------|
| offset | No | Pagination offset |
| limit | No | Number of results |

---

## 5. Search Endpoints

### 5.1 GET /search/transcripts?q=xxx

Top 5 lessons by transcript similarity.

```json
[
  {
    "lessonTitle": "Lesson Title",
    "lessonSlug": "lesson-slug",
    "transcriptSnippet": "...matching text..."
  }
]
```

### 5.2 GET /search/lessons?q=xxx

Top 20 lessons by title similarity.

| Parameter | Required | Description |
|-----------|----------|-------------|
| q | Yes | Search query |
| keyStage | No | Filter by key stage |
| subject | No | Filter by subject |
| unit | No | Filter by unit |

```json
[
  {
    "lessonSlug": "lesson-slug",
    "lessonTitle": "Lesson Title",
    "similarity": 0.95,
    "units": [
      {
        "unitSlug": "unit-slug",
        "unitTitle": "Unit Title",
        "keyStageSlug": "ks2",
        "subjectSlug": "maths"
      }
    ]
  }
]
```

---

## Reference URLs

| Resource | URL |
|----------|-----|
| Docs | https://open-api.thenational.academy/docs |
| API Overview | https://open-api.thenational.academy/docs/about-oaks-api/api-overview |
| API Limits | https://open-api.thenational.academy/docs/about-oaks-api/api-limits |
| Versioning | https://open-api.thenational.academy/docs/about-oaks-api/versioning |
| Playground | https://open-api.thenational.academy/playground |
| Lists | https://open-api.thenational.academy/docs/api-endpoints/lists |
| Lesson Data | https://open-api.thenational.academy/docs/api-endpoints/lesson-data |
| Unit/Curriculum | https://open-api.thenational.academy/docs/api-endpoints/unit-and-curriculum-data |
| Quiz Questions | https://open-api.thenational.academy/docs/api-endpoints/quiz-questions |
| Search | https://open-api.thenational.academy/docs/api-endpoints/search |
