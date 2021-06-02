#! /bin/bash -u

LIGHT_RED='\033[1;31m'
LIGHT_CYAN='\033[1;36m'
NC='\033[0m' # No Color

CDPATH=""

if [ -z "${1+x}" ]; then
  echo "Usage: $0 <flask|gunicorn|gae>"
  exit 0
fi

cd $(dirname $0)
cd ../web

venv=venv
app=url-shortener-app.py
printf "\nCurrent directory: ${LIGHT_CYAN}$(pwd)${NC}\n"

if [[ $1 == "flask" ]]; then
  shift
  printf "\n../venv/bin/python3 ${LIGHT_RED}${app}${NC} $@\n\n"
  ../${venv}/bin/python3 ${app} "$@"
elif [[ $1 == "gunicorn" ]]; then
  printf "\n${LIGHT_RED}WARNING: in this mode server won't serve static content${NC}\n\n"
  yaml=app.yaml
  for v in db_user db_password cloudsql_host; do
    if [ -z ${!v+x} ]; then
      export $v=$(perl -nle "print \$1 if /$v: *(.+)/" $yaml)
    fi
    printf "$v=${LIGHT_CYAN}${!v}${NC}\n"
  done

  cmd="-b :8080 --log-level debug"
  printf "\n../venv/bin/gunicorn $cmd ${LIGHT_RED}main:app${NC}\n\n"
  ../${venv}/bin/gunicorn $cmd main:app
elif [[ $1 == "gae" ]]; then
  gae_dir=~/Apps/google-cloud-sdk
  if ! [ -f "$gae_dir/path.bash.inc" ]; then
    printf "\n${LIGHT_RED}No such file $gae_dir/path.bash.inc${NC}\n\n"
    exit 1
  fi
  echo source $gae_dir/path.bash.inc
  source $gae_dir/path.bash.inc
  dev_appserver.py --host 0.0.0.0 --log_level=debug app.yaml
else
  printf "\n${LIGHT_RED}Invalid option $1${NC}\n\n"
fi
