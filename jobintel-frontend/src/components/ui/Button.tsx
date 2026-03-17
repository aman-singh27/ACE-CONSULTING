import { forwardRef } from 'react';
import type { ButtonHTMLAttributes } from 'react';
import { cn } from './Card';

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement>>(
    ({ className, ...props }, ref) => {
        return (
            <button
                ref={ref}
                className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-primary disabled:pointer-events-none disabled:opacity-50",
                    "bg-accent-primary text-white hover:bg-accent-primary/90 h-9 px-4 py-2",
                    className
                )}
                {...props}
            />
        );
    }
);
Button.displayName = 'Button';
