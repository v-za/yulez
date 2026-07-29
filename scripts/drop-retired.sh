#!/usr/bin/env bash
# Delete the retired decision-graph files for good.
#
# These moved to src/_retired/ when the variant menu was removed (8650ad3).
# Nothing builds or links to them. Git history keeps them regardless, so
# this only clears the working tree.
#
#   bash scripts/drop-retired.sh
#
# To bring one back instead:
#   git mv src/_retired/03-monument.html src/variants/
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d src/_retired ] || { echo "nothing to drop"; exit 0; }
echo "removing:"; ls src/_retired
git rm -r --quiet src/_retired
echo "done — commit when ready:  git commit -m 'Drop retired variants'"
