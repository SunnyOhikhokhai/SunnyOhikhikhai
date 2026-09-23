import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset [&_svg]:size-3",
  {
    variants: {
      variant: {
        default: "bg-navy-50 text-navy-700 ring-navy-600/15",
        green: "bg-green-50 text-green-700 ring-green-600/25",
        solid: "bg-green-600 text-white ring-transparent",
        navy: "bg-navy text-white ring-transparent",
        outline: "bg-white text-slate-700 ring-border",
        demo: "bg-amber-50 text-amber-800 ring-amber-600/30",
        danger: "bg-red-50 text-red-700 ring-red-600/20",
        glass: "bg-white/15 text-white ring-white/25 backdrop-blur",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
