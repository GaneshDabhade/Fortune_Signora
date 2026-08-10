/**
 * The shared component library's public surface.
 *
 * Business pages import from here and nowhere deeper. A page reaching into
 * `components/ui/button` directly is the first step toward a page-local
 * variant, and the second is a design system nobody uses (AC-15).
 */
export { Button, type ButtonProps, type ButtonSize, type ButtonVariant } from './button';
export { Input, type InputProps } from './input';
export { PasswordField, type PasswordFieldProps } from './password-field';
export { PasswordStrength, evaluatePassword, type PasswordRule } from './password-strength';
export {
  useResendTimer,
  formatRemaining,
  ATTEMPTS_BEFORE_FILTER_HINT,
  FIRST_RESEND_DELAY_SECONDS,
  type ResendTimer,
} from './resend-timer';
export { Select, type SelectOption, type SelectProps } from './select';
export { Badge, type BadgeProps, type BadgeTone } from './badge';
export { Confidence, type ConfidenceProps } from './confidence';
export { Card, CardBody, CardHeader, CardTitle } from './card';
export { LockedField, type LockedFieldProps } from './locked';
export { Dialog, type DialogProps } from './dialog';
export { Drawer, type DrawerProps } from './drawer';
export {
  CommandPalette,
  KEY_MAP,
  type CommandItem,
  type CommandPaletteProps,
} from './command-palette';
export { EmptyState, type EmptyStateProps } from './empty-state';
export { ErrorState, type ErrorStateProps } from './error-state';
export { SystemState, type SystemStateProps } from './system-state';
export { Breadcrumb } from './breadcrumb';
export { Tabs, type TabsProps, type TabItem } from './tabs';
export { Avatar, initialsFor, type AvatarProps, type AvatarSize } from './avatar';
export { Tooltip, TOOLTIP_DELAY_MS, type TooltipProps } from './tooltip';
export {
  PageHeader,
  RecordHeader,
  type PageHeaderProps,
  type RecordHeaderProps,
  type RecordFact,
} from './page-header';
export { ShellBanners, type ShellBanner } from './shell-banners';
export { CopyableId } from './copyable-id';
export { CodeInput, type CodeInputProps } from './code-input';
export { OfflineStatus } from './offline-status';
// ⛔ **`AuthModeIndicator` is deliberately NOT re-exported here.** It is a
// SERVER component — it calls `authMode()`, which reads `SIGNORA_ENVIRONMENT`,
// a variable that is not `NEXT_PUBLIC_` and must not become one
// ([TASK-473](../../../docs/BACKLOG.md)). ⚠️ **This barrel is imported by client
// components** — `app-shell.tsx` among them — **so a re-export would pull the
// authentication configuration module into every client bundle**, where the
// variable is absent and the badge would silently read `development` in every
// environment. ✅ **It still lives in `components/ui` because it is a library
// component and not a page-local variant** (§20c); callers import the file.
export { RegionBoundary, MAX_ATTEMPTS } from './region-boundary';
export { Skeleton, SkeletonText, type SkeletonTextProps } from './skeleton';
export {
  Table,
  TBody,
  TD,
  TH,
  THead,
  TR,
  EditableCell,
  type TableProps,
  type TRProps,
  type CellProps,
  type EditableCellProps,
} from './table';
export { StepRail, type RailStep, type StepRailProps } from './step-rail';
export {
  ChoiceCards,
  MultiChoiceCards,
  type Choice,
  type ChoiceCardsProps,
  type MultiChoiceCardsProps,
} from './choice-cards';
export { Inferred, type InferredProps } from './inferred';
export { FieldOriginTag, type FieldOrigin, type FieldOriginTagProps } from './field-origin';
export {
  SegmentedControl,
  type Segment,
  type SegmentedControlProps,
} from './segmented-control';
