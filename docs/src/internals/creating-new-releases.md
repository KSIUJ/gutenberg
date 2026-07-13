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

## Releasing new versions
Create a new branch `release/vX.Y.Z` from `develop`.
Create a pull request **targeting `main`** (**not `develop`!**) for this branch.

### Creating release candidates
- Update the package version in `backend/pyproject.toml`, including the pre-release 
    suffix (`X.Y.Z-rcN`).
- Run:
  ```bash
  cd backend && uv sync --upgrade
  ```
- In the CHANGELOG.md file:
  - Move the changes from the **[Unreleased]** section to a new
      section with the header  `## [X.Y.Z-rcN] - YYYY-MM-DD [Release candidate]`
  - where  `YYYY-MM-DD` is the date
      of the release.
  - If there already exists a header for a previous release candidate for the new
      version, update it instead.
  - Add an appropriate URL for the `[X.Y.Z-rcN]` link at the end of the file.
  - Update the `[unreleased]` link at the end of the file to compare only changes made
      since the release candidate tag.
  - Create a new GitHub Release with the tag `vX.Y.Z-rcN` on the `release/vX.Y.Z` branch.

### Adding fixes to a release branch
To make fixes in a pre-release version,
either commit them directly to the `release/vX.Y.Z` branch or create a new branch
based on `release/vX.Y.Z` and then squash merge it back to the release branch.

The changes can be cherry-picked into `develop`.

After making such fixes, the steps for creating release candidates can be repeated
with the next pre-release number.

### Finalizing a release
- Update the package version in `backend/pyproject.toml` (remove the pre-release suffix)
- Run:
  ```bash
  cd backend && uv sync --upgrade
  ```
- In the CHANGELOG.md file:
    - Move the changes from the **[Unreleased]** section if there are still any.
    - Replace the pre-release section header with `## [X.Y.Z] - YYYY-MM-DD`.
    - Add an appropriate URL for the `[X.Y.Z]` link at the end of the file.
    - Update the `[unreleased]` link at the end of the file to compare only changes made
      since the release candidate tag.
- Merge the release branch into `main` using the **merge commit** method.
- Create a new GitHub Release with the tag `vX.Y.Z` on the `main` branch.
- Finally, merge the `main` branch into `develop` (using fast-forward if possible).

[keep a changelog]: https://keepachangelog.com/en/1.1.0/
[semantic versioning]: (https://semver.org/lang/pl/spec/v2.0.0.html)
