# Frontend UI Migration: Glassmorphism → Element Plus X

**Date:** 2026-06-14
**Status:** Approved
**Scope:** Replace custom glassmorphism styles with Element Plus X component library + light/dark theme system

## Goal

Remove the custom frosted-glass CSS theme (hard-to-tune foreground/background color proximity) and adopt Element Plus X's design system with one-click light/dark theme switching.

## Constraints

- Preserve three-column layout (left sidebar + center chat + right panel)
- Preserve all existing functionality (WebSocket chat, stores, routing)
- Backend API remains unchanged
- Default theme: light
- User preference persisted in localStorage

## Architecture

```
App.vue
└── <ConfigProvider :theme="theme">       // EPX global theme
    ├── AppHeader                         // keep structure, add theme toggle
    ├── LeftSidebar
    │   └── <Conversations>              // EPX: replaces custom session list
    ├── ChatMain
    │   ├── <Welcome>                    // EPX: empty state
    │   ├── <BubbleList>                 // EPX: replaces v-for message loop
    │   │   ├── <Bubble role="user">
    │   │   ├── <Bubble role="ai">
    │   │   │   └── <Typewriter>         // EPX: streaming text
    │   │   └── <Thinking>               // EPX: AI processing state
    │   └── <XSender>                    // EPX: replaces ChatInput
    └── RightSidebar                     // keep, restyle with EP components
```

## Component Mapping

| Current | Replacement | Package |
|---------|------------|---------|
| `ChatBubble.vue` | `<Bubble>` | vue-element-plus-x |
| Message list (v-for) | `<BubbleList>` | vue-element-plus-x |
| `ChatInput.vue` | `<XSender>` | vue-element-plus-x |
| LeftSidebar session list | `<Conversations>` | vue-element-plus-x |
| Loading spinner | `<Thinking>` | vue-element-plus-x |
| Empty new-chat state | `<Welcome>` | vue-element-plus-x |
| Streaming markdown | `<Typewriter>` | vue-element-plus-x |

## Theme System

### Implementation

1. **Root wrapper:** `<ConfigProvider :theme="isDark ? 'dark' : 'light'">`
2. **State management:** `useDark()` from `@vueuse/core` (already installed)
3. **Toggle UI:** Sun/Moon icon button in AppHeader (right side)
4. **Persistence:** localStorage (handled by useDark automatically)
5. **CSS variables:** `--elx-*` tokens from Element Plus X (no custom --lc-* needed)

### Token Usage

- Background: `var(--elx-bg-page)`, `var(--elx-bg-surface)`
- Text: `var(--elx-text-color-primary)`, `var(--elx-text-color-secondary)`
- Border: `var(--elx-border-color)`
- Accent: `var(--elx-color-primary)` (default #409eff)
- Shadows: `var(--elx-box-shadow)`

## Removals

1. **style.css:** All `--lc-*` CSS variables (glass, gradient, palette)
2. **Components:** All `backdrop-filter`, `-webkit-backdrop-filter` rules
3. **Components:** All hardcoded GitHub-dark hex colors (#0d1117, #161b22, #21262d, #30363d, etc.)
4. **index.html:** Remove hardcoded `class="dark"` from `<html>`
5. **main.ts:** Remove `element-plus/theme-chalk/dark/css-vars.css` import (EPX handles it)
6. **Global overrides:** Remove `.el-dialog`, `.el-input__wrapper` style hacks in style.css

## Preserves

- Three-column flex layout
- Vue Router (`createWebHashHistory`, route params)
- Pinia stores (agents, sessions, chat)
- WebSocket communication layer
- Right sidebar tool/settings panel (restyled with EP native components)
- Backend API contracts

## Dependencies

### Add
- `vue-element-plus-x` (latest v2)

### Keep
- `element-plus` (required by EPX)
- `@vueuse/core` (for useDark)
- `pinia`, `vue-router`, `highlight.js`, `markdown-it`

### Potentially Remove
- `highlight.js` + `markdown-it` (if EPX Bubble handles markdown/code natively)

## Migration Order

1. Install `vue-element-plus-x`, configure `ConfigProvider` in App.vue
2. Implement theme toggle (useDark + header button)
3. Replace `style.css` tokens with EPX tokens
4. Migrate LeftSidebar → `<Conversations>`
5. Migrate ChatBubble → `<Bubble>` / `<BubbleList>`
6. Migrate ChatInput → `<XSender>`
7. Add `<Welcome>` for empty state
8. Add `<Thinking>` for loading state
9. Add `<Typewriter>` for streaming
10. Clean up: remove dead CSS, unused imports, old components
11. Test both themes end-to-end

## Risks

- EPX component API may not cover all current custom behaviors (e.g., token usage panel in ChatBubble)
- WebSocket streaming integration with `<BubbleList>` needs investigation
- Right sidebar has no EPX equivalent — must restyle manually with EP base components
