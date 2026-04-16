#! /usr/bin/env bash

verify () {
    if [[ "$1" == "system" ]]
    then
        return
    fi
    python <<EOF
import dip.bindings.$1
import dip.clerk.auto.$1
import sys
if '$1' == 'categorization':
    b = {f'channel.{tag.localName()}' for tag in dip.bindings.$1.channels_type()._ElementMap}
    b.add('channel.unk')  # this is a default for those that have no channel
else:
    b = {tag.localName() for tag in dip.bindings.$1.$1_type()._ElementMap}
r = {f'{sv.name()}.{valname}' for sv in dip.clerk.auto.$1.Runnable().state_vectors() for valname in sv}
print('Verification of $1 binding <-> values:', b == r)
sys.exit(0 if b == r else -100)
EOF
}

if ! command -v python &> /dev/null
then
    echo 'Simply python is not in your path. It should be a 3.12 python VENV with "pip install -Ur requirements.txt and pip install _ur .github/workflow/requirements.txt already run.'
    exit -1
fi

export CORGIDRP_DO_NOT_AUTO_INIT_CALDB=True
cd $(realpath $(dirname $0)/..)
export PYTHONPATH=.
declare -i err_count=0
python -m dip.basis.transmute -v
mkdir -p dip/bindings
for xsd in schema/*.xsd
do
    mod=$(basename -s .xsd $xsd)
    pyxbgen --schema-location=$xsd \
            --module=$mod \
            --module-prefix=dip.bindings 2>&1 | grep -v "WARNING.*renamed to" | grep -v AbsentNamespace0
    if ! verify $mod
    then
        err_count=err_count+1
    fi
    if ! xmllint --noout --schema $xsd dip/base/$mod.xml
    then
        err_count=err_count+1
    fi
done
KEEP_CHANGES=1 tools/run.sh Style  # reformat the generated code

if [ "$1" != "ignore_checks" ]
then
   # do base line checks for sanity
   tools/run.sh Style Linters Compliance PyTesting
   for rpt in *.rpt.txt
   do
       if [ -f "$rpt" ]
       then
           err_count=err_count+1
       fi
   done
fi

# give a summary message
if [ $err_count -gt 0 ]
then
    echo "FAILED($err_count): look back and see why. Fix it. Try again."
else
    echo "SUCCESS: all looks well today."
fi
exit $err_count
