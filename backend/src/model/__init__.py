# NOTE: submodules in this package (economic_data, asset_risk, settings, utilities)
# use bare top-level imports (`from settings import Settings`, `from economic_data.interest
# import InterestRate`, etc.) rather than relative imports. They are designed to be run
# with this `model/` directory itself on `sys.path` (see backend/src/config.py), not by
# importing this package as `model`. Do not `import model`; import its submodules after
# adding this directory to `sys.path` instead.