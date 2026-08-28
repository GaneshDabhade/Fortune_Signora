/**
 * Behavioural tests for the shared component library.
 *
 * Focused on the properties a business page will depend on and would not
 * notice breaking: that a loading button cannot be double-submitted, that
 * an error is announced rather than merely coloured, that an empty state
 * always offers a next step.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import {
  Badge,
  Button,
  Dialog,
  EmptyState,
  Input,
  Select,
  SkeletonText,
} from '@/components/ui';

describe('Button', () => {
  it('cannot be clicked while loading', async () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Save
      </Button>,
    );

    await userEvent.click(screen.getByRole('button'));

    // The duplicate-submission bug: a spinner that looks busy but still
    // dispatches. Disabling is what actually prevents the second request.
    expect(onClick).not.toHaveBeenCalled();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('announces its busy state to assistive technology', () => {
    render(<Button loading>Save</Button>);

    // A spinning border conveys nothing to a screen reader.
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
  });

  it('lets a caller override its default styling', () => {
    render(<Button className="w-full">Save</Button>);

    // tailwind-merge must resolve conflicts in the caller's favour, or
    // every page needs a wrapper div to do what className should.
    expect(screen.getByRole('button').classList.contains('w-full')).toBe(true);
  });
});

describe('Input', () => {
  it('associates its label with the control', () => {
    render(<Input label="Workspace name" />);

    // getByLabelText only resolves if the association is real, so this
    // fails on a decorative label rather than a linked one.
    expect(screen.getByLabelText('Workspace name')).toBeInTheDocument();
  });

  it('announces an error rather than only colouring the field', () => {
    render(<Input label="Name" error="Name is required" />);

    expect(screen.getByRole('alert')).toHaveTextContent('Name is required');
    expect(screen.getByLabelText('Name')).toHaveAttribute('aria-invalid', 'true');
  });

  it('describes the field with its hint', () => {
    render(<Input label="Name" hint="Shown to your team" />);

    expect(screen.getByLabelText('Name')).toHaveAccessibleDescription(
      'Shown to your team',
    );
  });
});

describe('Select', () => {
  it('keeps its label available when visually hidden', () => {
    render(
      <Select
        label="Active workspace"
        labelHidden
        options={[{ value: 'a', label: 'Acme' }]}
      />,
    );

    expect(screen.getByLabelText('Active workspace')).toBeInTheDocument();
  });
});

describe('EmptyState', () => {
  it('always states what the user can do next', () => {
    render(
      <EmptyState title="No companies yet" description="Connect a CRM to get started." />,
    );

    // Both are required props; this asserts the description is actually
    // rendered, so "No data" alone cannot ship.
    expect(screen.getByText('No companies yet')).toBeInTheDocument();
    expect(screen.getByText('Connect a CRM to get started.')).toBeInTheDocument();
  });

  it('renders an action when one is supplied', () => {
    render(
      <EmptyState
        title="No workspaces"
        description="Create one to begin."
        action={<Button>New workspace</Button>}
      />,
    );

    expect(screen.getByRole('button', { name: 'New workspace' })).toBeInTheDocument();
  });
});

describe('Dialog', () => {
  it('is labelled by its title', () => {
    render(<Dialog open onClose={vi.fn()} title="New workspace" />);

    expect(screen.getByRole('dialog', { name: 'New workspace' })).toBeInTheDocument();
  });

  it('is absent from the accessibility tree when closed', () => {
    render(<Dialog open={false} onClose={vi.fn()} title="New workspace" />);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});

describe('Skeleton', () => {
  it('is hidden from assistive technology', () => {
    const { container } = render(<SkeletonText lines={3} />);

    // Twelve skeleton rows each announcing "loading" is worse than
    // silence; the container owns the single status message.
    const hidden = container.querySelectorAll('[aria-hidden="true"]');
    expect(hidden).toHaveLength(3);
  });
});

describe('Badge', () => {
  it('renders each tone without a hardcoded colour', () => {
    render(<Badge tone="success">Active</Badge>);

    expect(screen.getByText('Active').classList.contains('text-success')).toBe(true);
  });
});
