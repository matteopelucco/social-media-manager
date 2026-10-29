import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Unisce nomi di classe CSS risolvendo i conflitti di Tailwind (vince l'ultimo). */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
