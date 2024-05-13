import sh
import yaml
import sys
from pathlib import Path

frozen_bundle_path = sys.argv[1]


frozen_bundle = yaml.safe_load(Path(frozen_bundle_path).read_text())
print(frozen_bundle)
