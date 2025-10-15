# Creating new releases

## Updating the changelog during development
The CHANGELOG.md file lists the changes in each release in the [keep a changelog] style.
Please update the CHANGELOG.md file in the same PR, which includes the changes that will
be mentioned in the changelog. Changes should be placed in the **[Unreleased]** section.

### Semantic versioning of Gutenberg
This project uses [semantic versioning]. In particular:
- The project version has the format `major.minor.patch` (e.g., `4.1.0`), in some places
    prefixed with `v` (e.g., in the Git release tags).
- Release candidate versions have the format `major.minor.patch-rcN` (e.g., `4.1.0-rc1`
    is the first candidate for the version `4.1.0`).
- The major version is incremented when the app has changes which require configuration
    changes or other actions from the system administrator when upgrading. When a new
    major version is released, the minor and patch versions are reset to `0`.
- The minor version is incremented if the release adds new features which don't break
    existing configurations. In this case the patch version is reset to `0`.
- The patch version is incremented if the release includes only bug fixes, and the
    upgrade does not require any actions from the system administrator.

Please pay extra attention to documenting the breaking changes in the changelog. Describe
the changes that need to be made in the deployment when upgrading from the previous stable
version, consider linking to relevant Gutenberg documentation.

## Creating a new release or release candidate
Create a new pull request with the name `Release vX.Y.Z-rcN`, which contains the following
changes:
- Update the package version in `backend/pyproject.toml`.
- Run:
  ```bash
  cd backend && uv sync --upgrade
  ```
- In the CHANGELOG.md file:
  - Move the changes from the **[Unreleased]** section to a new
      section with the header `## [X.Y.Z] - YYYY-MM-DD` or
      `## [X.Y.Z-rcN] - YYYY-MM-DD [Release candidate]` where  `YYYY-MM-DD` is the date
      of the release.
  - If there already exists a header for a previous release candidate for the new
      version, update it instead. 
  - Add an appropriate URL for the `[X.Y.Z]` or `[X.Y.Z-rcN]` link at the end of the file.
  - Update the `[unreleased]` link at the end of the file to compare only changes made
      since the release candidate tag.

After merging the pull request, create a new GitHub Release with the tag `vX.Y.Z` or 
`vX.Y.Z-rcN`.

[keep a changelog]: https://keepachangelog.com/en/1.1.0/
[semantic versioning]: (https://semver.org/lang/pl/spec/v2.0.0.html)
