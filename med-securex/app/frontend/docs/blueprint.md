# **App Name**: MediSecureX2 Dashboard

## Core Features:

- User Authentication: Implement user authentication using Firebase Auth (Google Login).
- Role Management: Implement role-based access control: Admin, Analyst, Viewer.
- Dashboard UI: Display a dashboard with key metrics, charts, and tables for security monitoring.
- Navigation: Implement sidebar navigation for different dashboard panels.
- Alerts Panel: Create alerts panel with filtering and sorting capabilities.
- TTP Correlation: Use AI to correlate alerts based on `ttp_id` to known threats and MITRE ATT&CK techniques. LLM serves as a tool here, reasoning about when a `ttp_id` can be used for alert description or filtering.
- Settings Panel: Settings panel for user management, alert thresholds, and log retention.

## Style Guidelines:

- Primary color: HSL 210, 65%, 50% (RGB: #3399cc) for a professional and calming feel.
- Background color: HSL 210, 20%, 95% (RGB: #f0f5f7) to provide a clean, light interface.
- Accent color: HSL 180, 55%, 40% (RGB: #000) to highlight interactive elements and severity levels.
- Font: 'Inter' (sans-serif) for a modern and readable UI.
- Grid-based layout with rounded corners (2xl), soft shadows, and minimal clutter to ensure a clean and professional look.
- Smooth transitions with Framer Motion for enhanced UX.
- Use clear, consistent icons to represent data sources and alert types.