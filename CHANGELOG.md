# Changelog

All notable changes to the Hiring System Dashboard.

## [v1.3] - 2026-01-21

### Added
- Serial numbers column (S.No) for easy candidate reference
- Student indicator: Names show (S) suffix when Source = "student_application"
- Example: "Virendra" displays as "Virendra (S)" for student applicants

## [v1.2] - 2026-01-20

### Added
- AI Video Evaluation integration
- AI Eval score column with sorting
- AI Recommendation column (Strong Yes, Yes, Maybe, No)
- Doer probability percentage display
- Re-run evaluation button
- AI Report viewer link
- Transcript status indicator

### Changed
- Column layout updated to accommodate AI evaluation fields

## [v1.1] - 2026-01-19

### Added
- Clickable column header sorting (Level, Experience, AI Eval, AI Rec)
- Filter persistence using localStorage
- Auto-refresh with 15-minute countdown timer
- Clear filters button

### Fixed
- Column alignment for filter dropdowns

## [v1.0] - 2026-01-17

### Added
- Initial dashboard release
- Section 1: Overall application metrics
- Section 2: Video submission statistics
- Section 3: Candidate review table
- Filters: Name search, Level, MBA status, Stage status
- Video link viewer
- PDF resume viewer modal
- Full profile modal
- Stage 1 Status dropdown (Selected/Rejected)
- Reviewer Comments textarea with auto-save
- Collapsible sections
- Responsive design with Tailwind CSS
