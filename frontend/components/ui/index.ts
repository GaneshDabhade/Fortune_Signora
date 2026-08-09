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
export { CopyableId } from './copyable-id';
export { Skeleton, SkeletonText, type SkeletonTextProps } from './skeleton';
export { Table, TBody, TD, TH, THead, TR } from './table';
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
