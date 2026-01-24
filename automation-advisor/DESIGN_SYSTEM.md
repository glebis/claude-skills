# Automation Advisor Design System

## Design Philosophy

**Core Principles**:
- **Clarity over cleverness**: Information should be immediately comprehensible
- **Guided autonomy**: Users feel supported but in control
- **Progressive disclosure**: Show complexity only when needed
- **Professional warmth**: Authoritative without being cold

**Target Audience**: Knowledge workers evaluating automation opportunities
**Primary Use Case**: Decision-making tool, not entertainment

---

## Color System

### Primary Palette
```css
--primary-blue: #3B82F6;      /* Primary actions, links */
--primary-blue-dark: #2563EB; /* Hover states */
--primary-purple: #8B5CF6;    /* Secondary actions, accents */
--primary-purple-dark: #7C3AED;

--success-green: #10B981;
--warning-amber: #F59E0B;
--error-red: #EF4444;
```

### Neutral Palette
```css
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-300: #D1D5DB;
--gray-400: #9CA3AF;
--gray-500: #6B7280;
--gray-600: #4B5563;
--gray-700: #374151;
--gray-800: #1F2937;
--gray-900: #111827;
```

### Semantic Colors
```css
--bg-primary: #0F172A;        /* Main background */
--bg-secondary: #1E293B;      /* Card backgrounds */
--bg-tertiary: #334155;       /* Elevated elements */

--text-primary: #F1F5F9;      /* Main text */
--text-secondary: #CBD5E1;    /* Secondary text */
--text-tertiary: #94A3B8;     /* Muted text */

--border-primary: #334155;    /* Default borders */
--border-accent: #3B82F6;     /* Focus/active borders */
```

---

## Typography

### Font Stack
```css
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
--font-mono: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace;
```

### Type Scale
```css
--text-xs: 0.75rem;    /* 12px - labels, hints */
--text-sm: 0.875rem;   /* 14px - body, buttons */
--text-base: 1rem;     /* 16px - body */
--text-lg: 1.125rem;   /* 18px - emphasized text */
--text-xl: 1.25rem;    /* 20px - section titles */
--text-2xl: 1.5rem;    /* 24px - card titles */
--text-3xl: 1.875rem;  /* 30px - page titles */
--text-4xl: 2.25rem;   /* 36px - hero text */
```

### Font Weights
```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Line Heights
```css
--leading-tight: 1.25;
--leading-snug: 1.375;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
```

---

## Spacing System

### Scale (based on 4px grid)
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

---

## Border Radius

```css
--radius-sm: 0.375rem;  /* 6px - small elements */
--radius-md: 0.5rem;    /* 8px - buttons, inputs */
--radius-lg: 0.75rem;   /* 12px - cards */
--radius-xl: 1rem;      /* 16px - large cards */
--radius-full: 9999px;  /* Pills, badges */
```

---

## Shadows

```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
```

---

## Component Patterns

### Buttons

**Primary Button**:
```css
background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
color: white;
padding: var(--space-3) var(--space-6);
border-radius: var(--radius-md);
font-weight: var(--font-semibold);
transition: all 150ms ease;
```

**Secondary Button**:
```css
background: var(--bg-tertiary);
color: var(--text-primary);
border: 1px solid var(--border-primary);
```

**Ghost Button**:
```css
background: transparent;
color: var(--primary-blue);
border: 1px solid var(--primary-blue);
```

### Cards

**Default Card**:
```css
background: var(--bg-secondary);
border: 1px solid var(--border-primary);
border-radius: var(--radius-lg);
padding: var(--space-6);
box-shadow: var(--shadow-md);
```

**Elevated Card**:
```css
background: var(--bg-tertiary);
border: 1px solid var(--border-accent);
box-shadow: var(--shadow-lg);
```

### Inputs

**Text Input/Textarea**:
```css
background: var(--bg-tertiary);
border: 1px solid var(--border-primary);
color: var(--text-primary);
padding: var(--space-3) var(--space-4);
border-radius: var(--radius-md);
font-size: var(--text-sm);
transition: all 150ms ease;

/* Focus state */
border-color: var(--primary-blue);
box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
```

### Progress Indicators

**Progress Bar**:
```css
height: 4px;
background: var(--bg-tertiary);
border-radius: var(--radius-full);

/* Fill */
background: linear-gradient(90deg, var(--primary-blue), var(--primary-purple));
transition: width 300ms ease;
```

---

## Animation & Transitions

### Timing Functions
```css
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### Durations
```css
--duration-fast: 150ms;
--duration-normal: 300ms;
--duration-slow: 500ms;
```

### Common Transitions
```css
transition: all var(--duration-fast) var(--ease-out);
```

---

## Layout Patterns

### Container Max-Width
```css
--container-sm: 640px;
--container-md: 768px;
--container-lg: 1024px;
--container-xl: 1280px;
```

### Split Layout (Question + Conversation)
- Question panel: 40% width
- Conversation panel: 60% width
- Gap: var(--space-6)

---

## Accessibility Standards

### Focus Visible
```css
outline: 2px solid var(--primary-blue);
outline-offset: 2px;
```

### Minimum Contrast Ratios
- Text on background: 4.5:1 (AA)
- Large text: 3:1 (AA)
- Interactive elements: 3:1 (AA)

### Touch Targets
- Minimum: 44x44px
- Preferred: 48x48px

---

## Responsive Breakpoints

```css
--breakpoint-sm: 640px;   /* Mobile landscape */
--breakpoint-md: 768px;   /* Tablet */
--breakpoint-lg: 1024px;  /* Desktop */
--breakpoint-xl: 1280px;  /* Large desktop */
```

---

## Icon System

**Emoji-based** (no icon library dependency):
- 🤖 Robot - AI/automation
- 📊 Chart - analysis/data
- ⚡ Lightning - speed/efficiency
- ⚠️ Warning - alerts
- ✅ Checkmark - success
- ❌ X - error/close
- 🎤 Microphone - voice
- 💬 Speech - conversation

---

## Motion Patterns

### Fade In
```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
animation: fadeIn 300ms ease-out;
```

### Pulse (for recording)
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
```

### Skeleton Loading
```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
background: linear-gradient(90deg,
  var(--bg-secondary) 25%,
  var(--bg-tertiary) 50%,
  var(--bg-secondary) 75%
);
background-size: 200% 100%;
animation: shimmer 1.5s infinite;
```

---

## Error States

### Error Message Pattern
```html
<div class="error-banner">
  <div class="error-icon">⚠️</div>
  <div class="error-content">
    <div class="error-title">Error</div>
    <div class="error-message">Descriptive message</div>
  </div>
  <button class="error-retry">Retry</button>
</div>
```

### Styles
```css
.error-banner {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--error-red);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}
```

---

## Loading States

### Loading Indicator (dots)
```html
<span class="loading-dots">
  <span>●</span><span>●</span><span>●</span>
</span>
```

```css
.loading-dots span {
  animation: pulse 1.4s infinite;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }
```

---

## Best Practices

### Do's
✅ Use design tokens, never hard-coded values
✅ Maintain consistent spacing (4px grid)
✅ Apply hover/focus states to all interactive elements
✅ Test at 200% zoom
✅ Ensure 4.5:1 contrast for text
✅ Add loading states for async operations
✅ Provide clear error messages with recovery actions

### Don'ts
❌ Create one-off color values
❌ Mix spacing systems
❌ Skip accessibility attributes
❌ Use generic error messages ("Error occurred")
❌ Forget reduced motion preferences
❌ Hard-code dimensions that should be responsive
❌ Leave interactive elements without focus states
