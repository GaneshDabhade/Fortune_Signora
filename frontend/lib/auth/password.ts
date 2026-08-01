/**
 * Shortest password Signora accepts.
 *
 * **Its own module because both tiers of the UI need it and neither may reach
 * the other.** `lib/auth/server.ts` configures Better Auth with it and imports
 * `pg`, so a client component cannot import from there; the sign-up form
 * states the rule before a person breaks it. Typing the number twice would
 * make the stated rule and the enforced rule two facts that can disagree.
 *
 * Stated rather than inherited: Better Auth defaults to 8, and a number the
 * product never chose is a security posture nobody reviewed. **Length is the
 * only requirement** — composition rules push people toward `Passw0rd!`, which
 * is less entropy in a longer costume.
 */
export const MINIMUM_PASSWORD_LENGTH = 12;
