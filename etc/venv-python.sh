#! /bin/bash -u

TOP="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && cd .. && pwd)"

cd "$TOP/web" || exit

auth='ign-us-google-app-auth.json'

if ! [ -e "$auth" ]; then
  echo "File $auth doesn't exist"
  exit 1
fi

echo
echo "from google.cloud import firestore"
echo "db = firestore.Client()"
echo

GOOGLE_APPLICATION_CREDENTIALS=secrets/firestore-auth.json exec ../venv/bin/python3

