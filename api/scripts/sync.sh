#!/bin/bash
ssh pi "rsync -av --remove-source-files $1/ sg1:$2/" && ssh pi "rm -r $3"