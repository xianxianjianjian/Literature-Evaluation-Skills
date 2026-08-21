# Topic Planning

Topic planning is a distinct pre-search stage. Do not begin formal literature retrieval until the user confirms the weekly topic.

## Required context

Before proposing topics, read when available:

- `knowledge/research_profile.md`;
- `knowledge/reading_history.csv`;
- recent `knowledge/selection_log.csv` entries;
- prior weekly `topic_selection.md`, `search_record.md`, and Open Questions / Next Reading Direction;
- explicit constraints in the current request.

Long-term research direction is user-controlled. A Skill may propose an update to `research_profile.md`, but must not change it because of one paper or one weekly search without explicit approval.

## Candidate generation

Normally propose 3–5 non-redundant topic candidates that serve different functions:

1. continuation of a previously unresolved question;
2. the current core research problem;
3. a methodological supplement or measurement problem;
4. an adjacent direction with clear transfer value;
5. a frontier direction worth checking for recent developments.

Do not invent a candidate merely to fill all five categories. Distinguish low-value repetition from legitimate deepening, replication, contradiction checking, and necessary backtracking.

For each candidate record:

- candidate id;
- candidate type;
- proposed topic;
- core research question;
- why it matters now;
- connection to previous reading or current research;
- expected evidence needed;
- preferred study type;
- likely method/measurement value;
- likely transfer value;
- priority and rationale;
- uncertainty or known evidence gap.

## User Gate

The user retains final topic authority. Before confirmation:

- write/update `weekly_reviews/YYYY/YYYY-Wxx/topic_selection.md`;
- set the manifest topic stage to `WAITING_USER`;
- do not treat a suggested topic as selected;
- do not start formal database searching.

After explicit confirmation, record the selected topic and set the topic stage to `COMPLETE`; Search may then enter `IN_PROGRESS`.

## `topic_selection.md` minimum structure

```markdown
# Topic Selection

- Week:
- Status:
- Context reviewed:

## Candidates
### TOPIC-01
- Type:
- Topic:
- Core question:
- Why now:
- Link to previous reading:
- Expected evidence:
- Preferred study type:
- Method/measurement value:
- Transfer value:
- Priority:
- Notes:

## User-confirmed topic
- Selected candidate:
- Confirmed topic:
- Confirmation date:
```

The file is a decision record, not a substitute for `research_profile.md`.