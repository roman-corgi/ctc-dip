#! /usr/bin/env bash

cd $(dirname $(realpath $0))/..
rm -rf dip/l*
rm -rf $(find . -type d -name auto) 
