# Veya UI system

Veya — Care, closer.

Veya is the working public-facing name. It suggests a way forward without tying the product to nutrition alone. Veya Guide names the care-navigation feature. Name, domain, and trademark availability have not been evaluated. Internal API identifiers, cookies, and database names remain unchanged to preserve existing accounts.

## Design direction

Warm ivory surfaces, forest green actions, botanical lime accents, and quiet lavender and peach service cards. Manrope is the interface typeface; an occasional serif italic adds warmth to editorial headings. The four-petal care illustration is CSS-native, with no image download or animation dependency.

Core tokens: background #f8f9f5, surface #fffefa, primary #245e4b, primary hover #174634, text #243c33, muted #69766e, border #e4e9df. Red is reserved for urgent help and error feedback.

## Navigation and hierarchy

The desktop shell groups personal navigation and care tools. At mobile widths, five primary destinations remain available in a bottom bar. Emergency help is always reachable from the shell. Authentication uses a focused standalone layout.

The home page prioritizes finding care, followed by service discovery and a guided next step. Its side panel shows an upcoming appointment from the API, a signed-out prompt, an empty state, or an unavailable state. It never invents activity counts.

Doctor search uses visible input labels, preserves location and budget when changing specialty, and provides clear reset, empty, and unavailable states. Veya Guide routes users to existing services; it does not simulate an AI search or diagnosis.

## Interaction and accessibility

Use 180–200ms transitions for buttons and cards. Home sections enter once with a short, restrained stagger. No looping decorative animation. Respect prefers-reduced-motion across animations and transitions.

Provide visible keyboard focus, a skip link, semantic navigation labels, current-page state, and named search controls. Primary controls target 44px or greater. Keep mobile content above the safe-area-aware bottom navigation.

## Scope and verification

This redesign covers the shared visual system and shell, home, doctor search, account-entry styling, and navigation guide. Other routes inherit typography, buttons, card styling, and brand naming. Existing demonstration content remains identified as such. Booking, authentication, API contracts, and backend identifiers are retained.
