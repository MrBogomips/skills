# Session wrap-up

Runs when the author signals the end of the work session.

## 1. Was the plugin used?

If no personal-voice skill was used in this session, do nothing and say
nothing about the voice profile.

## 2. Record what was missed

- Look through the session for revisions (pasted finals, corrections) that
  were not followed by a recording notice. Record them now, following
  `revision.md`.
- Re-read each file Claude wrote for people in this session (documents, not
  code). Compare it with the latest version already learned from in this
  session, or with what Claude last wrote if it was never learned from. Record
  only differences not yet recorded; a change already recorded is not new
  evidence.

During the wrap-up, do not show the per-recording notice or maintenance
suggestion from `recording.md`: the recap below replaces them.

## 3. Recap

At most two lines, in the language of the conversation: observations recorded
in this session, and the total now pending across both stores.

```
Voice profile: 4 observations recorded today; 12 pending in total.
```

## 4. Offer maintenance

If a threshold from `recording.md` §5 is reached, ask whether to run
maintenance now. On yes, invoke `personal-voice:voice-maintain`. Otherwise stop.
