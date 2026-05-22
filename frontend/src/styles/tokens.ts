// Design tokens — Jollof Intelligence Frontend
// Nigerian cultural identity colour palette

export const colors = {
  primary: '#008751',       // Nigerian flag green
  background: '#FFFFFF',    // white
  accent: '#E87722',        // warm orange (Jollof rice)
  accentAlt: '#CC0000',     // deep red (secondary accent)
  textPrimary: '#1A1A1A',   // near-black for body text
  textSecondary: '#555555', // muted text
  surface: '#F9F5F0',       // warm off-white card background
  border: '#D4C5B0',        // warm border
  error: '#CC0000',
  success: '#008751',
  focusRing: '#E87722',     // 3:1+ contrast on white
  headerBg: '#006B40',      // darker green for header
  tabActive: '#008751',
  tabInactive: '#555555',
  starFilled: '#E87722',
  starEmpty: '#D4C5B0',
  coldStartBg: '#FFF3E0',
  coldStartBorder: '#E87722',
  coldStartText: '#7A3B00',
  errorBg: '#FFF0F0',
  errorBorder: '#CC0000',
  conversationUserBg: '#E8F5E9',
  conversationAssistantBg: '#F9F5F0',
} as const;

export const breakpoints = {
  mobile: 768,
  tablet: 1024,
} as const;

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
} as const;

export const fontSizes = {
  sm: '0.875rem',
  base: '1rem',
  lg: '1.125rem',
  xl: '1.25rem',
  xxl: '1.5rem',
  xxxl: '2rem',
} as const;

export const borderRadius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
  full: '9999px',
} as const;
