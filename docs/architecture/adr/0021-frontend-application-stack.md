# ADR-0021: Frontend Application Stack — Next.js 15 Ecosystem

**Status:** Accepted

## Context

Signora's frontend serves Revenue Intelligence Platform's dashboards, Timeline feeds, and recommendation workflows to sales users — data-dense, interactive, AI-output-rendering UI. The stack must support server rendering for performance, strong typing end-to-end, and a component ecosystem mature enough to build data tables, virtualized lists, rich text (for AI reasoning output), and charts without excessive custom-build burden.

## Decision

**Next.js 15+** with **TypeScript**, **Tailwind CSS**, **shadcn/ui** (built on **Radix UI** primitives), **React Hook Form** + **Zod**, **Lucide** icons, **Motion** (Framer Motion), **TanStack Table**, **TanStack Virtual**, **TanStack Query**, **react-markdown**, **Tiptap**, **next-themes**, **Recharts**, **cmdk**, and **Sonner** — adopted together as one integrated frontend decision.

## Alternatives Considered

| Layer | Alternative | Why not chosen |
|---|---|---|
| Framework | Remix, plain Vite + React SPA | Next.js 15's App Router, server components, and ecosystem maturity (especially around the shadcn/ui component ecosystem) outweigh Remix's comparable capability; a plain SPA would forgo server-rendering performance benefits for a dashboard-heavy product where initial load performance matters. |
| Component library | Building custom components from scratch, or Material UI / Ant Design | shadcn/ui's copy-into-your-repo model (not an npm dependency you can't customize) gives full ownership of component code while starting from Radix UI's accessibility-correct primitives — avoiding both the "reinvent everything" cost of fully custom components and the customization ceiling of a prescriptive component library like Material UI/Ant Design. |
| Forms/validation | Formik, or hand-rolled form state | React Hook Form's performance (uncontrolled-by-default) and Zod's TypeScript-first schema validation, sharing validation logic conceptually with the backend's Pydantic v2 approach ([ADR-0004](0004-data-validation-and-serialization.md)), were judged the stronger combination. |
| Data fetching | SWR, Redux + RTK Query, hand-rolled fetch/state | TanStack Query's cache invalidation, background refetching, and optimistic update support fit the dashboard-refresh-on-pipeline-event pattern ([07-data-flow.md](../07-data-flow.md)) better than SWR's simpler feature set or Redux's heavier state-management ceremony for what is fundamentally server-state, not client-state. |
| Rich text | Slate, Lexical, hand-rolled contentEditable | Tiptap's ProseMirror foundation and Next.js/React ecosystem maturity were judged the best fit for rendering/editing AI-reasoning-adjacent rich content without excessive custom-build burden. |
| Charts | Nivo, Visx, D3 directly | Recharts' React-native API and sufficient customization for Revenue Intelligence Platform's dashboard needs outweigh D3's raw power (unnecessary complexity for standard chart types) and Nivo's/Visx's smaller ecosystems. |

## Tradeoffs

**We gain:** an integrated, TypeScript-first, accessibility-correct component foundation (Radix UI via shadcn/ui) fully owned in-repo rather than dependency-locked; strong end-to-end typing symmetry with the backend's own strong-typing discipline ([ADR-0001](0001-backend-language-and-runtime.md), [ADR-0004](0004-data-validation-and-serialization.md)); and a data-table/virtualization stack (TanStack Table + Virtual) capable of handling the dense, large-dataset views Revenue Intelligence Platform and Timeline require.

**We give up:** the reduced initial setup time of a more prescriptive, batteries-included component library (Material UI/Ant Design) — accepted, since shadcn/ui's ownership model was judged more valuable for a product with a distinctive UI (per [17-future-recommendations.md](../17-future-recommendations.md)'s emphasis on differentiation) than a faster initial ramp with a harder-to-customize library later.

## Risks

Adopting many focused, best-of-breed libraries (rather than one framework's bundled equivalents) means more individual upgrade/compatibility surfaces to track — mitigated by all choices being widely-adopted, actively-maintained projects with strong TypeScript support, and by centralizing version management in `frontend/package.json` with routine dependency updates.

## Migration Strategy

shadcn/ui's copy-into-repo model means component code is already owned and does not require a "migration" away from a library dependency in the traditional sense. TanStack Query's server-state layer is isolated in `frontend/lib/`, so a future data-fetching library swap would touch that layer only.

## Consequences

- All frontend code is TypeScript; Zod schemas validate forms and, where relevant, API response shapes at the client boundary, mirroring the backend's Pydantic-first discipline.
- shadcn/ui components live in `frontend/components/`, fully owned and directly editable — not treated as an external dependency to avoid touching.
- Vitest and Playwright ([ADR-0023](0023-testing-strategy.md)) test this stack.
