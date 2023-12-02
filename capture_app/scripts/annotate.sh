#!/bin/bash
src=$1
dest=$2
title=$3
moon=$4
coords=$(eval echo "${5}")
light=$6
shift 6
rest="$@"

annotateImg="${src}"

tmp=/tmp/astro_tmp_converted.jpg
height=$(exiftool -s3 -ImageHeight $annotateImg)
width=$(exiftool -s3 -ImageWidth $annotateImg)

filename=$(basename -- "$src")
extension="${filename##*.}"

if [ "${extension}" = 'cr2' ];then
    tmp_file="/tmp/tmp.stack.jpg"

    if test -f $tmp_file; then
        rm $tmp_file
    fi

    darktable-cli $annotateImg $tmp_file > /dev/null 2>&1
    annotateImg=$tmp_file
fi

addCross() {
    convert \
        \(  -size '3456x5184'\
            -fill none \
            -strokewidth 2 \
            -stroke red \
            -draw "line 0,0 $width,$height" \
            -draw "line $width,0  0,$height" \
        \) \
        -append $annotateImg \
        $1
}

if [ $light -eq 1 ];then
    addCross $dest
    exit 0
fi

addCross $tmp

convert \
    \(  -background '#111' \
        -fill '#fff' \
        -stroke '#000' \
        -pointsize 110 \
        -bordercolor "#111" \
        -border 20x20 \
        -gravity NorthWest \
        label:"$title - $coords" \
    \) -append $tmp \
    \(  -background '#111' \
        -fill '#fff' \
        -stroke '#000' \
        -pointsize 110 \
        -bordercolor "#111" \
        -border 20x20 \
        -gravity NorthWest \
        label:"$rest" \
    \) -append $tmp

moon_img="/home/telescope/capture-app/capture_app/scripts/moons/color/${moon}.png"

composite -gravity NorthEast -geometry "+20+20" ${moon_img} ${tmp} $dest

# Add exif back into the annotated version from the original
exiftool -overwrite_original_in_place -TagsFromFile $src "-all:all>all:all" $dest

exit 0















# #!/bin/bash
# src=$1
# dest=$2
# title=$3
# moon=$4
# coords=$(eval echo "${5}")
# light=$6
# shift 6
# rest="$@"

# tmp=/tmp/astro_tmp_converted.jpg
# height=$(exiftool -s3 -ImageHeight $src)
# width=$(exiftool -s3 -ImageWidth $src)

# echo "src: $src"
# echo "dest: $dest"
# echo "title: $title"
# echo "moon: $moon"
# echo "coords: $coords"
# echo "light: $light"
# echo "rest: $rest"



# convert \
#     \(  -size '3456x5184'\
#         -fill none \
#         -strokewidth 2 \
#         -stroke red \
#         -draw "line 0,0 $width,$height" \
#         -draw "line $width,0  0,$height" \
#     \) \
#     -append $src \
#     $tmp

# convert \
#     \(  -background '#111' \
#         -fill '#fff' \
#         -stroke '#000' \
#         -pointsize 110 \
#         -bordercolor "#111" \
#         -border 20x20 \
#         -gravity NorthWest \
#         label:"$title - $coords" \
#     \) -append $tmp \
#     \(  -background '#111' \
#         -fill '#fff' \
#         -stroke '#000' \
#         -pointsize 110 \
#         -bordercolor "#111" \
#         -border 20x20 \
#         -gravity NorthWest \
#         label:"$rest" \
#     \) -append $tmp

# moon_img="/home/telescope/capture-app/capture_app/scripts/moons/color/${moon}.png"

# composite -gravity NorthEast -geometry "+20+20" ${moon_img} ${dest} $dest

# exit 0