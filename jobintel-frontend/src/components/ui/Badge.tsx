import { forwardRef } from 'react';
import type { HTMLAttributes } from 'react';
import { cn } from './Card';

interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
    variant?: 'spiking' | 'struggling' | 'new' | 'default';
}

export const Badge = forwardRef<HTMLDivElement, BadgeProps>(
    ({ className, variant = 'default', ...props }, ref) => {

        // Simple color variants based on PRD requirements
        const variantStyles = {
            default: 'bg-bg-elevated text-text-secondary border-border-default',
            spiking: 'bg-green-500/10 text-green-400 border-green-500/20',
            struggling: 'bg-red-500/10 text-red-400 border-red-500/20',
            new: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
        };

        return (
            <div
                ref={ref}
                className={cn(
                    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none",
                    variantStyles[variant],
                    className
                )}
                {...props}
            />
        );
    }
);
Badge.displayName = 'Badge';
