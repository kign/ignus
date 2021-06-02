#! /bin/bash -u

TOP="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && cd .. && pwd)"

lib_git="${HOME}/git/inet-lab"
. "${lib_git}/shared/install.inc"

# Verify installation
test_availability python3 svgtoimg

# exit on error
set -e

cd "$TOP/web"
[ -e static ] || mkdir static
cd static
printf "\n${LIGHT_CYAN}Initializing static assets${NC}\n"
echo "Current directory: $(pwd)"

# One possible way to initialize
#if [ -d "static" ]; then
#    echo 'Directory "static" already exists, skipping initialization'
#else
#    echo "mkdir static"
#    mkdir static
#    echo cd static
#    cd static
#    echo ln -s ../static_assets/* .
#    ln -s ../static_assets/* .
#fi

svgtoimg -g 128x128 ../../assets/favicon.svg favicon.png
tmpf=$(mktemp /tmp/image.svg.XXXXX)
sed 's/fill: black/fill: red/g' ../../assets/favicon.svg > $tmpf
svgtoimg -g 128x128 $tmpf favicon_dbg.png

cd "$TOP"
printf "\n${LIGHT_CYAN}Installing python virtual environment${NC}\n"
echo "Current directory: $(pwd)"
venv=venv

# To create requirements anew, run this command:
## rm -rf venv
## python3 -m venv venv
## venv/bin/python3 -m pip install --upgrade pip
## venv/bin/python3 -m pip install flask python-dateutil pyyaml msal google-auth ua-parser user-agents emoji-country-flag google-cloud-firestore inetlab
## venv/bin/python3 -m pip freeze > web/requirements.txt
#
# And then run this command:
# venv/bin/python3 -m pip freeze > web/requirements.txt
#
# Note on used libraries:
#
#    * flask:        Self-explanatory
#
#    * python-dateutil: Provides relativedelta, date parser and other useful utilities
#                    Even of not used by a project, no reason not include it
#
#    * pyyaml:       Used in development environment to read web/app.yaml, and for user-agents
#
#    * msal, google-auth: MS and Google authentication libs
#
#    * inetlab:      My own library
#
#    * ua-parser, user-agents, emoji-country-flag:  User Agent parsing/presentation
#
#    * google-cloud-firestore   Google Firestore (NoSQL database)

if [ -e $venv ]; then
  echo "Directory $venv exists, skipping"
else
  echo python3 -m venv $venv
  python3 -m venv $venv
  echo $venv/bin/python3 -m pip install --upgrade pip
  $venv/bin/python3 -m pip install --upgrade pip
  echo "Installing dependencies from requirements.txt"
  $venv/bin/python3 -m pip install -r web/requirements.txt
fi

cd "$TOP/web/t"
printf "\n${LIGHT_CYAN}Linking standard Jinja templates${NC}\n"
echo "Current directory: $(pwd)"
echo "Linking from: $lib_git/shared/jinja"
for pf in "auth_error.html" "login.html"; do
  t="lib_${pf}"
  if [ -e $t ]; then
    echo >&2 -e "${LIGHT_RED}File $t exists, skipping${NC}"
  else
    ln -s $lib_git/shared/jinja/$pf "$t"
    echo "$pf => $t"
  fi
done

cd "$TOP/web"
gac_src="ign-us-google-app-auth.json"
if ! [ -e "$gac_src" ]; then
  printf "\n${LIGHT_RED}You are missing google application credentials file${NC}\n"
  printf "You need file ${LIGHT_CYAN}$gac_src${NC} to access Google Firestore\n\n"
fi

echo ""
echo "=> Now run this from directory $TOP/web <="
echo "../etc/run.sh flask"
