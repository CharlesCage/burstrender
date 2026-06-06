"""Mutable runtime state shared across burstrender modules.

Replaces the historical abuse of the `config` PyPI package as a global
namespace. Import as: `from imageautomation import runtime as config`
to keep call sites unchanged.
"""

# Process outcome
exit_code = 0
exit_reason = ""

# Console behavior
quiet = False

# Paths
working_directory = ""
source_path = "."
destination_path = "."
log_path = ""
log_level = "DEBUG"

# Burst detection knobs
seconds_between_bursts = 2
min_burst_length = 10

# Rendering knobs
normalize_string = ""
custom_vf_string = ""
crop_string = None
gravity_string = None
file_extension = ".cr3"
