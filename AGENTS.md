# Agent rules — FleetKit

## Authorship (hard rule)

- **Единственный автор репозитория:** Богдан Щербинин / `blessed-bless`.
- В Contributors, authors, LICENSE copyright, README, `Co-authored-by`, commit author/committer, tagger и любых «создано с помощью» полях — **только** он. Никаких Cursor / AI / bot / agent.
- Перед каждым `git commit` и `git tag` выставляй:

```bash
git config user.name "Bogdan Shcherbinin"
git config user.email "blessed-bless@users.noreply.github.com"
```

- Запрещено оставлять в истории `Cursor Agent`, `cursoragent@cursor.com`, `cursor[bot]`, `github-actions` как автора коммита (кроме системных merge committer `GitHub <noreply@github.com>` на merge через UI — author merge должен быть `blessed-bless`).
- Если агент уже закоммитил под чужим именем — перепиши author/committer на `blessed-bless` **до** push. На защищённом `master` — через PR только с правильным author; history rewrite на `master` требует force-push (см. `scripts/reauthor_to_owner.sh`).

## Commits / PR

- Imperative subject: `feat:`, `fix:`, `docs:`, `chore:`.
- Не добавляй `Co-authored-by: Cursor` / AI trailer.
