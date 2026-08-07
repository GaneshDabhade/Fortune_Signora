/**
 * The shared component library's public surface.
 *
 * Business pages import from here and nowhere deeper. A page reaching into
 * `components/ui/button` directly is the first step toward a page-local
 * variant, and the second is a design system nobody uses (AC-15).
 */
export { Button, type ButtonProps, type ButtonSize, type ButtonVariant } from './button';
export { Input, type InputProps } from './input';
export { Select, type SelectOption, type SelectProps } from './select';
export { Badge, type BadgeProps, type BadgeTone } from './badge';
export { Confidence, type ConfidenceProps } from './confidence';
export { Card, CardBody, CardHeader, CardTitle } from './card';
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
export { Skeleton, SkeletonText, type SkeletonTextProps } from './skeleton';
export { Table, TBody, TD, TH, THead, TR } from './table';
