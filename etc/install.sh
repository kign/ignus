#! /bin/bash -u

TOP="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && cd .. && pwd)"

. "${TOP}/external/install.inc"

# Verify required utilities
test_availability python3

# exit on error
set -e

if type svgtoimg >/dev/null 2>&1 ; then
  cd "$TOP"
  ci=cached_images
  [ -e $ci ] || mkdir $ci
  cd $ci
  printf "\n${LIGHT_CYAN}Updating cached images${NC}\n"
  echo "Current directory: $(pwd)"

  tmpf=$(mktemp /tmp/image.svg.XXXXX)
  sed -E 's/(fill|stroke): (darkblue|rgb\(0, 0, 139\))/\1: blue/g' ../assets/redirect-www.svg > $tmpf
  svgtoimg -g 128x128 $tmpf favicon.png
  sed -E 's/(fill|stroke): (darkblue|rgb\(0, 0, 139\))/\1: red/g' ../assets/redirect-www.svg > $tmpf
  svgtoimg -g 128x128 $tmpf favicon_dbg.png
  svgtoimg -g 32x32 ../assets/alien.svg guest.png
  rm "$tmpf"
else
  printf "${LIGHT_RED}svgtoimg not available, using cached images\n${NC}"
fi


cd "$TOP/web"
[ -e static ] || mkdir static
cd static
printf "\n${LIGHT_CYAN}Initializing static assets${NC}\n"
echo "Current directory: $(pwd)"

cp ../../assets/www-redirect.png logo.png
echo "www-redirect.png => logo.png"
cp ../../assets/www-redirect-red.png logo-dbg.png
echo "www-redirect-red.png => logo-dbg.png"

for f in favicon.png favicon_dbg.png guest.png; do
  if [ -e $f ]; then
    echo "File $f exists"
  else
    echo "ln -s ../../$ci/$f ."
    ln -s ../../$ci/$f .
  fi
done

cd "$TOP"
printf "\n${LIGHT_CYAN}Installing python virtual environment${NC}\n"
echo "Current directory: $(pwd)"
venv=venv

# To create requirements anew, run this command:
## rm -rf venv
## python3 -m venv venv
## venv/bin/python3 -m pip install --upgrade pip
## venv/bin/python3 -m pip install flask python-dateutil pyyaml msal google-auth ua-parser user-agents emoji-country-flag google-cloud-firestore inetlab
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
#    * inetlab:      My own utility library
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
echo "Linking from: $TOP/external"
for pf in "auth_error.html" "login.html"; do
  t="lib_${pf}"
  if [ -e $t ]; then
    echo >&2 -e "${LIGHT_RED}File $t exists, skipping${NC}"
  else
    ln -s ${TOP}/external/$pf "$t"
    echo "$pf => $t"
  fi
done

cd "$TOP/web"
gac_src="secrets/firestore-auth.json"
if ! [ -e "$gac_src" ]; then
  printf "\n${LIGHT_RED}You are missing google application credentials file${NC}\n"
  printf "You need file ${LIGHT_CYAN}$gac_src${NC} to access Google Firestore\n\n"
fi

priv_txt="secrets/priv.txt"
if ! [ -e "$priv_txt" ]; then
  printf "\nCreating empty ${LIGHT_CYAN}${priv_txt}${NC} (you may wish to edit as needed)\n"
  touch "${priv_txt}"
fi

echo ""
echo "=> Now run this from directory $TOP/web <="
echo "../etc/run.sh flask"
