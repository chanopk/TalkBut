# Design Document: Release v0.2.0

## Overview

This design document outlines the technical approach for releasing TalkBut version 0.2.0. The release process is implemented as a Python script that automates version updates, changelog management, test execution, and Git tagging. The design focuses on reliability, idempotency, and clear error reporting to ensure a smooth release process.

The release automation will be implemented as a standalone script that can be executed manually or integrated into CI/CD pipelines. It will perform all necessary checks and updates in a specific order to maintain consistency and allow for rollback if issues are detected.

## Architecture

The release system follows a linear pipeline architecture with validation checkpoints:

```
┌─────────────────┐
│ Pre-flight      │
│ Checks          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Run Tests       │
│ (Unit + PBT)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Version  │
│ Files           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update          │
│ Changelog       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Commit Changes  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create Git Tag  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Display         │
│ Instructions    │
└─────────────────┘
```

Each stage validates its preconditions and can halt the process if errors are detected. The design ensures that partial releases cannot occur - either all steps complete successfully or the process stops with clear error messages.

## Components and Interfaces

### 1. ReleaseManager

The main orchestrator that coordinates the entire release process.

```python
class ReleaseManager:
    def __init__(self, new_version: str, dry_run: bool = False):
        """
        Initialize the release manager.
        
        Args:
            new_version: Target version (e.g., "0.2.0")
            dry_run: If True, show what would be done without making changes
        """
        
    def execute_release(self) -> bool:
        """
        Execute the complete release process.
        
        Returns:
            True if release completed successfully, False otherwise
        """
```

### 2. VersionUpdater

Handles updating version numbers in configuration files.

```python
class VersionUpdater:
    def update_package_json(self, version: str) -> None:
        """Update version in package.json"""
        
    def update_setup_py(self, version: str) -> None:
        """Update version in setup.py"""
        
    def update_pyproject_toml(self, version: str) -> None:
        """Update version in pyproject.toml"""
        
    def verify_consistency(self) -> bool:
        """Verify all files have the same version"""
```

### 3. ChangelogManager

Manages changelog updates and formatting.

```python
class ChangelogManager:
    def add_release_entry(
        self, 
        version: str, 
        date: str,
        changes: Dict[str, List[str]]
    ) -> None:
        """
        Add a new release entry to CHANGELOG.md
        
        Args:
            version: Release version
            date: Release date in YYYY-MM-DD format
            changes: Dictionary mapping category to list of changes
        """
        
    def get_changes_since_last_release(self) -> Dict[str, List[str]]:
        """Extract changes from git commits since last release"""
```

### 4. TestRunner

Executes test suites and reports results.

```python
class TestRunner:
    def run_all_tests(self) -> TestResults:
        """Run all unit and property-based tests"""
        
    def run_unit_tests(self) -> TestResults:
        """Run unit tests only"""
        
    def run_property_tests(self) -> TestResults:
        """Run property-based tests only"""

class TestResults:
    passed: int
    failed: int
    skipped: int
    errors: List[str]
    
    def is_success(self) -> bool:
        """Return True if all tests passed"""
```

### 5. GitManager

Handles Git operations for the release.

```python
class GitManager:
    def check_clean_working_directory(self) -> bool:
        """Check if working directory has uncommitted changes"""
        
    def commit_release_changes(self, version: str, files: List[str]) -> None:
        """Commit release-related file changes"""
        
    def create_tag(self, version: str, message: str) -> None:
        """Create an annotated Git tag"""
        
    def verify_tag_exists(self, version: str) -> bool:
        """Verify that a tag was created successfully"""
```

## Data Models

### ReleaseConfig

Configuration for the release process.

```python
@dataclass
class ReleaseConfig:
    """Configuration for release process"""
    new_version: str
    dry_run: bool = False
    skip_tests: bool = False
    auto_commit: bool = True
    
    # File paths
    package_json_path: str = "package.json"
    setup_py_path: str = "setup.py"
    pyproject_toml_path: str = "pyproject.toml"
    changelog_path: str = "CHANGELOG.md"
```

### VersionInfo

Represents version information.

```python
@dataclass
class VersionInfo:
    """Version information"""
    major: int
    minor: int
    patch: int
    
    @classmethod
    def from_string(cls, version_str: str) -> "VersionInfo":
        """Parse version string like '0.2.0'"""
        
    def to_string(self) -> str:
        """Convert to version string"""
        
    def __str__(self) -> str:
        return self.to_string()
```

### ChangelogEntry

Represents a changelog entry.

```python
@dataclass
class ChangelogEntry:
    """A single changelog entry"""
    version: str
    date: str  # YYYY-MM-DD format
    features: List[str]
    bug_fixes: List[str]
    improvements: List[str]
    documentation: List[str]
    
    def to_markdown(self) -> str:
        """Convert to markdown format"""
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Version update preserves configuration

*For any* configuration file (package.json, setup.py, or pyproject.toml) and any valid version string, updating the version field should change only the version value while preserving all other configuration settings, formatting, and structure.

**Validates: Requirements 1.1, 1.2, 1.3, 1.5**

### Property 2: Version consistency across files

*For any* valid version string, after updating all configuration files, reading the version from each file should return the same version value.

**Validates: Requirements 1.4**

### Property 3: Changelog entry positioning

*For any* existing changelog with N entries, adding a new release entry should result in N+1 entries with the new entry appearing first in the file.

**Validates: Requirements 2.1, 2.4**

### Property 4: Date format in changelog

*For any* date value, the changelog entry should contain that date formatted as YYYY-MM-DD (ISO 8601 format).

**Validates: Requirements 2.2**

### Property 5: Changelog category structure

*For any* changelog entry, the generated markdown should contain sections for all required categories: Features, Bug Fixes, Improvements, and Documentation.

**Validates: Requirements 2.3**

### Property 6: Git tag creation and placement

*For any* version string, after creating a release tag, the tag should exist in the repository and point to the current HEAD commit.

**Validates: Requirements 3.1, 3.3**

### Property 7: Annotated tag with message

*For any* release tag created, the tag should be annotated (not lightweight) and contain a non-empty message.

**Validates: Requirements 3.2**

### Property 8: Test failure halts release

*For any* test suite execution that results in one or more failures, the release process should halt and not proceed to version updates or tagging.

**Validates: Requirements 4.3**

### Property 9: Test results summary format

*For any* test execution, the output should include numeric counts for passed tests, failed tests, and skipped tests.

**Validates: Requirements 4.5**

### Property 10: Working directory state detection

*For any* Git repository state, the system should correctly identify whether the working directory is clean (no uncommitted changes) or dirty (has uncommitted changes).

**Validates: Requirements 5.1**

### Property 11: Release commit message format

*For any* version string, when creating a release commit, the commit message should follow the format "Release v{version}".

**Validates: Requirements 5.2**

### Property 12: Release commit includes required files

*For any* release commit, the commit should include all modified version files (package.json, setup.py, pyproject.toml) and the updated CHANGELOG.md.

**Validates: Requirements 5.3, 5.4**

## Error Handling

The release system implements comprehensive error handling at each stage:

### Pre-flight Validation Errors

- **Dirty Working Directory**: If uncommitted changes exist and auto-commit is disabled, the process halts with instructions to commit or stash changes
- **Invalid Version Format**: If the target version doesn't follow semantic versioning (X.Y.Z), the process halts with format requirements
- **Missing Files**: If any required configuration file is missing, the process halts with a list of missing files

### Test Execution Errors

- **Test Failures**: If any test fails, the process halts and displays:
  - Number of failed tests
  - Names of failed tests
  - First few lines of failure messages
  - Command to re-run failed tests
- **Test Runner Not Found**: If pytest is not installed, the process halts with installation instructions

### File Update Errors

- **Parse Errors**: If a configuration file cannot be parsed (invalid JSON, TOML, or Python syntax), the process halts with the parse error details
- **Write Errors**: If a file cannot be written (permissions, disk space), the process halts with the system error
- **Verification Failures**: If version verification fails after updates, the process halts and shows which files have mismatched versions

### Git Operation Errors

- **Commit Failures**: If git commit fails, the process halts with the git error message
- **Tag Already Exists**: If the release tag already exists, the process halts with options to delete the existing tag or choose a different version
- **Not a Git Repository**: If the current directory is not a git repository, the process halts with initialization instructions

### Rollback Strategy

The release process is designed to be atomic where possible:

1. **Before Commit**: If any error occurs before the git commit, no changes are persisted (files are modified but not committed)
2. **After Commit**: If an error occurs after committing but before tagging, the commit exists but can be reverted with `git reset HEAD~1`
3. **After Tagging**: If an error occurs after tagging, both commit and tag exist and must be manually removed if rollback is desired

The system provides clear rollback instructions for each failure scenario.

## Testing Strategy

The release automation will be tested using both unit tests and property-based tests to ensure reliability across different scenarios.

### Unit Testing Approach

Unit tests will cover:

- **Specific version updates**: Test updating from 0.1.0 to 0.2.0 in each file format
- **Changelog formatting**: Test that a known set of changes produces expected markdown output
- **Error conditions**: Test specific error scenarios like missing files, invalid versions, dirty working directory
- **Git operations**: Test tag creation, commit creation with mocked git commands
- **Edge cases**: Empty changelogs, files with unusual formatting, version strings with pre-release tags

### Property-Based Testing Approach

Property-based tests will use **Hypothesis** (Python's leading PBT library) to verify universal properties:

- **Version update properties**: Generate random valid version strings and verify updates work correctly
- **Configuration preservation**: Generate random configuration content and verify non-version fields are preserved
- **Changelog structure**: Generate random change lists and verify output structure is always correct
- **Git operations**: Generate random version strings and verify tags are created correctly
- **Idempotency**: Running the release process twice with the same version should fail the second time (tag already exists)

Each property-based test will run a minimum of 100 iterations to ensure thorough coverage of the input space.

### Test Organization

```
tests/
├── test_release_manager.py          # Unit tests for ReleaseManager
├── test_version_updater.py          # Unit tests for VersionUpdater
├── test_changelog_manager.py        # Unit tests for ChangelogManager
├── test_git_manager.py              # Unit tests for GitManager
├── test_version_update_property.py  # Property tests for version updates
├── test_changelog_property.py       # Property tests for changelog
└── test_git_operations_property.py  # Property tests for git operations
```

### Test Tagging Convention

All property-based tests will include a comment tag referencing the design document:

```python
# Feature: release-v0.2.0, Property 1: Version update preserves configuration
@given(version=version_strings(), config_data=json_objects())
def test_version_update_preserves_config(version, config_data):
    ...
```

## Implementation Notes

### Version String Parsing

Version strings will be parsed using a simple regex pattern that supports semantic versioning:

```python
VERSION_PATTERN = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$'
```

This supports versions like:
- `0.2.0` (standard)
- `1.0.0-alpha.1` (pre-release)
- `2.1.3+build.123` (build metadata)

### File Update Strategy

Each file type requires a different update strategy:

- **package.json**: Parse as JSON, update version field, write back with preserved formatting
- **setup.py**: Use regex to find and replace the version string (avoid executing Python code)
- **pyproject.toml**: Parse as TOML, update version field, write back

### Changelog Format

The changelog will follow the "Keep a Changelog" format:

```markdown
## [0.2.0] - 2025-12-08

### ✨ Features
- Feature 1
- Feature 2

### 🐛 Bug Fixes
- Fix 1

### 🔧 Improvements
- Improvement 1

### 📚 Documentation
- Doc update 1
```

### Dry Run Mode

The release manager supports a dry-run mode that:
- Shows what would be done without making changes
- Validates all preconditions
- Displays the exact commands that would be executed
- Useful for testing and CI/CD integration

### CLI Interface

The release will be triggered via a CLI command:

```bash
# Standard release
python scripts/release.py 0.2.0

# Dry run
python scripts/release.py 0.2.0 --dry-run

# Skip tests (not recommended)
python scripts/release.py 0.2.0 --skip-tests

# Manual commit (don't auto-commit changes)
python scripts/release.py 0.2.0 --no-auto-commit
```

## Dependencies

The release automation requires:

- **Python 3.9+**: For the release script
- **GitPython**: For Git operations
- **pytest**: For running tests
- **hypothesis**: For property-based testing
- **toml**: For parsing pyproject.toml

All dependencies are already in the project's dev requirements.

## Security Considerations

- **No Credential Storage**: The release script does not handle git credentials or push operations
- **Local Operations Only**: All operations are local; pushing to remote is manual
- **File Permissions**: The script respects file system permissions and fails gracefully if write access is denied
- **Input Validation**: Version strings are validated against a strict pattern to prevent injection attacks

## Future Enhancements

Potential improvements for future versions:

1. **Automated Changelog Generation**: Parse git commits to automatically generate changelog entries
2. **GitHub Release Integration**: Automatically create GitHub releases with release notes
3. **Rollback Command**: Add a command to rollback a failed release
4. **Multi-Package Support**: Support monorepos with multiple packages
5. **Custom Changelog Templates**: Allow users to customize changelog format
6. **Pre-release Versions**: Better support for alpha, beta, rc versions
7. **CI/CD Integration**: GitHub Actions workflow for automated releases
