LIGHT_RED='\033[1;31m'
LIGHT_CYAN='\033[1;36m'
NC='\033[0m' # No Color

# inherited from parent shell, caused issues with 'cd'
CDPATH=''

function test_availability () {
    for e in "$@"; do
        type $e >/dev/null 2>&1 || { echo >&2 -e "${LIGHT_RED}$e not installed.  Aborting.${NC}"; exit 1; }
    done
}


function download_file() {
    local -r b=$(basename $1)
    if [ -e $b ]; then
        echo "File $b exists, will not override"
    else
        echo "Downloading $b ...."
        exec 3>$b
        # without --compressed option, some (misconfigured) sites could still
        # send compressed data, but curl won't uncompress it!
        http_stat=$(curl --location --compressed -w "%{http_code}" -so >(cat >&3) "$1")
        if [ "$http_stat" -ne 200 ]; then
            printf "${LIGHT_RED}ERROR: downloading $1 failed${NC}\n"
            rm -f $b
        else
            if [[ $b == *.zip ]] ; then
                echo "Unzipping $b...."
                unzip $b
                local -r d=${b%.zip}
                echo "Testing if directory $d was created...."
                if [ -d $d ]; then
                    mv $d/* .
                    rmdir $d
                fi
            fi
        fi
    fi
}
