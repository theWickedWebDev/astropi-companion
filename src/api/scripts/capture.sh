#!/bin/bash

ssh pi "\
    gphoto2 \
        --filename \
        $1/$2.%C \
        --capture-image-and-download \
    "