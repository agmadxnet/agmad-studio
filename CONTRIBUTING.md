# Contributing

Start with a small reproducible issue tied to a tool/project and version. Use synthetic inputs. Record expected vs actual results, browser/OS and testing limits. Do not attach passwords, keys, customer data, private screenshots or original game assets.

Preserve proven processing engines unless a verified defect requires a change. Keep shared Core changes separate from module changes where practical. Every release needs an accurate changelog, input/output limits, compatibility evidence and a recovery path.

Use a branch and reviewable PR. Do not assume a merged documentation change deploys the website. Existing repository/project instructions and licenses take precedence; inspect them before implementation.

## Documentation privacy checks

Before committing public documentation, run:

```sh
python3 scripts/check_doc_privacy.py
python3 -m unittest discover -s tests -v
```

The read-only check enumerates Git-tracked documentation anywhere in the repository, including templates, Markdown, text, HTML, structured metadata and license/notice files. New untracked files must be staged before a local check; CI checks the committed snapshot on pushes and pull requests. Missing, unreadable, non-UTF-8 or symlinked documents fail rather than being silently skipped.

The rules mirror Silent Cutter's targeted safeguards for the previously removed private team attribution (English/Arabic) and private home/workspace references. Diagnostics report the file, line and category without echoing matched text; sensitive filenames are redacted. Generic build placeholders, standard per-user application locations and ordinary technical documentation remain valid.

This is a targeted regression check, not detection of every possible personal name or secret. Human review is still required for new names, private data and publication claims. If a rule matches required license or copyright attribution, preserve the attribution and review the rule; never remove legal notices to make CI pass. The check does not edit files, rewrite history, deploy the website or change release assets.
