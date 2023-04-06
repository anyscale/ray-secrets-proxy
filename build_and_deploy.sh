#/bin/bash

set -euo pipefail

echo "Deleting dist/"
rm -rf dist/

echo "Beginning Build:"

python -m build

echo "Opening Token page"
open https://pypi.org/manage/account/token/

echo "Uplading to twine:"
twine upload -u __token__ dist/*