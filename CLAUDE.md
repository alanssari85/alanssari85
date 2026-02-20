# CLAUDE.md

This file provides guidance for AI assistants (Claude and others) working in this repository.

---

## Repository Overview

This is a newly initialized repository (`alanssari85/alanssari85`). As the project grows, update this file with:
- Project purpose and architecture description
- Technology stack details
- Non-obvious design decisions

Until the project is established, follow the conventions below.

---

## Project Status

**Current state:** Empty repository — no source code, dependencies, or build system have been added yet.

When the first code is committed, update this section with:
- Language and runtime versions
- Framework(s) in use
- High-level architecture diagram or description

---

## Development Workflow

### Branch Naming

| Purpose | Pattern | Example |
|---|---|---|
| Features | `feature/<short-description>` | `feature/user-auth` |
| Bug fixes | `fix/<short-description>` | `fix/login-redirect` |
| Chores / config | `chore/<short-description>` | `chore/update-deps` |
| AI-assisted work | `claude/<session-id>` | `claude/claude-md-mlvc7709zye6f216-BToSm` |

Never push directly to `main`. Always open a pull request.

### Commit Messages

Use the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<optional scope>): <short imperative summary>

<optional body — explain *why*, not *what*>
```

Common types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`

Examples:
```
feat(auth): add JWT refresh token rotation
fix(api): handle null response from upstream service
docs: add CLAUDE.md with development conventions
```

- Subject line: ≤ 72 characters, imperative mood, no trailing period
- Reference issues when relevant: `Closes #42`

### Pull Request Guidelines

- Keep PRs focused and small — one logical change per PR
- Include a description of *what* changed and *why*
- Ensure all CI checks pass before requesting review
- Do not merge your own PRs without review unless the project is solo

---

## Code Conventions

These are defaults; override them when a language/framework-specific config file is present in the repo.

### General

- Prefer readability over cleverness
- Name things clearly: variables, functions, and files should be self-describing
- Avoid dead code — delete unused code rather than commenting it out
- No magic numbers or strings without named constants
- Keep functions small and single-purpose

### Security

- Never commit secrets, tokens, passwords, or API keys — use environment variables or a secrets manager
- Add `.env` to `.gitignore` immediately; provide a `.env.example` instead
- Validate and sanitize all input at system boundaries (user input, external APIs)
- Follow OWASP Top 10 guidance for web projects

### Error Handling

- Fail fast: surface errors early rather than silently swallowing them
- Log errors with sufficient context to reproduce the issue
- Never expose internal stack traces to end users

---

## Testing

When tests are introduced, update this section with:
- Test runner command (e.g., `npm test`, `pytest`, `go test ./...`)
- Location of test files
- Coverage requirements or thresholds

General testing principles (before a framework is chosen):
- Write tests alongside new code, not after
- Unit-test pure logic; integration-test system boundaries
- Tests should be deterministic and runnable without network access

---

## CI / CD

No CI pipeline exists yet. When one is added (e.g., GitHub Actions), document:
- Workflow file locations (`.github/workflows/`)
- What triggers each workflow (push, PR, schedule)
- Required environment secrets and where to configure them

---

## Adding Dependencies

Before adding any dependency:
1. Confirm it is actively maintained and has an appropriate license
2. Check for known vulnerabilities (e.g., `npm audit`, `pip-audit`, `cargo audit`)
3. Prefer standard-library solutions when they are sufficient

---

## AI Assistant Instructions

When working in this repository as an AI assistant:

1. **Read before writing** — always read relevant existing files before making changes
2. **Minimal changes** — only modify what is necessary for the task; avoid refactoring unrelated code
3. **No speculative features** — implement only what was requested
4. **Update this file** — if you discover conventions, architecture decisions, or workflows that are missing from this document, add them
5. **Branch discipline** — develop on the designated feature branch; never push to `main`
6. **Test your changes** — run the test suite (once one exists) and confirm it passes before committing
7. **Security first** — never introduce secrets into version control, never generate vulnerable patterns (SQL injection, XSS, command injection, etc.)
8. **Commit messages** — follow the Conventional Commits format described above

---

## Updating This File

This file should evolve with the codebase. Update it when:
- A new technology, framework, or tool is adopted
- A non-obvious architectural decision is made
- A recurring review comment reveals a missing convention
- The project structure changes significantly

Keep it concise: link to external documentation rather than reproducing it here.
