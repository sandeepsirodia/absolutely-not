# Installing absolutely-not (instructions for coding agents)

If a user asked you to install this skill, do this:

1. Fetch `https://raw.githubusercontent.com/sandeepsirodia/absolutely-not/main/skills/absolutely-not/SKILL.md`.
2. Install it for the agent you are:
   - **Claude Code:** save it as `~/.claude/skills/absolutely-not/SKILL.md` (all projects) or `.claude/skills/absolutely-not/SKILL.md` (this project only). Ask which, defaulting to all projects.
   - **Codex:** save it as `~/.codex/skills/absolutely-not/SKILL.md`.
   - **Cursor:** save the body (without the `---` frontmatter) as `.cursor/rules/absolutely-not.mdc`, with frontmatter `alwaysApply: true`.
   - **Anything else:** append the body to the project's `AGENTS.md` under a `## absolutely-not` heading.
3. Don't overwrite an existing file without showing the user a diff first.
4. Tell the user it's installed and that it applies from the next session.
