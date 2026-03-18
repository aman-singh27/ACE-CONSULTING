import { forwardRef } from 'react';
import type { ButtonHTMLAttributes } from 'react';
import { cn } from './Card';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg' | 'icon';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
        const variants = {
            primary: "bg-accent-primary text-white hover:bg-accent-primary/90 shadow-sm",
            secondary: "bg-bg-elevated text-text-primary hover:bg-bg-elevated/80 border border-border-default",
            outline: "bg-transparent border border-border-default text-text-primary hover:bg-bg-elevated",
            ghost: "bg-transparent text-text-secondary hover:bg-bg-elevated hover:text-text-primary",
            danger: "bg-red-500 text-white hover:bg-red-600 shadow-sm",
        };

        const sizes = {
            sm: "h-8 px-3 text-xs",
            md: "h-9 px-4 py-2",
            lg: "h-11 px-8 text-base",
            icon: "h-9 w-9",
        };

        return (
            <button
                ref={ref}
                className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-primary disabled:pointer-events-none disabled:opacity-50",
                    variants[variant],
                    sizes[size],
                    className
                )}
                {...props}
            />
        );
    }
);

Button.displayName = 'Button';
