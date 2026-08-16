import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/design/cn';

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('rounded-lg border border-border-soft bg-surface shadow-sm', className)}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  // 📁 **§05 `spacing` — *"Card padding — 20–24px, was 16px in v1."*** ⚠️ **The
  // horizontal value migrated to v2 and the vertical one did not**: this read
  // `px-5 py-4`, so 20px across and 16px down. TASK-1453.
  return <div className={cn('border-b border-border-soft p-5', className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2 className={cn('text-base font-semibold text-content', className)} {...props} />
  );
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  // 📁 The same 20px, for the same reason — see the header above.
  return <div className={cn('p-5', className)} {...props} />;
}
