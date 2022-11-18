#!/usr/bin/env bash

export HTTPS_PROXY="http://squid.corp.redhat.com:3128"

# set -xv

# LIMIT=100
# BATCH=$LIMIT
WAIT=0

while getopts 'l:b:w:d' OPTION; do
  case "$OPTION" in
    l)
      LIMIT=$OPTARG
      ;;
    b)
      BATCH=$OPTARG
      ;;
    w)
      WAIT=$OPTARG
      ;;
    d)
      DEBUG=true
      set -xv
      ;;
    ?)
      echo "script usage: ./cleanup.sh [-l LIMIT] [-b BATCH_SIZE] [-d]" >&2
      exit 1
      ;;
  esac
done
shift "$(($OPTIND -1))"

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI5MDI0YWU0ZC1kZDFlLTQ0MDEtOTg3MS1mOTdiNTUxYzEzN2UifQ.eyJpYXQiOjE2NTk5ODUwOTMsImp0aSI6IjhjZGRmYjNlLWI4NTctNGI4Zi04YTM1LTg5ODU3NjcxODhhNCIsImlzcyI6Imh0dHBzOi8vc3NvLnN0YWdlLnJlZGhhdC5jb20vYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjoiaHR0cHM6Ly9zc28uc3RhZ2UucmVkaGF0LmNvbS9hdXRoL3JlYWxtcy9yZWRoYXQtZXh0ZXJuYWwiLCJzdWIiOiJmOmFjNGJjZGI1LTFmYjEtNDFjNS05MzIzLTM0OTY5OGI5Yjc1NzphbnNpYmxlLWluc2lnaHRzIiwidHlwIjoiT2ZmbGluZSIsImF6cCI6ImNsb3VkLXNlcnZpY2VzIiwibm9uY2UiOiIzOGNiMDJmNC1kZDFjLTQwNTEtYmViNS1iMzdhMTRhNThlNWUiLCJzZXNzaW9uX3N0YXRlIjoiODIwODgwOGYtZWFmYS00MWY3LWIwZDctMjZjZjk5NzVhMTJjIiwic2NvcGUiOiJvcGVuaWQgb2ZmbGluZV9hY2Nlc3MgYXBpLmlhbS5zZXJ2aWNlX2FjY291bnRzIiwic2lkIjoiODIwODgwOGYtZWFmYS00MWY3LWIwZDctMjZjZjk5NzVhMTJjIn0.D7Ud40A-o9vSirwPJzR6EO0QUIJctz3Numw-pBQLQ-8"

read -r -d '' GKIT << EOM
galaxykit
    -s https://console.stage.redhat.com/api/automation-hub/
    -a https://sso.stage.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
    -t $TOKEN
EOM

anywait() {
    for pid in "$@"; do
        while kill -0 "$pid"; do
            sleep 0.5
        done
    done
}

progress_update() {
    V=$1
    T=$2
    R=$3
    SCALE=$((100 / $T))
    V=$(($SCALE * $V))
    T=$(($SCALE * $T))
    if [[ "$V" == "$T" ]] || [[ "$R" == "" ]]; then
        #  00:00:00/00:00:00
        R="................."
    fi
    printf "%-*s" $(($V + 1)) '[' | tr ' ' '#'
    printf "%*s%3d%%\r"  $(($T - $V))  "] $R  " "$V"
}

if [[ ! -v LIMIT ]]; then
    LIMIT=`$GKIT collection list --limit 1 | jq '.meta.count' -r`
fi
if [[ ! -v BATCH ]]; then
    BATCH=$LIMIT
fi

SEEN_COUNT=0
DELETE_COUNT=0
BATCH_NUMBER=1
REMAIN_TIME=""
TOTAL_TO_DELETE=$LIMIT
BATCH_TOTAL=$(($LIMIT / $BATCH))
SKIPPED=0

if [[ $(($LIMIT % $BATCH)) != 0  ]]; then
    BATCH_TOTAL=$(($BATCH_TOTAL + 1))
fi

SECONDS=0
while [[ $TOTAL_TO_DELETE != 0 ]]; do
    COUNTER=0
    BATCH_LABEL="batch #$BATCH_NUMBER/$BATCH_TOTAL"
    BATCH_START=$SECONDS

    echo $"Fetching and Deleting collection $BATCH_LABEL. $TOTAL_TO_DELETE remain. $DELETE_COUNT deleted. (Total time est: ${REMAIN_TIME:-unknown})"
    progress_update $COUNTER $BATCH

    COLL_LIST=`$GKIT collection list --limit $BATCH | jq '.data[] | "\(.namespace.name) \(.name)"' -r`
    COLL_LIST_PID=$!
    while read COLLECTION; do
        COUNTER=$(($COUNTER + 1))
        DEL_OUTPUT=$($GKIT collection delete --dependents --repository published,staging,rejected $COLLECTION)
        DC=$(
            jq ".delete_count" < <(echo "$DEL_OUTPUT")
        )
        if [[ "$DC" == "" ]]; then
            echo "Delete operation failed for $COLLECTION. Continuing after 30 seconds..."
            echo $DEL_OUTPUT
            sleep 30
            continue
        fi
        DELETE_COUNT=$(($DELETE_COUNT + $DC))
        TOTAL_TO_DELETE=$(($TOTAL_TO_DELETE - $DC))
        SEEN_COUNT=$(($SEEN_COUNT + 1))

        if [[ "$DC" == "0" ]]; then
            SKIPPED=$(( $SKIPPED + 1 ))
            BATCH_TOTAL=$(( ($LIMIT + $SKIPPED) / $BATCH ))
        fi

        DURATION=$SECONDS
        if [[ $DELETE_COUNT == 0 ]]; then
            REMAIN_TIME=""
        else
            RATE=$(($DURATION / $DELETE_COUNT))
            REMAIN_SEC=$(($TOTAL_TO_DELETE * $RATE))
            REMAIN_TIME=$(date -d@$REMAIN_SEC -u +%H:%M:%S)
        fi

        BATCH_DURATION=$(($SECONDS - $BATCH_START))
        if [[ $DELETE_COUNT == 0 ]]; then
            BATCH_REMAIN_TIME=""
        else
            RATE=$(($DURATION / $SEEN_COUNT))
            REMAIN_SEC=$(( ($BATCH - $COUNTER) * $RATE))
            BATCH_REMAIN_TIME=$(date -d@$REMAIN_SEC -u +%H:%M:%S)
        fi

        progress_update $COUNTER $BATCH "$BATCH_REMAIN_TIME/$REMAIN_TIME"

        sleep $WAIT
    done < <(echo "$COLL_LIST")
    
    BATCH_NUMBER=$(($BATCH_NUMBER + 1))
    echo
done

echo "Done. ${DELETE_COUNT} deletions completed successfully."

if [[ $DEBUG == true ]]; then
    set +xv
fi