# ./run prod
# ./run development

trap "exit" INT TERM ERR
trap "kill 0" EXIT

export ENV=$1

# redis-server &
sass --watch /home/pi/astropi-companion/src/static/scss/main.scss:/home/pi/astropi-companion/src/static/style.css &
find . -name '*.py' | entr -cr poetry run python -m src.app $1 &

wait