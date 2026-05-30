---
name: project-doc-writer
description: 'Create or update project.md with project info, development rules, implementation status, feature history, and per-feature updates. Use for living project documentation, build summaries, and project handoff notes.'
argument-hint: 'Project docs to capture in project.md'
---

# Project Doc Writer

## When to Use
- Create a living `project.md` file for a repository
- Capture how to develop the project, the rules to follow, and the current project state
- Record what has been built so far and append updates for each feature
- Turn scattered documentation into one authoritative project reference

## Goal
Produce a root-level `project.md` file that acts as the project’s working memory. It should be easy to scan, easy to update, and focused on the current state of the codebase.

## Procedure
1. Inspect the project’s existing documentation and source structure first.
2. Extract the project name, purpose, stack, run commands, folder layout, and main architecture.
3. Collect the development rules the team should follow, including coding conventions, architectural constraints, and any workflow notes.
4. Summarize what has already been built, separating completed work from partially complete or pending work.
5. Build or update `project.md` at the repository root.
6. Preserve existing content when the file already exists, and append new feature updates instead of overwriting useful history.
7. Add a dated update entry for each meaningful feature or change, including what was built, where it lives, and any follow-up work.

## `project.md` Structure
Use clear headings and keep the document practical:
- `Project Info`
- `How to Develop`
- `Rules to Follow`
- `Built So Far`
- `Feature Updates`
- `Current Status`
- `Open Work` or `Next Steps`

## What to Capture
Include the most useful facts only:
- Project purpose and scope
- Main technologies and services
- Local setup and run steps
- Directory and module overview
- Design and implementation rules
- Completed features and their status
- Recent feature-level updates with dates
- Known gaps, risks, or pending work

## Update Rules
- Keep entries specific and factual.
- Prefer short bullets over long paragraphs.
- When adding a new feature update, include the feature name, status, short description, and relevant file locations if known.
- If the repo already has release notes or summaries, link or summarize them instead of duplicating them all verbatim.
- If information is uncertain, mark it as unverified rather than guessing.

## Completion Check
The skill is complete when `project.md`:
- Exists at the repo root
- Describes how to develop the project
- Lists the rules to follow
- Summarizes what is built so far
- Includes feature-by-feature updates
- Reflects the current state of the codebase without stale claims

## Example Output Shape
```markdown
# Project Name

## Project Info
...

## How to Develop
...

## Rules to Follow
...

## Built So Far
...

## Feature Updates
- 2026-05-31: Added ...

## Current Status
...

## Next Steps
...
```
