/**
 * Onboarding API operations — [TASK-469](../../../docs/BACKLOG.md), Workflow 8.
 *
 * ⚡ **Every call returns the whole run**, and that is the design's autosave
 * made checkable: *"every step saves on advance and on blur."* A screen that
 * held its own copy of the answers would have two representations of one
 * fact, and the one on the screen is the one that would be wrong after a
 * network drop.
 */

import { apiRequest } from '@/lib/api/client';

/** Where a value came from. **Never absent** — a value without it cannot be
 * rendered honestly, because the *Inferred* badge would be either missing or
 * wrong. */
export type Provenance = 'inferred' | 'confirmed' | 'entered';

export type OnboardingStep = 'welcome' | 'workspace' | 'company' | 'you' | 'goals' | 'connect';

export type Goal =
  | 'forecast_accurately'
  | 'stop_deals_slipping'
  | 'protect_renewals'
  | 'coach_the_team'
  | 'find_new_pipeline'
  | 'prove_marketing_impact';

export interface Answer {
  value: string;
  provenance: Provenance;
}

export interface OnboardingRun {
  workspace_id: string;
  current_step: OnboardingStep;
  completed_steps: OnboardingStep[];
  industry: Answer | null;
  company_size: Answer | null;
  region: Answer | null;
  timezone: Answer | null;
  role: Answer | null;
  team_size: Answer | null;
  goals: Goal[];
  /** ⛔ **Derived server-side from the goals and stored nowhere.** The client
   * displays it and never computes it — a second copy of the mapping here is
   * exactly the disagreement §2 forbids. */
  features: string[];
  started_at: string;
  finished_at: string | null;
  /** ⚡ What the resume banner reads. *Left* is not *finished*. */
  skipped_at: string | null;
}

/**
 * Begin, or resume what is already in progress.
 *
 * ⛔ **Idempotent, and the server answers `200` rather than `201` to say so.**
 * The person most likely to call this twice arrived from the resume banner.
 */
export async function startOnboarding(workspaceId: string): Promise<OnboardingRun> {
  return apiRequest<OnboardingRun>(`/workspaces/${workspaceId}/onboarding`, {
    method: 'POST',
    workspaceId,
  });
}

export async function getOnboarding(workspaceId: string): Promise<OnboardingRun> {
  return apiRequest<OnboardingRun>(`/workspaces/${workspaceId}/onboarding`, { workspaceId });
}

export async function advanceOnboarding(
  workspaceId: string,
  step: OnboardingStep,
): Promise<OnboardingRun> {
  return apiRequest<OnboardingRun>(`/workspaces/${workspaceId}/onboarding/step`, {
    method: 'POST',
    body: { step },
    workspaceId,
  });
}

/**
 * Screen `04`. **Omitting a field leaves it alone** — a `PATCH`, because
 * *"four confirmations, no typing"* means somebody may answer one and leave
 * three, and a whole-object write would clear what the request did not repeat.
 */
export async function confirmCompany(
  workspaceId: string,
  body: {
    industry?: Answer;
    company_size?: Answer;
    region?: Answer;
    timezone?: Answer;
  },
): Promise<OnboardingRun> {
  return apiRequest<OnboardingRun>(`/workspaces/${workspaceId}/onboarding/company`, {
    method: 'PATCH',
    body,
    workspaceId,
  });
}

export async function describePerson(
  workspaceId: string,
  body: { role?: Answer; team_size?: Answer },
): Promise<OnboardingRun> {
  return apiRequest<OnboardingRun>(`/workspaces/${workspaceId}/onboarding/person`, {
    method: 'PATCH',
    body,
    workspaceId,
  });
}

/**
 * Screen `06`. ⚡ **A `PUT`, deliberately unlike the two above**: the goals
 * are one selection rather than independent fields, and deselecting sends the
 * remaining two. **An empty list is valid** — skipping entirely is permitted.
 */
export async function chooseGoals(workspaceId: string, goals: Goal[]): Promise<OnboardingRun> {
  return apiRequest<OnboardingRun>(`/workspaces/${workspaceId}/onboarding/goals`, {
    method: 'PUT',
    body: { goals },
    workspaceId,
  });
}

export async function finishOnboarding(workspaceId: string): Promise<OnboardingRun> {
  return apiRequest<OnboardingRun>(`/workspaces/${workspaceId}/onboarding/completion`, {
    method: 'POST',
    workspaceId,
  });
}

/** ⛔ **Its own resource, because leaving is not finishing.** The two states
 * have to be distinguishable or the resume banner cannot decide to appear. */
export async function skipOnboarding(workspaceId: string): Promise<OnboardingRun> {
  return apiRequest<OnboardingRun>(`/workspaces/${workspaceId}/onboarding/skip`, {
    method: 'POST',
    workspaceId,
  });
}
