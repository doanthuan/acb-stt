# acb-stt
speech to text demo for acb

## Development run
```
    $ sh run.sh
```

## Docker run
```
    $ docker build . -t <docker-image>
    $ docker run --rm -e CACHE_DIR=/cache -e MAX_WORKERS=1 -v <path-to-trankit-cache>:/cache  -p <custom-port>:80 <docker-image>
```


## Testing
```
    $ pytest -v
```
