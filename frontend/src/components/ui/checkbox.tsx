import * as React from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export function Checkbox({ checked, onCheckedChange, className, ...props }: Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "onChange"> & { checked: boolean; onCheckedChange: (checked: boolean) => void }) {
  return <button type="button" role="checkbox" aria-checked={checked} onClick={() => onCheckedChange(!checked)} className={cn("flex size-5 items-center justify-center rounded border transition-colors", checked ? "border-primary bg-primary text-primary-foreground" : "border-input bg-background hover:border-primary/60", className)} {...props}>{checked && <Check className="size-3.5" strokeWidth={3} />}</button>;
}
