# Pages

Customer-facing page modules live here. `main.jsx` is the application controller
(state, API orchestration and routing) while page-specific presentation should be
kept out of it. New Dashboard, Scans, Targets, Settings and Finding UI work must
be added to the matching page module instead of growing `main.jsx`.
