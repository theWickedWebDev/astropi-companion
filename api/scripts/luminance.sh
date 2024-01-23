#!/bin/bash

src_img=$1

tmp_file="/tmp/tmp.stack.jpg"

if test -f $tmp_file; then
    rm $tmp_file
fi

darktable-cli $src_img $tmp_file > /dev/null 2>&1
lum=$(/usr/bin/convert $tmp_file -format "%[fx:100*mean]" info:)
lum_val=${lum%.*}
echo $lum_val

# ext=$2

# if [ $ext == '.cr2' ];then
#     tmp_file="/tmp/tmp.stack.jpg"

#     if test -f $tmp_file; then
#         rm $tmp_file
#     fi

#     darktable-cli $src_img $tmp_file > /dev/null 2>&1
#     lum=$(/usr/bin/convert $tmp_file -format "%[fx:100*mean]" info:)
#     lum_val=${lum%.*}
#     echo $lum_val;
# else
#     lum=$(convert $src_img -format "%[fx:100*mean]" info:)
#     lum_val=${lum%.*}
#     echo $lum_val
# fi