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
                "rounded-[10px] border border-border-subtle bg-bg-surface text-text-primary",
                className
            )}
            {...props}
        />
    )
);
Card.displayName = 'Card';

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className, ...props }, ref) => (
        <div ref={ref} className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />
    )
);
CardHeader.displayName = "CardHeader";

export const CardTitle = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLHeadingElement>>(
    ({ className, ...props }, ref) => (
        <h3 ref={ref} className={cn("font-semibold leading-none tracking-tight", className)} {...props} />
    )
);
CardTitle.displayName = "CardTitle";

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className, ...props }, ref) => (
        <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
    )
);
CardContent.displayName = "CardContent";

