# Third-party software notices

This kit redistributes unmodified CPython installers and third-party Python
wheel files. Each component remains subject to its own license. No single
project license replaces those component licenses.

- The Python Software Foundation license and incorporated notices are in
  `licenses/PYTHON-LICENSE.txt` and the official Python distribution.
- Original license, copyright and NOTICE files remain inside each wheel in
  `wheels/`. Recognized license/notice files from the top-level `.dist-info`
  directory are also copied to `licenses/<package>-<version>/` for inspection.
- Exact package versions, license metadata and upstream URLs are recorded in
  `packages.json`. Some older packages use classifiers or place their notices
  elsewhere; the original wheel is authoritative when extracted metadata is
  incomplete.
- The standard CPython Windows EXE remains unmodified, with its original
  Authenticode signature.
- Generated examples in `verification-output/` are local validation artifacts
  and are not part of the redistributed package payload.

The installation and maintenance scripts in this repository are provided under
the MIT license in `LICENSE`. This license applies only to those original scripts
and documentation, not to the redistributed third-party software.
