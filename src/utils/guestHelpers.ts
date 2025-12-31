/**
 * Get initials from a guest's full name
 * For "John Doe" returns "JD", for "Alice" returns "AL"
 */
export function getGuestInitials(name: string): string {
  if (!name || name.trim().length === 0) return '??'

  const nameParts = name.trim().split(/\s+/)
  return nameParts.length >= 2
    ? `${nameParts[0].charAt(0)}${nameParts[nameParts.length - 1].charAt(0)}`.toUpperCase()
    : name.substring(0, 2).toUpperCase()
}
