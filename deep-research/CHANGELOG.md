# Deep Research Skill - Changelog

## Version 2.0 - Token-Optimized with Automatic Markdown Saving

### New Features

#### Automatic Markdown Saving
- Research reports are now automatically saved to timestamped markdown files
- Default filename: `research_report_YYYYMMDD_HHMMSS.md`
- Includes complete report, sources, and metadata footer
- No manual intervention needed

#### Token-Efficient Long-Running Task Handling
- Optimized for 10-20 minute deep research queries
- Synchronous execution (blocking subprocess, no polling)
- No intermediate status checks during wait
- **Token savings**: ~19,000 tokens per research query vs. polling approach

#### New Command-Line Options
```bash
--output-file <path>      # Custom output file path
--no-save                 # Disable automatic markdown saving
```

### Improvements

#### deep_research.py Updates
- Added automatic file saving with timestamped filenames
- Enhanced markdown formatting with metadata footer
- Added datetime import for timestamp generation
- Success confirmation message with absolute file path

#### run_deep_research.py Updates
- Better progress messages with estimated time (10-20 minutes)
- Timeout display in both seconds and minutes
- Completion confirmation message
- Improved error handling

#### SKILL.md Updates
- Added "Token-Efficient Workflow" section explaining optimization
- Documented automatic markdown saving feature
- Added token savings calculations (~20K tokens saved)
- Updated all usage examples
- Enhanced troubleshooting section

### Technical Details

**Token Optimization Strategy:**
- Traditional approach: 40 status checks × 500 tokens = 20,000 tokens
- Optimized approach: Single wait = ~1,000 tokens
- **Savings**: ~95% reduction in token usage during wait

**File Generation:**
- `research_prompt_YYYYMMDD_HHMMSS.txt` - Enhanced prompt with parameters
- `research_report_YYYYMMDD_HHMMSS.md` - Complete markdown report

### Usage Example

```bash
# Basic usage (auto-saves to research_report_20251025_150402.md)
python3 scripts/run_deep_research.py "Art as sense-making"

# Custom output location
python3 assets/deep_research.py --prompt-file prompt.txt --output-file my_research.md

# No automatic saving (terminal only)
python3 assets/deep_research.py --prompt-file prompt.txt --no-save
```

### Breaking Changes
None - all changes are backward compatible. The skill maintains full compatibility with existing workflows.

### Files Modified
- `assets/deep_research.py` - Added automatic markdown saving
- `scripts/run_deep_research.py` - Enhanced progress messages
- `SKILL.md` - Comprehensive documentation updates

---

*Released: October 25, 2025*
