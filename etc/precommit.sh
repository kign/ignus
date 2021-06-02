#! /bin/bash -u

TOP="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && cd .. && pwd)"

cd "$TOP/web" || exit

cp app.yaml secrets/app.yaml
perl -nle 's/(MS_CLIENT_ID|MS_CLIENT_SECRET|GOOGLE_CLIENT_ID):.+/$1: <hidden>/; print' secrets/app.yaml > app.yaml

echo "After commit, execute:"
echo ""
echo "(cd $TOP/web && cp secrets/app.yaml app.yaml)"
