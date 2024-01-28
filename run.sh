trap "exit" INT TERM ERR
trap "kill 0" EXIT

sass --watch /home/pi/astropi-companion/src/static/scss/main.scss:/home/pi/astropi-companion/src/static/style.css &
find . -name '*.py' | entr -cr poetry run python -m src.app mock-camera &

wait