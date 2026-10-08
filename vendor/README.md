# Vendor component placement

Do not commit vendor-restricted binaries or license files.

After installing the authorized FireEye/Honglian software on the target workstation, copy the matching `skills` directories and their required CLI programs into `vendor-drop/` locally. Typical source locations seen on the source workstation or in public deployment notes include:

- `BootMagixV4\skills`
- `APPAnalysis\skills`
- `ForensicDesktop\resources\skills`

The exact paths depend on the installed product version. The DSH skill instructions must point to the real executable paths on the target machine.
