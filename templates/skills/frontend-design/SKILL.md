# Frontend Design

Design and implement UI components with accessibility, responsiveness, and clean component structure.

**Announce at start:** "Using frontend-design skill."

## Process

1. **Understand requirements** — what does the user need to do, see, or feel?
2. **Sketch component structure** — identify: container, presentational, and interactive components
3. **Design the data flow** — props down, events up; identify shared state
4. **Implement with TDD** — Vitest for logic, Playwright for user flows
5. **Verify in browser** — start dev server, check golden path AND edge cases

## Component design rules

**Single responsibility:** each component does one thing. If you're scrolling to find where it ends, split it.

**Props interface:** define types before writing JSX. If the props interface looks messy, the component is doing too much.

**No business logic in components.** Extract to hooks or utilities. Components render; hooks manage state and side effects.

## Accessibility (non-negotiable)

- Semantic HTML: `<button>` not `<div onClick>`, `<nav>` not `<div class="nav">`
- Every interactive element keyboard-accessible
- Images have `alt` text (empty string for decorative)
- Forms: `<label>` associated with every input
- Color contrast: 4.5:1 minimum for text

## Responsive design

- Mobile-first: base styles for small, override for larger
- Use CSS Grid and Flexbox — avoid fixed pixel widths
- Test at 375px, 768px, 1280px minimum

## State management

- Local state (`useState`) first — only lift if two+ siblings need it
- `useReducer` when state transitions are complex (>3 state variables that change together)
- External store (Zustand, Jotai) only when state is truly global

## Done means

- Component renders correctly at all breakpoints
- Keyboard navigation works
- Playwright E2E test covers the main user flow
- Vitest unit tests for any business logic in hooks
- No console errors or warnings
- `pnpm exec playwright test` passes
