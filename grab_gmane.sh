#!/bin/sh

# config
GMANE_DROPBOX=~/dev/gmane-git
REPO=~/dev/gitbare.git

# download new mails
cd "$GMANE_DROPBOX"
cur_inbox=$(ls | sort -n | tail -1)
cur_gmane_id () {
    grep '^Archived-At' "$1" | tail -1 | sed 's#.*/\([0-9]\{1,\}\)>$#\1#'
}
begin=$(($(cur_gmane_id $cur_inbox) + 1))
boundary=$(($begin+1000))
wget -O gmane-$boundary.tmp http://download.gmane.org/gmane.comp.version-control.git/$begin/$boundary
end=$(cur_gmane_id gmane-$boundary.tmp)
if [ -z "$end" ]; then
    rm gmane-$boundary.tmp
else
    mv gmane-$boundary.tmp $end
fi
