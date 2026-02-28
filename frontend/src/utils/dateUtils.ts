/**
 * Formats a date string into a readable month/day, hour:minute:second AM/PM format
 * Example: "7/29 12:31:09 PM"
 *
 * @param dateString - ISO date string or any valid Date input
 * @returns Formatted date-time string
 */
function toUTCDate(dateString: string | Date): Date {
  if (typeof dateString === 'string' && !dateString.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(dateString)) {
    return new Date(dateString + 'Z');
  }
  return new Date(dateString);
}

export function formatDateTime(dateString: string | Date): string {
  const date = toUTCDate(dateString);
  return date.toLocaleString('en-US', {
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    second: 'numeric',
    hour12: true
  });
}

/**
 * Formats a date string into a readable month/day format
 * Example: "7/29"
 *
 * @param dateString - ISO date string or any valid Date input
 * @returns Formatted date string
 */
export function formatDate(dateString: string | Date): string {
  const date = toUTCDate(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'numeric',
    day: 'numeric'
  });
}