#/bin/bash

set -euo pipefail

echo "Deleting dist/"
rm -rf dist/

echo "Beginning Build:"

python -m build


echo "Uplading to twine:"
twine upload -u __token__ dist/*