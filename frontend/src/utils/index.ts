import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export function formatRelativeTime(dateInput: string | Date | number): string {
  try {
    const date = new Date(dateInput);
    if (isNaN(date.getTime())) return 'unknown time';
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSec < 45) return 'just now';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    if (diffSec < 2592000) return `${Math.floor(diffSec / 86400)}d ago`;
    return date.toLocaleDateString();
  } catch {
    return 'recently';
  }
}
