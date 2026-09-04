---
name: release
description: Cut a release — changelog section, version bumps, verification, commit, tag. Use when the user wants to release, publish, bump the version, or ship the current branch.
---

# Release ritual

Three places must agree on the version: `CHANGELOG.md`, `service/app.py`, and
the git tag. This ritual keeps them in lockstep.

## 1. Pick the version

Semver from what's shipping since the last released section: breaking API
change → major; new observable behavior (endpoint, event type, sink) → minor;
fixes only → patch. Confirm the number with the user if it's ambiguous.

## 2. Changelog

- Add a new `## [x.y.z] - YYYY-MM-DD - Short Title` section at the top,
  dated **today** (the ship date, not when work happened).
- **Never edit an already-released section** — prior versions are history.
- Follow the house style: themed `####` subsections under `### Major Changes`,
  then `### Modified Files`. Describe observable behavior, not diffs.
- Note the bundled Zoom SDK version if it changed (`sdk-version.lock`).

## 3. Version strings

Update **both** spots in `service/app.py`: the `FastAPI(version=...)`
constructor and the root endpoint's `"version"` field.

## 4. Verify

Run `/run-tests` (all suites). Do not proceed on any failure.

## 5. Commit, tag, push

Review `git status` first and stage **deliberately** — never `git add -A` (it
scoops up unrelated untracked files: logs, scratch docs, local configs):

```bash
git add CHANGELOG.md service/app.py <other release files>
git commit -m "chore(release): x.y.z"
git tag vx.y.z
git push && git push --tags
```

Pushing triggers `dockerhub-build-push.yml`: build → contract → lifecycle →
unit+smoke → push image. Confirm the Actions run goes green; the image tag is
`<branch>-<sha>`.

## Notes

- Live e2e against the lab room is the manual pre-release step for changes
  touching the connection lifecycle — remind the user, don't run it unasked.
- If the release includes new sinks, verify the run-tests skill's expected
  counts were updated.
