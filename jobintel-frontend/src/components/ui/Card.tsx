import { clsx, type ClassValue } from 'clsx';
import { forwardRef } from 'react';
import type { HTMLAttributes } from 'react';

// Simplified tailwind merge for now, using just clsx
export function cn(...inputs: ClassValue[]) {
    return clsx(inputs);
}

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className, ...props }, ref) => (
        <div
            ref={ref}
            className={cn(
                "rounded-[10px] border border-border-subtle bg-bg-surface p-4 text-text-primary",
                className
            )}
            {...props}
        />
    )
);
Card.displayName = 'Card';
