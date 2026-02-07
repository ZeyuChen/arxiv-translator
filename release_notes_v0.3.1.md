# release_notes_v0.3.1

## Changes

- **Performance**:
    - Increased concurrent translation workers from 8 to **12** for faster processing.
    - Set **Gemini 3.0 Flash** as the default model (deprecated Pro in CLI).
    - Optimized progress reporting for better frontend integration.

- **Bug Fixes**:
    - Fixed a critical compilation conflict with `\chinese` command by globally renaming user-defined macros.
    - Added auto-fix for `minted` package (`outputdir=.`).
    - Added auto-fix for duplicate LaTeX labels.
    - Fixed `\ }` escape sequence errors.

- **Features**:
    - Enhanced strict progress output format `PROGRESS:TRANSLATING:IDX:TOTAL:FILENAME`.
