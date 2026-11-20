# Manual

For any other harness, or when the start fails. Write the handoff files, then give the user, per child, one block
with the commands to run in a new terminal:

```bash
cd <repo>
codex "Read and follow <file>"
```

Use the start command of the child's agent kind. For a Claude child,
`[env HOME=<home> CLAUDE_CONFIG_DIR=<dir>] claude <carried flags> -n <name> --permission-mode <mode> --add-dir <handoff-dir> "Read and follow <file>"`
keeps the messaging channel, with the master's identity and flags (*Launch command* in
[environments.md](../environments.md)) and the permission mode the children inherit. With other
kinds there is no automatic channel: the child's reports reach the master through the user.
