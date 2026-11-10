# Confidentiality check

## When

Before anything leaves the machine: the recipient is elsewhere, a remote session or unknown, or a zip is made.
A zip is checked even for the same machine, because it is easy to pass on. Only a same-machine prompt with no zip
skips the check.

## Scope

- Files that go into a zip.
- Every hunk of a patch or inline diff.
- Values quoted in the prompt: an email address, a token in a log line, a customer record.
- Files the prompt mentions that hold sensitive data, even if you plan to describe them only in words. The user
  decides how each one travels; the table gives the default you propose.

Names of clients, projects and documents in the prose stay, because the recipient needs them for context.

## Procedure

1. Classify each item by the most sensitive data it holds, using the table.
2. If nothing is found, go on without asking.
3. Otherwise ask one question that lists each finding with its type and proposed default. The user confirms or
   changes the defaults item by item.

| Type | Examples | Default |
|---|---|---|
| Secret | API keys, tokens, passwords, private keys, `.env` files, credentials in URLs | exclude, and mention it in general terms ("a local `.env` with the API key") |
| Personal data | names, email addresses, phone numbers, postal addresses, customer records | anonymize |
| Confidential document | client documents, contracts, internal reports | mention it in general terms (alternative: as is) |
| Code and non-sensitive material | source code, tests, public documentation | as is |

Something excluded stays excluded everywhere: a file or hunk left out of the zip is also left out of the patch
and the prompt.

## Question format

```text
Before the handoff leaves this machine, check these items (reply with the numbers to change):
1. acme-invoices-2026-03.csv (outside the repository): personal data, customer names and emails → anonymize
2. bug22-debug.log, line 3: secret, API key → exclude, mention in general terms
3. .env (changed in the working tree): secret → exclude
```

## Anonymizing

Replace each value with a placeholder of the same shape, and use the same placeholder for the same value across
all files: `Giulia Ferri` becomes `Customer A`, `giulia.ferri@acme.test` becomes `customer-a@example.com`.
Keep values that matter to the work and are not personal, such as dates and amounts that reproduce a bug.

## Push scan

Before offering to push local-only commits, scan each of them with the table above, messages included:
`git log -p --diff-merges=first-parent <base>..HEAD`. The net diff is not enough, because a secret added in one
commit and removed in a later one is still published by the push. If the scan turns up anything, do not offer
the push: those commits travel in the patch and go through this check.

## Paths and URLs

- A prompt for anyone but the same machine carries no absolute local paths, which reveal user names and folder
  layout. Use repo-relative paths, and describe outside files in words or by their name in the zip.
- For an unknown recipient, the only local path is the repository root, written with `~` for the home directory
  (`~/src/invoice-parser`), so that a session on the same machine can find it.
- Strip credentials from remote URLs: `https://user:token@github.com/acme/app.git` becomes
  `https://github.com/acme/app.git`.
