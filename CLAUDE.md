# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of standalone HTML tool/calculator pages — no build system, no dependencies, no frameworks. Each file is a single self-contained `.html` file with inline CSS and vanilla JavaScript.

## Architecture

- **Single-file tools**: All HTML, CSS, and JS live in one `.html` file per tool. No external libraries, no module bundler.
- **No server required**: Files open directly in the browser (`file://`).
- **Vanilla JS only**: All interactivity is written in plain JavaScript with direct DOM manipulation.

## Design System

All tools follow this visual style — maintain consistency across files:

### Colors
| Role | Value |
|---|---|
| Page background | `#0f0f0f` |
| Card background | `#1a1a1a` |
| Input background | `#111` |
| Border (default) | `#2e2e2e` / `#2a2a2a` |
| Border (focus/active) | `#4ade80` |
| Text (primary) | `#e8e8e8` / `#ffffff` |
| Text (muted) | `#666` / `#888` |
| Accent (positive) | `#4ade80` (green) |
| Accent (negative/error) | `#f87171` (red) |
| Active button background | `#1e3a2a` |

### Typography
- Font: `'Segoe UI', sans-serif`
- Labels: `12px`, uppercase, `letter-spacing: 0.05em`, color `#888`
- Body/inputs: `15px`
- Result values: `48px`, `font-weight: 700`

### Component Patterns
- **Card**: `border-radius: 16px`, `padding: 40px`, `max-width: 480px`, centered on page
- **Inputs**: `border-radius: 10px`, `padding: 12px`, with absolute-positioned `$` prefix or `%` suffix spans
- **Toggle buttons**: Two-button row (`$ Fixed` / `% of Price`), active state uses green accent
- **Result block**: Centered, `border-radius: 12px`, large colored value + subtitle line
- **Breakdown rows**: `display: flex; justify-content: space-between`, muted left label, lighter right value

## Language Note

Labels in the UI may appear in Latvian (e.g. "Produkta cena", "Nodokļi"). This is intentional — the user translates field labels to Latvian while keeping result/formula text in English.
